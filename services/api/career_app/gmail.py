"""Gmail adapter: no blind write retries; only approved queued packages can be sent."""

import base64
import hashlib
import secrets
import shutil
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import httpx
from cryptography.fernet import Fernet
from sqlalchemy import select

from .domain import assessment, audit, check_package, fail, fingerprint, get
from .models import Company, Delivery, Integration, Outbox, Package, Suppression, now, uid

BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
TOKEN = "https://oauth2.googleapis.com/token"
ZONES = {
    "TR": "Europe/Istanbul",
    "DE": "Europe/Berlin",
    "AT": "Europe/Vienna",
    "CH": "Europe/Zurich",
    "NL": "Europe/Amsterdam",
    "DK": "Europe/Copenhagen",
    "SE": "Europe/Stockholm",
    "NO": "Europe/Oslo",
    "GB": "Europe/London",
    "BE": "Europe/Brussels",
}


def utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def cipher(settings):
    return Fernet(
        base64.urlsafe_b64encode(hashlib.sha256(settings.api_key.get_secret_value().encode()).digest())
    )


def state(db, key, payload=None):
    obj = db.get(Integration, key)
    if payload is not None:
        if obj is None:
            obj = Integration(id=key, payload=payload)
            db.add(obj)
        else:
            obj.payload = payload
    return obj


def begin(db, settings):
    if not settings.gmail_client_id or not settings.gmail_client_secret.get_secret_value():
        fail("configure GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET locally first", 422)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    state(
        db,
        "oauth_pending",
        {"nonce": nonce, "verifier": verifier, "expires": (now() + timedelta(minutes=10)).isoformat()},
    )
    return {
        "url": "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(
            {
                "client_id": settings.gmail_client_id,
                "redirect_uri": settings.gmail_redirect_uri,
                "response_type": "code",
                "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
                "access_type": "offline",
                "prompt": "consent",
                "state": nonce,
                "code_challenge_method": "S256",
                "code_challenge": base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
                .decode()
                .rstrip("="),
            }
        )
    }


def finish(db, settings, code, nonce):
    pending = state(db, "oauth_pending")
    if (
        not pending
        or not secrets.compare_digest(pending.payload.get("nonce", ""), nonce)
        or datetime.fromisoformat(pending.payload["expires"]) < now()
    ):
        fail("invalid or expired OAuth state", 400)
    verifier = pending.payload["verifier"]
    db.delete(pending)
    db.commit()  # One-use state, even if the exchange fails.
    try:
        response = httpx.post(
            TOKEN,
            data={
                "code": code,
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret.get_secret_value(),
                "redirect_uri": settings.gmail_redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            },
            timeout=20,
        )
        response.raise_for_status()
        tokens = response.json()
        if not tokens.get("refresh_token"):
            fail("no refresh token; reconnect with offline consent", 422)
        profile = httpx.get(
            BASE + "/profile", headers={"Authorization": "Bearer " + tokens["access_token"]}, timeout=20
        )
        profile.raise_for_status()
    except (httpx.HTTPError, KeyError, ValueError):
        fail("Google authorization exchange failed; reconnect", 502)
    state(
        db,
        "gmail",
        {
            "refresh": cipher(settings).encrypt(tokens["refresh_token"].encode()).decode(),
            "email": profile.json()["emailAddress"],
        },
    )
    audit(db, "gmail.connected", "gmail")
    return {
        "connected": True,
        "email": profile.json()["emailAddress"],
        "live_enabled": settings.gmail_live_enabled,
    }


class Client:
    def __init__(self, db, settings):
        account = state(db, "gmail")
        if not account:
            fail("connect Gmail first", 409)
        try:
            refresh = cipher(settings).decrypt(account.payload["refresh"].encode()).decode()
            result = httpx.post(
                TOKEN,
                data={
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret.get_secret_value(),
                    "refresh_token": refresh,
                    "grant_type": "refresh_token",
                },
                timeout=20,
            )
            result.raise_for_status()
            self.token = result.json()["access_token"]
        except Exception:
            fail("Gmail token refresh failed; reconnect the account", 503)
        self.email = account.payload["email"]

    def request(self, method, path, **kwargs):
        response = httpx.request(
            method, BASE + path, headers={"Authorization": "Bearer " + self.token}, timeout=30, **kwargs
        )
        response.raise_for_status()
        return response.json()


def cancel_company(db, company_id, event):
    for item in db.scalars(select(Outbox).where(Outbox.company_id == company_id, Outbox.status == "queued")):
        item.status = "cancelled"
        audit(db, "gmail.sequence_stopped", item.id, event=event)


def reply_text(payload):
    text = ""
    if payload.get("mimeType") == "text/plain":
        encoded = payload.get("body", {}).get("data", "")
        try:
            text = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode(
                "utf-8", errors="replace"
            )
        except ValueError:
            pass
    return text + " ".join(reply_text(p) for p in payload.get("parts", []))


def sync(db, settings):
    client = Client(db, settings)
    deliveries = list(db.scalars(select(Delivery).where(Delivery.replied.is_(False))))
    if len(deliveries) > 100:
        fail("more than 100 active threads; archive completed conversations first")
    checked = 0
    try:
        for delivery in deliveries:
            thread = client.request("GET", "/threads/" + delivery.thread_id, params={"format": "full"})
            messages = thread.get("messages", [])
            newer = [m for m in messages if m["id"] != delivery.provider_id]
            if newer:
                # Any activity besides the original message pauses the sequence, including a manual sent reply.
                delivery.replied = True
                delivery.event = "activity_requires_review"
                item = get(db, Outbox, delivery.id)
                for message in newer:
                    if "SENT" in message.get("labelIds", []):
                        continue
                    payload = message.get("payload", {})
                    headers = {h["name"].lower(): h["value"].lower() for h in payload.get("headers", [])}
                    content = reply_text(payload).lower().split("\non ")[0]
                    optout = any(
                        term in content
                        for term in (
                            "do not contact",
                            "stop contacting",
                            "unsubscribe",
                            "bir daha iletişime",
                            "mail göndermeyin",
                        )
                    )
                    bounce = "mailer-daemon" in headers.get("from", "") or "delivery-status" in payload.get(
                        "mimeType", ""
                    )
                    if optout or bounce:
                        delivery.event = "opted_out" if optout else "bounced"
                        pkg = get(db, Package, item.package_id)
                        existing = db.scalar(
                            select(Suppression).where(
                                Suppression.scope == "email", Suppression.value == pkg.recipient.lower()
                            )
                        )
                        if not existing:
                            db.add(
                                Suppression(scope="email", value=pkg.recipient.lower(), reason=delivery.event)
                            )
                cancel_company(db, item.company_id, delivery.event)
                audit(db, "gmail.thread_activity", item.id, message_count=len(messages))
            checked += 1
        # Reconcile ambiguous sends using the stable RFC Message-ID; never resend on an empty search result.
        for item in db.scalars(select(Outbox).where(Outbox.status == "send_unknown")):
            found = client.request(
                "GET", "/messages", params={"q": "in:sent rfc822msgid:" + item.message_id.strip("<>")}
            )
            matches = found.get("messages", [])
            if len(matches) == 1:
                message = client.request(
                    "GET", "/messages/" + matches[0]["id"], params={"format": "metadata"}
                )
                headers = {
                    h["name"].lower(): h["value"] for h in message.get("payload", {}).get("headers", [])
                }
                pkg = get(db, Package, item.package_id)
                if (
                    headers.get("message-id", "").strip("<>") != item.message_id.strip("<>")
                    or pkg.recipient.lower() not in headers.get("to", "").lower()
                ):
                    continue
                item.status = "sent"
                item.completed_at = now()
                if not db.get(Delivery, item.id):
                    db.add(Delivery(id=item.id, provider_id=message["id"], thread_id=message["threadId"]))
                audit(db, "gmail.send_reconciled", item.id)
    except (httpx.HTTPError, KeyError, ValueError):
        db.commit()  # Preserve any observed replies before reporting an incomplete sync.
        fail("Gmail sync incomplete; sending remains blocked until a successful sync", 503)
    state(db, "gmail_sync", {"at": now().isoformat()})
    return {"checked_threads": checked, "synced_at": now().isoformat()}


def live_dispatch(factory, settings):
    if not settings.gmail_live_enabled:
        fail("GMAIL_LIVE_ENABLED is false; live sending is disabled")
    from .models import Control

    with factory() as db:
        control = db.get(Control, "global", with_for_update=True)
        if control.dispatch_paused:
            return {"status": "paused"}
        sync(db, settings)
        db.commit()
        # Serialize all dispatchers and pause actions while selecting and claiming one item.
        db.get(Control, "global", with_for_update=True, populate_existing=True)
        if db.get(Control, "global").dispatch_paused:
            return {"status": "paused"}
        item = db.scalar(
            select(Outbox)
            .where(Outbox.status == "queued", Outbox.due_at <= now())
            .order_by(Outbox.due_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if not item:
            return {"status": "idle"}
        pkg = get(db, Package, item.package_id)
        job, contact = check_package(db, pkg, settings.artifact_dir)
        if pkg.status != "approved" or pkg.approved_hash != pkg.package_hash:
            fail("package approval is stale")
        score = assessment(db, pkg.profile_id, job)
        blockers = [
            b
            for b in score["blockers"]
            if not (job.kind == "speculative" and b == "work eligibility is unknown")
        ]
        if blockers:
            fail("; ".join(blockers))
        company = get(db, Company, job.company_id)
        local = now().astimezone(ZoneInfo(ZONES[company.country]))
        if local.weekday() not in (1, 2, 3) or not (
            9 * 60 + 30 <= local.hour * 60 + local.minute < 16 * 60 + 30
        ):
            return {"status": "outside_send_window"}
        attempts = list(db.scalars(select(Outbox).where(Outbox.attempted_at.is_not(None))))
        if sum(utc(o.attempted_at) > now() - timedelta(days=1) for o in attempts) >= 10:
            return {"status": "daily_limit"}
        if any(utc(o.attempted_at) > now() - timedelta(minutes=15) for o in attempts):
            return {"status": "spacing_limit"}
        client = Client(db, settings)
        parent = pkg.content.get("followup_parent")
        thread_id = None
        message = EmailMessage()
        if parent:
            previous = get(db, Delivery, parent)
            if previous.replied:
                fail("the original thread has activity; follow-up is cancelled")
            prior = get(db, Outbox, parent)
            message["In-Reply-To"] = prior.message_id
            message["References"] = prior.message_id
            thread_id = previous.thread_id
        message["From"] = client.email
        message["To"] = contact.email
        message["Subject"] = pkg.subject
        message["Message-ID"] = item.message_id
        message.set_content(pkg.body)
        message.add_attachment(
            (settings.artifact_dir / pkg.id / "cv.pdf").read_bytes(),
            maintype="application",
            subtype="pdf",
            filename="CV.pdf",
        )
        payload = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}
        if thread_id:
            payload["threadId"] = thread_id
        item.status = "sending"
        item.attempted_at = now()
        audit(db, "gmail.send_attempted", item.id)
        db.commit()
        item_id = item.id
    try:
        sent = client.request("POST", "/messages/send", json=payload)
        provider_id, thread_id = sent["id"], sent["threadId"]
    except Exception:
        with factory() as db:
            obj = get(db, Outbox, item_id)
            obj.status = "send_unknown"
            obj.error_code = "gmail_outcome_unknown"
            audit(db, "gmail.send_unknown", item_id)
            db.commit()
        return {"status": "send_unknown", "outbox_id": item_id}
    with factory() as db:
        obj = get(db, Outbox, item_id)
        obj.status = "sent"
        obj.completed_at = now()
        db.add(Delivery(id=item_id, provider_id=provider_id, thread_id=thread_id))
        if parent:
            get(db, Delivery, parent).event = "followup_sent"
        audit(db, "gmail.sent", item_id)
        db.commit()
    return {"status": "sent", "outbox_id": item_id}


def plan_followups(db, settings):
    result = []
    # A single follow-up, after seven weekdays. Generated messages need exact-package review.
    for delivery in db.scalars(
        select(Delivery)
        .where(Delivery.replied.is_(False), Delivery.event == "awaiting_reply")
        .with_for_update()
    ):
        original = get(db, Outbox, delivery.id)
        if not original.completed_at:
            continue
        due = utc(original.completed_at)
        count = 0
        while count < 7:
            due += timedelta(days=1)
            if due.weekday() < 5:
                count += 1
        if due > now() or state(db, "followup:" + delivery.id):
            continue
        previous = get(db, Package, original.package_id)
        if previous.content.get("followup_parent"):
            continue
        new_id = uid()
        content = {**previous.content, "followup_parent": delivery.id}
        body = (
            "Hello,\n\nI wanted to follow up on my introduction below. If relevant, I would welcome a short conversation with your team.\n\nKind regards,\n"
            + previous.content["name"]
        )
        obj = Package(
            id=new_id,
            profile_id=previous.profile_id,
            profile_revision=previous.profile_revision,
            opportunity_id=previous.opportunity_id,
            contact_id=previous.contact_id,
            fact_ids=previous.fact_ids,
            content=content,
            subject=previous.subject,
            body=body,
            recipient=previous.recipient,
            manifest=previous.manifest,
            package_hash="",
            status="needs_review",
        )
        check_package(db, previous, settings.artifact_dir)
        shutil.copytree(settings.artifact_dir / previous.id, settings.artifact_dir / new_id)
        obj.package_hash = fingerprint(obj)
        db.add(obj)
        state(db, "followup:" + delivery.id, {"package_id": new_id})
        audit(db, "followup.prepared", new_id)
        result.append(new_id)
    return {"review_packages": result, "calendar": "weekdays; country holidays not included"}
