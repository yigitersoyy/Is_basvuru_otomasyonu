import smtplib
from datetime import UTC, timedelta
from email.message import EmailMessage

from sqlalchemy import select

from .domain import audit, check_package, fail, get
from .models import Control, Outbox, Package, now


def dispatch(session_factory, settings) -> dict:
    # v0.1 intentionally has no live transport. No arbitrary SMTP host can be supplied via the API.
    if settings.mail_transport != "mailpit" or settings.smtp_host != "mailpit" or settings.smtp_port != 1025:
        fail("only the local Mailpit test transport is supported in this release")
    with session_factory() as session:
        control = session.get(Control, "global", with_for_update=True)
        if control is not None and control.dispatch_paused:
            return {"status": "paused", "transport": "mailpit"}
        item = session.scalar(
            select(Outbox)
            .where(Outbox.status == "queued", Outbox.due_at <= now())
            .order_by(Outbox.due_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not item:
            return {"status": "idle", "transport": "mailpit"}
        package = get(session, Package, item.package_id)
        try:
            check_package(session, package, settings.artifact_dir)
            if package.status != "approved" or package.approved_hash != package.package_hash:
                fail("package no longer approved")
            if "pdf" not in package.manifest:
                fail("a validated PDF is required before queueing")
        except Exception as exc:
            from fastapi import HTTPException

            if not isinstance(exc, HTTPException):
                raise
            item.status = "held"
            item.error_code = "gate_failed"
            audit(session, "dispatch.held", item.id, reason=exc.detail)
            session.commit()
            return {"status": "held", "outbox_id": item.id, "reason": exc.detail}
        message = EmailMessage()
        message["From"] = settings.mail_from
        message["To"] = package.recipient
        message["Subject"] = package.subject
        message["Message-ID"] = item.message_id
        message.set_content(package.body)
        message.add_attachment(
            (settings.artifact_dir / package.id / "cv.pdf").read_bytes(),
            maintype="application",
            subtype="pdf",
            filename="Candidate_CV.pdf",
        )
        # Commit the claim BEFORE any SMTP call; uncertain writes are never silently retried.
        item.status = "sending"
        item.attempted_at = now()
        audit(session, "dispatch.attempted", item.id, transport="mailpit", message_id=item.message_id)
        session.commit()
        item_id = item.id
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            refused = client.send_message(message)
            if refused:
                raise smtplib.SMTPRecipientsRefused(refused)
    except Exception:
        # Conservative even for a connection failure: no automatic repeat of an ambiguous write.
        with session_factory() as session:
            item = get(session, Outbox, item_id)
            item.status = "send_unknown"
            item.error_code = "smtp_outcome_unknown"
            audit(session, "dispatch.unknown", item.id)
            session.commit()
        return {"status": "send_unknown", "outbox_id": item_id}
    with session_factory() as session:
        item = get(session, Outbox, item_id)
        item.status = "delivered_to_test"
        item.completed_at = now()
        audit(session, "dispatch.test_delivered", item.id, transport="mailpit")
        session.commit()
    return {"status": "delivered_to_test", "outbox_id": item_id, "transport": "mailpit"}


def recover(session):
    rows = session.scalars(select(Outbox).where(Outbox.status == "sending").with_for_update())
    changed = []
    for item in rows:
        attempted = item.attempted_at
        if attempted and attempted.tzinfo is None:
            attempted = attempted.replace(tzinfo=UTC)
        if attempted is None or attempted < now() - timedelta(minutes=5):
            item.status = "send_unknown"
            item.error_code = "interrupted_attempt"
            audit(session, "dispatch.recovered_unknown", item.id)
            changed.append(item.id)
    return changed
