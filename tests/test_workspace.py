import smtplib
from datetime import timedelta
from io import BytesIO

from career_app.models import Outbox, now
from career_app.outbox import dispatch
from docx import Document
from sqlalchemy import select


def approve_queue(client, s):
    p = s["package"]
    assert (
        client.post(f"/v1/packages/{p['id']}/approve", json={"package_hash": p["package_hash"]}).status_code
        == 200
    )
    r = client.post(f"/v1/packages/{p['id']}/queue")
    assert r.status_code == 200, r.text
    return r.json()


def test_authentication_and_no_live_transport(client, app):
    assert client.get("/v1/profiles", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/health").json()["live_sending"] is False
    app.state.settings.mail_transport = "gmail"
    assert client.post("/v1/outbox/dispatch-test").status_code == 409


def test_truthful_tailoring_and_unknown_eligibility(client, scenario):
    p = scenario["package"]
    assert "future" in p["body"].lower()
    assert "part-time" in p["content"]["sections"][0]["items"][0]
    assert "work eligibility is unknown" in p["assessment"]["blockers"]
    assert "required language needs confirmation: English" in p["assessment"]["blockers"]
    assert "pytorch" in p["assessment"]["missing_tags"]
    binary = client.get(f"/v1/packages/{p['id']}/artifacts/docx")
    doc = Document(BytesIO(binary.content))
    text = "\n".join(x.text for x in doc.paragraphs)
    assert "Built Python RAG pipelines." in text
    assert "PyTorch" not in text
    assert "{{" not in text


def test_invented_source_quote_rejected(client, scenario):
    r = client.post(
        f"/v1/profiles/{scenario['profile']['id']}/facts",
        json={
            "section": "experience",
            "text": "Invented result",
            "source_page": 1,
            "source_quote": "Reduced costs by 95%",
            "tags": [],
        },
    )
    assert r.status_code == 422


def test_exact_approval_and_idempotent_queue(client, scenario):
    p = scenario["package"]
    assert client.post(f"/v1/packages/{p['id']}/queue").status_code == 409
    assert client.post(f"/v1/packages/{p['id']}/approve", json={"package_hash": "0" * 64}).status_code == 409
    first = approve_queue(client, scenario)
    second = client.post(f"/v1/packages/{p['id']}/queue").json()
    assert first["id"] == second["id"]
    assert len(client.get("/v1/outbox").json()) == 1


def test_edit_invalidates_approval_and_cancels_queue(client, scenario):
    approve_queue(client, scenario)
    p = scenario["package"]
    edited = client.patch(
        f"/v1/packages/{p['id']}", json={"subject": "Updated subject", "body": p["body"]}
    ).json()
    assert edited["approved_hash"] is None
    assert edited["package_hash"] != p["package_hash"]
    assert client.get("/v1/outbox").json()[0]["status"] == "cancelled"
    assert client.post(f"/v1/packages/{p['id']}/queue").status_code == 409


def test_profile_revocation_cancels_old_packages(client, scenario):
    approve_queue(client, scenario)
    client.post(f"/v1/facts/{scenario['fact']['id']}/revoke")
    assert client.get("/v1/outbox").json()[0]["status"] == "cancelled"
    assert (
        client.post(
            f"/v1/packages/{scenario['package']['id']}/approve",
            json={"package_hash": scenario["package"]["package_hash"]},
        ).status_code
        == 409
    )


def test_file_tampering_blocks_approval(client, app, scenario):
    p = scenario["package"]
    (app.state.settings.artifact_dir / p["id"] / "cv.pdf").write_bytes(b"changed")
    assert (
        client.post(f"/v1/packages/{p['id']}/approve", json={"package_hash": p["package_hash"]}).status_code
        == 409
    )


def test_suppression_cancels_pending_work(client, scenario):
    approve_queue(client, scenario)
    client.post(
        "/v1/suppressions", json={"scope": "email", "value": "CAREERS@EXAMPLE.ORG", "reason": "Please stop"}
    )
    assert client.get("/v1/outbox").json()[0]["status"] == "cancelled"
    assert client.post(f"/v1/packages/{scenario['package']['id']}/queue").status_code == 409


def test_guessed_contact_never_confirmed(client, scenario):
    contact = client.post(
        "/v1/contacts",
        json={
            "company_id": scenario["company"]["id"],
            "name": "Unknown person",
            "email": "guess@example.org",
            "title": "CTO",
            "evidence_type": "inferred_or_unconfirmed",
            "source_url": "https://example.org/",
            "source_quote": "Guessed from an email pattern",
        },
    ).json()
    assert client.post(f"/v1/contacts/{contact['id']}/confirm").status_code == 409


def test_uncertain_send_is_not_retried(client, app, scenario, monkeypatch):
    approve_queue(client, scenario)
    calls = []

    def failed(*args, **kwargs):
        calls.append(1)
        raise smtplib.SMTPServerDisconnected("response lost")

    monkeypatch.setattr("career_app.outbox.smtplib.SMTP", failed)
    assert dispatch(app.state.sessions, app.state.settings)["status"] == "send_unknown"
    assert dispatch(app.state.sessions, app.state.settings)["status"] == "idle"
    assert len(calls) == 1


def test_recover_interrupted_attempt_never_requeues(client, app, scenario):
    approve_queue(client, scenario)
    with app.state.sessions() as db:
        item = db.scalar(select(Outbox))
        item.status = "sending"
        item.attempted_at = now() - timedelta(minutes=10)
        db.commit()
    assert len(client.post("/v1/outbox/recover").json()["held_as_unknown"]) == 1
    assert client.get("/v1/outbox").json()[0]["status"] == "send_unknown"


def test_duplicate_company_and_job_discovery(client, scenario):
    c = scenario["company"]
    result = client.post(
        "/v1/companies", json={k: c[k] for k in ["name", "domain", "country", "source_url"]}
    ).json()
    assert result["id"] == c["id"]
    j = scenario["job"]
    result = client.post(
        "/v1/opportunities",
        json={
            k: j[k]
            for k in ["company_id", "external_key", "title", "kind", "role", "description", "source_url"]
        },
    ).json()
    assert result["id"] == j["id"]


def test_header_injection_rejected(client, scenario):
    r = client.patch(
        f"/v1/packages/{scenario['package']['id']}",
        json={"subject": "Hello\r\nBcc: attacker@example.org", "body": scenario["package"]["body"]},
    )
    assert r.status_code == 422


def test_pause_persists_for_future_work(client, app, scenario):
    client.post("/v1/outbox/pause")
    approve_queue(client, scenario)
    assert dispatch(app.state.sessions, app.state.settings)["status"] == "paused"
    assert client.post("/v1/outbox/resume-test").json()["live_sending"] is False


def test_second_active_company_sequence_blocked(client, scenario):
    approve_queue(client, scenario)
    p = scenario["post"](
        "/v1/packages",
        {
            "profile_id": scenario["profile"]["id"],
            "opportunity_id": scenario["job"]["id"],
            "contact_id": scenario["contact"]["id"],
        },
    )
    client.post(f"/v1/packages/{p['id']}/approve", json={"package_hash": p["package_hash"]})
    assert client.post(f"/v1/packages/{p['id']}/queue").status_code == 409


def test_stale_contact_cannot_be_approved(client, app, scenario):
    from career_app.models import Contact

    with app.state.sessions() as db:
        contact = db.get(Contact, scenario["contact"]["id"])
        contact.verified_at = now() - timedelta(days=31)
        db.commit()
    p = scenario["package"]
    assert (
        client.post(f"/v1/packages/{p['id']}/approve", json={"package_hash": p["package_hash"]}).status_code
        == 409
    )


def test_ats_input_cannot_inject_a_fetch_url(client, scenario):
    response = client.post(
        "/v1/boards/import",
        json={
            "company_id": scenario["company"]["id"],
            "provider": "greenhouse",
            "board": "https://127.0.0.1/secrets",
            "role": "applied_ai",
        },
    )
    assert response.status_code == 422


def test_invalid_upload_and_unknown_country(client):
    assert (
        client.post("/v1/sources", files={"file": ("cv.pdf", b"not PDF", "application/pdf")}).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/companies",
            json={
                "name": "Outside Target",
                "domain": "example.org",
                "country": "US",
                "source_url": "https://example.org",
            },
        ).status_code
        == 422
    )


def test_migration_matches_current_models(app):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from career_app.models import Base

    with app.state.engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
        assert differences == []
