import io

import pytest
from alembic import command
from alembic.config import Config
from career_app.main import create_app
from career_app.settings import Settings
from fastapi.testclient import TestClient
from pypdf import PdfWriter


@pytest.fixture
def app(tmp_path, monkeypatch):
    url = "sqlite:///" + str(tmp_path / "test.db")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("API_KEY", "x" * 48)
    command.upgrade(Config("alembic.ini"), "head")
    settings = Settings(database_url=url, api_key="x" * 48, artifact_dir=tmp_path / "artifacts")
    application = create_app(settings)
    return application


@pytest.fixture
def client(app):
    with TestClient(app, headers={"X-API-Key": "x" * 48}) as c:
        yield c


@pytest.fixture
def fake_render(monkeypatch):
    from career_app.documents import render_docx
    from career_app.domain import digest

    def render(settings, package_id, content):
        folder = settings.artifact_dir / package_id
        folder.mkdir(parents=True, exist_ok=True)
        docx = folder / "cv.docx"
        render_docx(docx, content)
        # A real conversion is tested separately against Gotenberg in the Compose smoke test.
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        data = io.BytesIO()
        writer.write(data)
        (folder / "cv.pdf").write_bytes(data.getvalue())
        return {
            ext: {
                "sha256": digest((folder / ("cv." + ext)).read_bytes()),
                "size": (folder / ("cv." + ext)).stat().st_size,
            }
            for ext in ["docx", "pdf"]
        }

    monkeypatch.setattr("career_app.main.render_package", render)
    return render


@pytest.fixture
def scenario(client, app, fake_render):
    from career_app.models import Source, uid

    with app.state.sessions() as db:
        src = Source(
            id=uid(),
            sha256="a" * 64,
            filename="synthetic.pdf",
            pages=[
                "Jane Example. Junior AI trainee, part-time, Jan 2025 - Jul 2026. Built Python RAG pipelines. "
                "English C1. BSc Computer Engineering."
            ],
        )
        db.add(src)
        db.commit()
        source_id = src.id

    def post(path, data):
        r = client.post(path, json=data)
        assert r.status_code in [200, 201], r.text
        return r.json()

    p = post(
        "/v1/profiles",
        {"name": "Jane Example", "email": "jane@example.org", "location": "Istanbul", "source_id": source_id},
    )
    f = post(
        f"/v1/profiles/{p['id']}/facts",
        {
            "section": "experience",
            "text": "Junior AI trainee, part-time, Jan 2025 - Jul 2026. Built Python RAG pipelines.",
            "source_page": 1,
            "source_quote": "Built Python RAG pipelines.",
            "tags": ["python", "rag"],
        },
    )
    post(f"/v1/facts/{f['id']}/approve", {})
    company = post(
        "/v1/companies",
        {
            "name": "Example Tools",
            "domain": "example.org",
            "country": "NL",
            "source_url": "https://example.org/",
        },
    )
    job = post(
        "/v1/opportunities",
        {
            "company_id": company["id"],
            "external_key": "spec:ai",
            "title": "Junior AI Engineer",
            "kind": "speculative",
            "role": "applied_ai",
            "description": "Future AI integration opportunities",
            "source_url": "https://example.org/",
            "required_languages": ["English"],
        },
    )
    contact = post(
        "/v1/contacts",
        {
            "company_id": company["id"],
            "name": "Recruiting Team",
            "email": "careers@example.org",
            "title": "Recruiting",
            "evidence_type": "published_functional",
            "source_url": "https://example.org/careers",
            "source_quote": "Apply: careers@example.org",
        },
    )
    post(f"/v1/contacts/{contact['id']}/confirm", {})
    package = post(
        "/v1/packages", {"profile_id": p["id"], "opportunity_id": job["id"], "contact_id": contact["id"]}
    )
    return {
        "profile": p,
        "fact": f,
        "company": company,
        "job": job,
        "contact": contact,
        "package": package,
        "post": post,
    }
