import json

import httpx
import pytest
from career_app.llm import propose_facts
from career_app.settings import Settings
from fastapi import HTTPException


def test_api_requires_explicit_enable_and_no_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: calls.append(a))
    settings = Settings(api_key="x" * 48, ai_provider="openai_compatible")
    with pytest.raises(HTTPException) as error:
        propose_facts(settings, ["Python"])
    assert error.value.status_code == 409
    assert calls == []


def test_api_contract_and_quote_rejection(monkeypatch):
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        fact = {
            "section": "skills",
            "text": "Python",
            "source_quote": "Invented skill",
            "source_page": 1,
            "tags": [],
        }
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"content": json.dumps({"facts": [fact]})}}]},
        )

    monkeypatch.setattr(httpx, "post", post)
    settings = Settings(
        api_key="x" * 48,
        ai_provider="openai_compatible",
        ai_api_enabled=True,
        ai_api_model="chosen-model",
        ai_api_key="private-test-key",
    )
    with pytest.raises(HTTPException) as error:
        propose_facts(settings, ["Python"])
    assert error.value.status_code == 422
    assert len(calls) == 1
    assert calls[0][1]["json"]["model"] == "chosen-model"


def test_ai_settings_never_expose_or_redirect_key(client):
    current = client.get("/v1/ai/settings").json()
    assert current["provider"] == "ollama"
    assert current["fallback"] == "none"
    assert "ai_api_key" not in current
    current.pop("api_key_configured")
    current.pop("fallback")
    current["api_url"] = "https://other.example/v1"
    assert client.put("/v1/ai/settings", json=current).status_code == 422


def test_campaign_repeat_and_pause(client, scenario):
    data = {
        "name": "Synthetic campaign",
        "profile_id": scenario["profile"]["id"],
        "countries": ["NL"],
        "roles": ["applied_ai"],
        "minimum_coverage": 0,
        "mode": "review_each",
        "enabled": True,
    }
    created = client.post("/v1/campaigns", json=data)
    assert created.status_code == 201, created.text
    key = created.json()["id"]
    result = client.post(f"/v1/campaigns/{key}/run")
    assert result.status_code == 200, result.text
    assert result.json()["results"][0]["status"] == "needs_review"
    assert client.post(f"/v1/campaigns/{key}/run").json()["results"] == []
    assert client.get("/v1/outbox").json() == []
    client.post(f"/v1/campaigns/{key}/pause")
    assert client.post(f"/v1/campaigns/{key}/run").status_code == 409


def test_portal_submission_separate_from_email(client, scenario):
    key = scenario["package"]["id"]
    assert client.get(f"/v1/packages/{key}/portal-handoff").json()["status"] == "awaiting_portal_submission"
    response = client.post(
        f"/v1/packages/{key}/portal-submission",
        json={"reference": "USER-CONFIRMATION-123", "submitted_at": "2026-01-01T12:00:00+03:00"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "submitted"
    assert client.get("/v1/outbox").json() == []


def test_policy_auto_holds_unknown_rights(client, scenario):
    data = {
        "name": "Synthetic auto",
        "profile_id": scenario["profile"]["id"],
        "countries": ["NL"],
        "roles": ["applied_ai"],
        "minimum_coverage": 0,
        "mode": "policy_auto",
        "enabled": True,
    }
    key = client.post("/v1/campaigns", json=data).json()["id"]
    response = client.post(f"/v1/campaigns/{key}/run")
    assert response.status_code == 200, response.text
    assert response.json()["results"][0]["status"] == "needs_review"
    assert client.get("/v1/outbox").json() == []


def test_sourced_requirement_missing_skill(client, scenario):
    job = scenario["job"]
    job["external_key"] = "vacancy:missing-skill"
    job["kind"] = "vacancy"
    job["description"] = "Kubernetes is required. Python experience preferred."
    for key in ["id", "created_at"]:
        job.pop(key, None)
    created = client.post("/v1/opportunities", json=job)
    assert created.status_code == 201, created.text
    response = client.get(f"/v1/opportunities/{created.json()['id']}/assessment/{scenario['profile']['id']}")
    requirements = response.json()["requirement_mapping"]["requirements"]
    missing = next(r for r in requirements if r["skill"] == "kubernetes")
    assert missing["importance"] == "required"
    assert missing["approved_fact_ids"] == []
    assert missing["source_quote"] == "Kubernetes is required"


def test_contact_discovery_does_not_confirm_or_invent_identity(client, scenario, monkeypatch):
    monkeypatch.setattr(
        "career_app.research.public_page",
        lambda *args: {
            "url": "https://example.org",
            "text": "For careers contact careers@example.org and team@example.org",
            "published_emails": ["careers@example.org", "team@example.org"],
        },
    )
    response = client.post(f"/v1/companies/{scenario['company']['id']}/discover-contacts")
    assert response.status_code == 200, response.text
    assert response.json()["automatically_confirmed"] is False
    candidate = response.json()["contacts"][-1]
    assert candidate["name"] is None
    assert len(client.get("/v1/contacts").json()) == 1


def test_holiday_calendars_cover_target_countries():
    from datetime import date

    from career_app.calendar import business_day, national_calendar

    for country in ["TR", "DE", "AT", "CH", "NL", "DK", "SE", "NO", "GB", "BE"]:
        assert national_calendar(country, 2026)
    assert not business_day(date(2026, 1, 1), "DE")
    assert business_day(date(2026, 11, 17), "NL")


def test_ocr_missing_tools_is_actionable(monkeypatch):
    from career_app.ocr import recognize

    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(HTTPException) as error:
        recognize(b"%PDF-test", 1)
    assert error.value.status_code == 503


def test_retention_preserves_referenced_artifacts_and_suppression(app, client, scenario):
    import os
    import time

    root = app.state.settings.artifact_dir
    orphan = root / "old-failed-generation"
    orphan.mkdir()
    os.utime(orphan, (time.time() - 172800, time.time() - 172800))
    preview = client.post("/v1/operations/retention").json()
    assert preview["dry_run"] is True
    assert "old-failed-generation" in preview["orphan_directories"]
    assert orphan.exists()
    client.post("/v1/operations/retention", params={"dry_run": False}).raise_for_status()
    assert not orphan.exists()
    assert (root / scenario["package"]["id"] / "cv.pdf").exists()


def test_real_local_scanned_pdf_ocr():
    import io
    import shutil

    from career_app.documents import extract_pdf
    from PIL import Image, ImageDraw, ImageFont

    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        pytest.skip("Local OCR tools not installed")
    image = Image.new("RGB", (1600, 500), "white")
    font = ImageFont.truetype("DejaVuSans.ttf", 36)
    draw = ImageDraw.Draw(image)
    draw.text((40, 80), "Synthetic candidate developed Python workflows.", fill="black", font=font)
    draw.text((40, 160), "Part time trainee. English language. Source evidence.", fill="black", font=font)
    data = io.BytesIO()
    image.save(data, format="PDF")
    pages = extract_pdf(data.getvalue(), ocr=True)
    assert "Python workflows" in pages[0]
    assert "Part time trainee" in pages[0]


def test_policy_auto_queues_eligible_approved_content_and_pause_cancels(app, client, scenario):
    from career_app.models import Opportunity

    with app.state.sessions() as db:
        db.get(Opportunity, scenario["job"]["id"]).eligibility = "eligible"
        db.commit()
    language = client.post(
        f"/v1/profiles/{scenario['profile']['id']}/facts",
        json={
            "section": "languages",
            "text": "English C1",
            "source_page": 1,
            "source_quote": "English C1",
            "tags": ["english"],
        },
    ).json()
    client.post(f"/v1/facts/{language['id']}/approve").raise_for_status()
    data = {
        "name": "Approved lane",
        "profile_id": scenario["profile"]["id"],
        "countries": ["NL"],
        "roles": ["applied_ai"],
        "minimum_coverage": 0,
        "mode": "policy_auto",
        "enabled": True,
    }
    key = client.post("/v1/campaigns", json=data).json()["id"]
    response = client.post("/v1/campaigns/run", json={"campaign_id": key})
    assert response.status_code == 200, response.text
    assert response.json()["results"][0]["status"] == "queued"
    assert len(client.get("/v1/outbox").json()) == 1
    assert client.post("/v1/campaigns/run", json={"campaign_id": key}).json()["results"] == []
    client.post(f"/v1/campaigns/{key}/pause").raise_for_status()
    assert client.get("/v1/outbox").json()[0]["status"] == "cancelled"
