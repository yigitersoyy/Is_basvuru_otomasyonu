import json
import shutil
import subprocess
from pathlib import Path

import httpx
import pytest
from career_app.documents import extract_pdf, render_package
from career_app.llm import propose_facts
from career_app.settings import Settings


def test_real_libreoffice_pdf_text_validation(tmp_path, monkeypatch):
    if not shutil.which("soffice"):
        pytest.skip("native LibreOffice not installed; Compose smoke test exercises Gotenberg instead")
    settings = Settings(api_key="x" * 48, artifact_dir=tmp_path)
    calls = []

    def converter(url, *, files, timeout):
        calls.append(url)
        name, data, *_ = files["files"]
        source = tmp_path / name
        source.write_bytes(data)
        result = subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(source)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        return httpx.Response(
            200, content=source.with_suffix(".pdf").read_bytes(), request=httpx.Request("POST", url)
        )

    monkeypatch.setattr("career_app.documents.httpx.post", converter)
    content = {
        "name": "Yiğit Ersoy",
        "email": "candidate@example.org",
        "location": "Istanbul",
        "target_role": "Junior AI Engineer",
        "sections": [
            {
                "title": "Experience",
                "items": ["AI Agent Trainee (Part-time), Oct 2025 – Jul 2026. Built local RAG workflows."],
            }
        ],
    }
    manifest = render_package(settings, "native-check", content)
    assert manifest["pdf"]["pages"] == 1
    assert "Built local RAG workflows." in extract_pdf((tmp_path / "native-check/cv.pdf").read_bytes())[0]
    assert calls == [settings.gotenberg_url + "/forms/libreoffice/convert"]


def test_local_model_quote_fabrication_is_rejected(tmp_path, monkeypatch):
    settings = Settings(api_key="x" * 48, artifact_dir=tmp_path)
    invented = {
        "facts": [
            {
                "section": "experience",
                "text": "Invented result",
                "source_page": 1,
                "source_quote": "Never appeared here",
                "tags": [],
            }
        ]
    }

    def model(url, **kwargs):
        return httpx.Response(
            200, json={"message": {"content": json.dumps(invented)}}, request=httpx.Request("POST", url)
        )

    monkeypatch.setattr("career_app.llm.httpx.post", model)
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as e:
        propose_facts(settings, ["Original CV text."])
    assert e.value.status_code == 422


def test_workflows_call_real_authenticated_routes(app):
    paths = {route.path for route in app.routes}
    for path in Path("n8n/workflows").glob("*.json"):
        flow = json.loads(path.read_text())
        assert flow["active"] is False
        node = next(n for n in flow["nodes"] if n["name"] == "Career API")
        assert node["parameters"]["url"].removeprefix("http://api:8000") in paths
        assert node["parameters"]["authentication"] == "genericCredentialType"
        for n in flow["nodes"]:
            if n["type"] == "n8n-nodes-base.webhook":
                assert n["parameters"]["authentication"] == "headerAuth"
