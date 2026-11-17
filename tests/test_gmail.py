from datetime import UTC, datetime, timedelta

import httpx
import pytest
from career_app import gmail
from career_app.models import Delivery, Integration, Opportunity
from sqlalchemy import select
from test_workspace import approve_queue


class FakeGmail:
    calls = []
    messages = []
    sent_error = False

    def __init__(self, db, settings):
        self.email = "candidate@example.org"

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if method == "POST":
            if self.sent_error:
                raise httpx.ReadTimeout("unknown send outcome")
            return {"id": "gmail-1", "threadId": "thread-1"}
        if path.startswith("/threads/"):
            return {"messages": self.messages or [{"id": "gmail-1"}]}
        return {"messages": []}


@pytest.fixture
def live(app, scenario, client, monkeypatch):
    FakeGmail.calls = []
    FakeGmail.messages = []
    FakeGmail.sent_error = False
    monkeypatch.setattr(gmail, "Client", FakeGmail)
    monkeypatch.setattr(gmail, "now", lambda: datetime(2026, 11, 17, 11, 0, tzinfo=UTC))
    app.state.settings.gmail_live_enabled = True
    with app.state.sessions() as db:
        job = db.get(Opportunity, scenario["job"]["id"])
        job.required_languages = []
        db.commit()
    approve_queue(client, scenario)
    return scenario


def test_live_switch_required(client):
    assert client.post("/v1/gmail/dispatch").status_code == 409


def test_successful_send_recorded_once(app, client, live):
    first = client.post("/v1/gmail/dispatch")
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "sent"
    assert client.post("/v1/gmail/dispatch").json()["status"] == "idle"
    assert sum(m == "POST" for m, p, k in FakeGmail.calls) == 1
    with app.state.sessions() as db:
        assert db.scalar(select(Delivery)).thread_id == "thread-1"


def test_ambiguous_live_write_never_retried(app, client, live):
    FakeGmail.sent_error = True
    assert client.post("/v1/gmail/dispatch").json()["status"] == "send_unknown"
    assert client.post("/v1/gmail/dispatch").json()["status"] == "idle"
    assert sum(m == "POST" for m, p, k in FakeGmail.calls) == 1


def test_reply_stops_followup_and_creates_visible_event(app, client, live):
    client.post("/v1/gmail/dispatch")
    FakeGmail.messages = [{"id": "gmail-1"}, {"id": "reply-2"}]
    assert client.post("/v1/gmail/sync").status_code == 200
    conversations = client.get("/v1/conversations").json()
    assert conversations[0]["replied"] is True
    assert client.post("/v1/followups/plan").json()["review_packages"] == []


def test_one_followup_requires_review(app, client, live, monkeypatch):
    client.post("/v1/gmail/dispatch")
    monkeypatch.setattr(gmail, "now", lambda: datetime(2026, 12, 1, 11, 0, tzinfo=UTC))
    # completed_at uses the same fixed clock as live dispatch.
    first = client.post("/v1/followups/plan")
    assert first.status_code == 200, first.text
    ids = first.json()["review_packages"]
    assert len(ids) == 1
    package = client.get("/v1/packages/" + ids[0]).json()
    assert package["status"] == "needs_review"
    assert package["approved_hash"] is None
    assert client.post("/v1/followups/plan").json()["review_packages"] == []


def test_oauth_state_expiry_and_pkce(app, client):
    app.state.settings.gmail_client_id = "test-client"
    app.state.settings.gmail_client_secret = "test-secret"
    from pydantic import SecretStr

    app.state.settings.gmail_client_secret = SecretStr("test-secret")
    result = client.post("/v1/gmail/connect")
    assert result.status_code == 200, result.text
    assert "code_challenge_method=S256" in result.json()["url"]
    assert (
        client.get("/oauth/gmail/callback", params={"state": "wrong", "code": "not-a-code"}).status_code
        == 400
    )
    with app.state.sessions() as db:
        pending = db.get(Integration, "oauth_pending")
        payload = dict(pending.payload)
        payload["expires"] = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
        pending.payload = payload
        db.commit()
    assert (
        client.get(
            "/oauth/gmail/callback", params={"state": payload["nonce"], "code": "not-a-code"}
        ).status_code
        == 400
    )


def test_encrypted_refresh_roundtrip(app):
    encrypted = gmail.cipher(app.state.settings).encrypt(b"private-refresh-token")
    assert b"private-refresh-token" not in encrypted
    assert gmail.cipher(app.state.settings).decrypt(encrypted) == b"private-refresh-token"


def test_research_private_destinations_rejected(monkeypatch):
    from career_app.research import public_page
    from fastapi import HTTPException

    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **k: [(2, 1, 6, "", ("127.0.0.1", 443))])
    with pytest.raises(HTTPException):
        public_page("https://example.org", "example.org")
    with pytest.raises(HTTPException):
        public_page("https://attacker.org", "example.org")


def test_optout_creates_durable_suppression(app, client, live):
    import base64

    client.post("/v1/gmail/dispatch")
    FakeGmail.messages = [
        {"id": "gmail-1"},
        {
            "id": "reply-stop",
            "payload": {
                "mimeType": "text/plain",
                "headers": [{"name": "From", "value": "careers@example.org"}],
                "body": {"data": base64.urlsafe_b64encode(b"Please do not contact us again.").decode()},
            },
        },
    ]
    assert client.post("/v1/gmail/sync").status_code == 200
    assert client.get("/v1/conversations").json()[0]["event"] == "opted_out"
    from career_app.models import Suppression

    with app.state.sessions() as db:
        assert db.scalar(select(Suppression)).value == "careers@example.org"


def test_live_sent_package_cannot_be_edited(client, live):
    assert client.post("/v1/gmail/dispatch").json()["status"] == "sent"
    response = client.patch(
        "/v1/packages/" + live["package"]["id"],
        json={"subject": "Changed after send", "body": "This is a new unsanctioned body."},
    )
    assert response.status_code == 409


def test_failed_sync_prevents_send(client, live, monkeypatch):
    def failed(*a, **k):
        from fastapi import HTTPException

        raise HTTPException(503, "sync failed")

    monkeypatch.setattr(gmail, "sync", failed)
    assert client.post("/v1/gmail/dispatch").status_code == 503
    assert not any(method == "POST" for method, path, kwargs in FakeGmail.calls)


def test_outside_window_does_not_send(client, live, monkeypatch):
    monkeypatch.setattr(gmail, "now", lambda: datetime(2026, 11, 21, 11, 0, tzinfo=UTC))
    assert client.post("/v1/gmail/dispatch").json()["status"] == "outside_send_window"
    assert not any(method == "POST" for method, path, kwargs in FakeGmail.calls)


def test_new_subject_exact_sender_holds_company_and_creates_task(app, client, live, monkeypatch):
    client.post("/v1/gmail/dispatch").raise_for_status()
    original = FakeGmail.request

    def request(self, method, path, **kwargs):
        if path == "/messages" and "from:(" in kwargs.get("params", {}).get("q", ""):
            return {"messages": [{"id": "new-subject"}]}
        if path == "/messages/new-subject":
            return {
                "id": "new-subject",
                "internalDate": str(int(datetime(2026, 11, 17, 12, tzinfo=UTC).timestamp() * 1000)),
                "payload": {"headers": [{"name": "From", "value": "Recruiting <careers@example.org>"}]},
            }
        return original(self, method, path, **kwargs)

    monkeypatch.setattr(FakeGmail, "request", request)
    response = client.post("/v1/gmail/sync")
    assert response.status_code == 200, response.text
    assert client.get("/v1/conversations").json()[0]["event"] == "new_subject_requires_review"
    assert client.get("/v1/tasks").json()[0]["status"] == "needs_review"
    assert client.post("/v1/followups/plan").json()["review_packages"] == []
