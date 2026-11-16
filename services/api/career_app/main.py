import hmac
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from . import schemas as S
from .db import database
from .discovery import board_jobs
from .documents import extract_pdf, render_package
from .domain import (
    ROLES,
    assessment,
    audit,
    check_package,
    digest,
    fail,
    fingerprint,
    get,
    normalized,
    relevant_facts,
    serialize,
)
from .llm import propose_facts
from .models import (
    Audit,
    Company,
    Contact,
    Control,
    Fact,
    Opportunity,
    Outbox,
    Package,
    Profile,
    Source,
    Suppression,
    now,
    uid,
)
from .outbox import dispatch, recover
from .settings import Settings


def create_app(settings=None):
    settings = settings or Settings()
    engine, sessions = database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        settings.artifact_dir.mkdir(parents=True, exist_ok=True)
        yield
        engine.dispose()

    app = FastAPI(title="Career Outreach — local workspace", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.sessions = sessions
    app.state.engine = engine
    api_key = APIKeyHeader(name="X-API-Key", auto_error=False)

    def authenticate(value=Depends(api_key)):
        if not value or not hmac.compare_digest(value, settings.api_key.get_secret_value()):
            fail("invalid API key", 401)

    def session():
        with sessions() as db:
            try:
                yield db
                db.commit()
            except IntegrityError:
                db.rollback()
                fail("record already exists or conflicts with an active sequence")

    auth = [Depends(authenticate)]

    @app.get("/health")
    def health():
        try:
            with engine.connect() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            fail("database unavailable", 503)
        return {"status": "ok", "version": "0.1.0", "live_sending": False}

    @app.get("/v1/overview", dependencies=auth)
    def overview(db=Depends(session)):
        from sqlalchemy import func

        return {
            "counts": {
                m.__tablename__: db.scalar(select(func.count()).select_from(m))
                for m in [Source, Profile, Fact, Company, Opportunity, Contact, Package, Outbox]
            },
            "transport": "mailpit",
            "live_sending": False,
            "outbox": [
                serialize(o) for o in db.scalars(select(Outbox).order_by(Outbox.created_at.desc()).limit(20))
            ],
        }

    @app.get("/v1/roles", dependencies=auth)
    def roles():
        return ROLES

    @app.post("/v1/sources", dependencies=auth, status_code=201)
    def upload(file: UploadFile = File(), db=Depends(session)):
        data = file.file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            fail("CV exceeds 10 MB", 413)
        sha = digest(data)
        existing = db.scalar(select(Source).where(Source.sha256 == sha))
        if existing:
            return serialize(existing)
        pages = extract_pdf(data)
        source = Source(
            id=uid(), sha256=sha, filename=Path(file.filename or "cv.pdf").name[:255], pages=pages
        )
        db.add(source)
        folder = settings.artifact_dir / source.id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "source.pdf").write_bytes(data)
        audit(db, "source.imported", source.id, pages=len(pages), sha256=sha)
        db.flush()
        return serialize(source)

    @app.get("/v1/sources/{source_id}", dependencies=auth)
    def source(source_id: str, db=Depends(session)):
        return serialize(get(db, Source, source_id))

    @app.post("/v1/profiles", dependencies=auth, status_code=201)
    def profile(data: S.ProfileInput, db=Depends(session)):
        get(db, Source, data.source_id)
        obj = Profile(id=uid(), **data.model_dump(mode="json"))
        db.add(obj)
        audit(db, "profile.created", obj.id)
        db.flush()
        return serialize(obj)

    @app.get("/v1/profiles", dependencies=auth)
    def profiles(db=Depends(session)):
        return [serialize(p) for p in db.scalars(select(Profile).order_by(Profile.created_at))]

    @app.get("/v1/profiles/{profile_id}/facts", dependencies=auth)
    def facts(profile_id: str, db=Depends(session)):
        get(db, Profile, profile_id)
        return [serialize(f) for f in db.scalars(select(Fact).where(Fact.profile_id == profile_id))]

    def add_fact(db, profile, data):
        source = get(db, Source, profile.source_id)
        if data.source_page > len(source.pages) or normalized(data.source_quote) not in normalized(
            source.pages[data.source_page - 1]
        ):
            fail("source quote is not present on the cited CV page", 422)
        fact = Fact(id=uid(), profile_id=profile.id, **data.model_dump())
        db.add(fact)
        audit(db, "fact.proposed", fact.id, profile_id=profile.id)
        db.flush()
        return serialize(fact)

    @app.post("/v1/profiles/{profile_id}/facts", dependencies=auth, status_code=201)
    def fact(profile_id: str, data: S.FactInput, db=Depends(session)):
        return add_fact(db, get(db, Profile, profile_id), data)

    @app.post("/v1/profiles/{profile_id}/propose-facts", dependencies=auth)
    def suggest(profile_id: str, db=Depends(session)):
        profile = get(db, Profile, profile_id)
        proposed = propose_facts(settings, get(db, Source, profile.source_id).pages)
        return [add_fact(db, profile, f) for f in proposed.facts]

    def revise_profile(db, profile):
        profile.revision += 1
        for p in db.scalars(select(Package).where(Package.profile_id == profile.id)):
            p.status = "approval_invalidated"
            p.approved_hash = None
            for o in db.scalars(select(Outbox).where(Outbox.package_id == p.id, Outbox.status == "queued")):
                o.status = "cancelled"

    @app.post("/v1/facts/{fact_id}/approve", dependencies=auth)
    def approve_fact(fact_id: str, db=Depends(session)):
        obj = get(db, Fact, fact_id)
        profile = db.get(Profile, obj.profile_id, with_for_update=True)
        if not obj.approved:
            obj.approved = True
            obj.approved_at = now()
            revise_profile(db, profile)
            audit(db, "fact.approved", obj.id)
        return serialize(obj)

    @app.post("/v1/facts/{fact_id}/revoke", dependencies=auth)
    def revoke_fact(fact_id: str, db=Depends(session)):
        obj = get(db, Fact, fact_id)
        profile = db.get(Profile, obj.profile_id, with_for_update=True)
        if obj.approved:
            obj.approved = False
            obj.approved_at = None
            revise_profile(db, profile)
            audit(db, "fact.revoked", obj.id)
        return serialize(obj)

    @app.post("/v1/companies", dependencies=auth, status_code=201)
    def company(data: S.CompanyInput, db=Depends(session)):
        existing = db.scalar(select(Company).where(Company.domain == data.domain))
        if existing:
            return serialize(existing)
        obj = Company(id=uid(), **data.model_dump(mode="json"))
        db.add(obj)
        db.flush()
        return serialize(obj)

    @app.get("/v1/companies", dependencies=auth)
    def companies(db=Depends(session)):
        return [
            serialize(c) for c in db.scalars(select(Company).order_by(Company.created_at.desc()).limit(200))
        ]

    @app.post("/v1/opportunities", dependencies=auth, status_code=201)
    def opportunity(data: S.OpportunityInput, db=Depends(session)):
        get(db, Company, data.company_id)
        existing = db.scalar(
            select(Opportunity).where(
                Opportunity.company_id == data.company_id, Opportunity.external_key == data.external_key
            )
        )
        if existing:
            return serialize(existing)
        obj = Opportunity(id=uid(), **data.model_dump(mode="json"))
        db.add(obj)
        audit(db, "opportunity.created", obj.id, kind=data.kind)
        db.flush()
        return serialize(obj)

    @app.get("/v1/opportunities", dependencies=auth)
    def opportunities(db=Depends(session)):
        return [
            serialize(o)
            for o in db.scalars(select(Opportunity).order_by(Opportunity.created_at.desc()).limit(200))
        ]

    @app.post("/v1/boards/import", dependencies=auth)
    def import_board(data: S.BoardInput, db=Depends(session)):
        get(db, Company, data.company_id)
        jobs = board_jobs(data.provider, data.board)
        return [
            opportunity(
                S.OpportunityInput(company_id=data.company_id, kind="vacancy", role=data.role, **j), db
            )
            for j in jobs
        ]

    @app.get("/v1/opportunities/{opportunity_id}/assessment/{profile_id}", dependencies=auth)
    def assess(opportunity_id: str, profile_id: str, db=Depends(session)):
        return assessment(db, profile_id, get(db, Opportunity, opportunity_id))

    @app.post("/v1/contacts", dependencies=auth, status_code=201)
    def contact(data: S.ContactInput, db=Depends(session)):
        get(db, Company, data.company_id)
        obj = Contact(id=uid(), **data.model_dump(mode="json"))
        # Imported evidence is not proof of current mailbox ownership; user confirmation is separate.
        db.add(obj)
        db.flush()
        return serialize(obj)

    @app.get("/v1/contacts", dependencies=auth)
    def contacts(db=Depends(session)):
        return [serialize(c) for c in db.scalars(select(Contact).limit(200))]

    @app.post("/v1/contacts/{contact_id}/confirm", dependencies=auth)
    def confirm_contact(contact_id: str, db=Depends(session)):
        obj = get(db, Contact, contact_id)
        if obj.evidence_type == "inferred_or_unconfirmed":
            fail("guessed addresses cannot be confirmed; add a contact with actual evidence")
        if obj.email.lower() not in obj.source_quote.lower() and obj.evidence_type != "user_confirmed":
            fail("published-contact evidence must contain the address")
        obj.verified_at = now()
        audit(db, "contact.user_confirmed", obj.id)
        return serialize(obj)

    @app.post("/v1/packages", dependencies=auth, status_code=201)
    def prepare(data: S.PackageInput, db=Depends(session)):
        profile = db.get(Profile, data.profile_id, with_for_update=True)
        if not profile:
            fail("Profile not found", 404)
        job = get(db, Opportunity, data.opportunity_id)
        contact = get(db, Contact, data.contact_id)
        company = get(db, Company, job.company_id)
        if contact.company_id != job.company_id:
            fail("contact belongs to another company")
        facts = relevant_facts(db, profile.id, job.role)
        sections = [
            {"title": section.title(), "items": [f.text for f in facts if f.section == section]}
            for section in ["summary", "experience", "skills", "projects", "education", "languages"]
            if any(f.section == section for f in facts)
        ]
        content = {
            "name": profile.name,
            "email": profile.email,
            "location": profile.location,
            "target_role": ROLES[job.role]["title"],
            "sections": sections,
        }
        first_line = (
            f"I am writing about the {job.title} position at {company.name}."
            if job.kind == "vacancy"
            else f"I am interested in future {ROLES[job.role]['title']} opportunities at {company.name}."
        )
        proof = [f.text for f in facts if f.section in {"experience", "projects"}][:2]
        body = (
            f"Hello {contact.name},\n\n{first_line}\n\n"
            + "\n".join(proof)
            + "\n\nMy CV is attached. Would you be open to a short conversation, or could you direct me to the appropriate team?"
            f"\n\nKind regards,\n{profile.name}\n{profile.email}"
        )
        obj = Package(
            id=uid(),
            profile_id=profile.id,
            profile_revision=profile.revision,
            opportunity_id=job.id,
            contact_id=contact.id,
            fact_ids=[f.id for f in facts],
            content=content,
            subject=f"{ROLES[job.role]['title']} — {profile.name}"[:200],
            body=body,
            recipient=contact.email,
            manifest={},
            package_hash="",
        )
        obj.manifest = render_package(settings, obj.id, content)
        obj.package_hash = fingerprint(obj)
        db.add(obj)
        audit(db, "package.prepared", obj.id, fact_ids=obj.fact_ids, package_hash=obj.package_hash)
        db.flush()
        return {**serialize(obj), "assessment": assessment(db, profile.id, job)}

    @app.get("/v1/packages", dependencies=auth)
    def packages(db=Depends(session)):
        return [
            serialize(p) for p in db.scalars(select(Package).order_by(Package.created_at.desc()).limit(200))
        ]

    @app.get("/v1/packages/{package_id}", dependencies=auth)
    def package(package_id: str, db=Depends(session)):
        return serialize(get(db, Package, package_id))

    @app.patch("/v1/packages/{package_id}", dependencies=auth)
    def edit(package_id: str, data: S.PackageEdit, db=Depends(session)):
        obj = db.get(Package, package_id, with_for_update=True)
        if not obj:
            fail("Package not found", 404)
        pending = list(db.scalars(select(Outbox).where(Outbox.package_id == obj.id)))
        if any(o.status in {"sending", "send_unknown", "delivered_to_test"} for o in pending):
            fail("attempted packages are immutable; generate a new package")
        for o in pending:
            o.status = "cancelled"
        obj.subject, obj.body = data.subject, data.body
        obj.approved_hash = None
        obj.status = "needs_review"
        obj.package_hash = fingerprint(obj)
        audit(db, "package.edited", obj.id, package_hash=obj.package_hash)
        return serialize(obj)

    @app.post("/v1/packages/{package_id}/approve", dependencies=auth)
    def approve(package_id: str, data: S.Approval, db=Depends(session)):
        obj = db.get(Package, package_id, with_for_update=True)
        if not obj:
            fail("Package not found", 404)
        check_package(db, obj, settings.artifact_dir)
        if data.package_hash != obj.package_hash:
            fail("reviewed hash is stale; reload the exact package")
        obj.approved_hash = obj.package_hash
        obj.status = "approved"
        audit(db, "package.approved", obj.id, package_hash=obj.package_hash)
        return serialize(obj)

    @app.post("/v1/packages/{package_id}/queue", dependencies=auth)
    def queue(package_id: str, db=Depends(session)):
        obj = db.get(Package, package_id, with_for_update=True)
        if not obj:
            fail("Package not found", 404)
        job = get(db, Opportunity, obj.opportunity_id)
        db.get(Company, job.company_id, with_for_update=True)
        check_package(db, obj, settings.artifact_dir)
        if obj.status != "approved" or obj.approved_hash != obj.package_hash:
            fail("approve the exact package before queueing")
        existing = db.scalar(select(Outbox).where(Outbox.package_id == obj.id))
        if existing and existing.status != "cancelled":
            return serialize(existing)
        active = db.scalar(
            select(Outbox.id).where(
                Outbox.company_id == job.company_id, Outbox.status.in_(["queued", "sending", "send_unknown"])
            )
        )
        if active:
            fail("another company sequence is active")
        if existing:
            existing.status = "queued"
            existing.due_at = now()
            audit(db, "outbox.requeued", existing.id)
            return serialize(existing)
        entry = Outbox(
            id=uid(), package_id=obj.id, company_id=job.company_id, message_id=f"<{uid()}@career.local>"
        )
        db.add(entry)
        audit(db, "outbox.queued", entry.id, package_id=obj.id)
        db.flush()
        return serialize(entry)

    @app.get("/v1/packages/{package_id}/artifacts/{fmt}", dependencies=auth)
    def artifact(package_id: str, fmt: str, db=Depends(session)):
        obj = get(db, Package, package_id)
        if fmt not in {"pdf", "docx"} or fmt not in obj.manifest:
            fail("artifact not found", 404)
        path = settings.artifact_dir / obj.id / ("cv." + fmt)
        if not path.is_file() or digest(path.read_bytes()) != obj.manifest[fmt]["sha256"]:
            fail("artifact missing or changed")
        return FileResponse(path, filename="Candidate_CV." + fmt)

    @app.get("/v1/outbox", dependencies=auth)
    def outbox(db=Depends(session)):
        return [
            serialize(o) for o in db.scalars(select(Outbox).order_by(Outbox.created_at.desc()).limit(200))
        ]

    @app.post("/v1/outbox/dispatch-test", dependencies=auth)
    def dispatch_test():
        return dispatch(sessions, settings)

    @app.post("/v1/outbox/recover", dependencies=auth)
    def recover_outbox(db=Depends(session)):
        return {"held_as_unknown": recover(db)}

    @app.post("/v1/outbox/pause", dependencies=auth)
    def pause(db=Depends(session)):
        control = get(db, Control, "global")
        db.refresh(control, with_for_update=True)
        control.dispatch_paused = True
        audit(db, "dispatch.paused", "global")
        entries = list(db.scalars(select(Outbox).where(Outbox.status == "queued").with_for_update()))
        for o in entries:
            o.status = "cancelled"
            audit(db, "outbox.cancelled", o.id)
        return {"cancelled": len(entries), "note": "already in-flight requests cannot be recalled"}

    @app.post("/v1/outbox/resume-test", dependencies=auth)
    def resume_test(db=Depends(session)):
        control = db.get(Control, "global", with_for_update=True)
        if control is None:
            control = Control(id="global", dispatch_paused=False)
            db.add(control)
        else:
            control.dispatch_paused = False
        audit(db, "dispatch.test_resumed", "global")
        return {"dispatch_paused": False, "live_sending": False}

    @app.post("/v1/suppressions", dependencies=auth, status_code=201)
    def suppress(data: S.SuppressionInput, db=Depends(session)):
        value = data.value.lower() if data.scope == "email" else data.value
        if data.scope == "company":
            get(db, Company, value)
        obj = db.scalar(
            select(Suppression).where(Suppression.scope == data.scope, Suppression.value == value)
        )
        if not obj:
            obj = Suppression(id=uid(), scope=data.scope, value=value, reason=data.reason)
            db.add(obj)
        for item in db.scalars(select(Outbox).where(Outbox.status == "queued")):
            pkg = get(db, Package, item.package_id)
            if (data.scope == "company" and item.company_id == value) or (
                data.scope == "email" and pkg.recipient.lower() == value
            ):
                item.status = "cancelled"
        audit(db, "suppression.created", obj.id, scope=data.scope)
        db.flush()
        return serialize(obj)

    @app.get("/v1/audit", dependencies=auth)
    def audit_log(db=Depends(session)):
        return [serialize(a) for a in db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(200))]

    return app
