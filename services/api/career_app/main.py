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
    Integration,
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

    app = FastAPI(title="Career Outreach — local workspace", version="0.2.0", lifespan=lifespan)
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
        return {"status": "ok", "version": "0.2.0", "live_sending": settings.gmail_live_enabled}

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

    def selected_ai(db):
        row = db.get(Integration, "ai_selection")
        if not row:
            return settings
        data = row.payload
        return settings.model_copy(
            update={
                "ai_provider": data["provider"],
                "ollama_model": data["ollama_model"],
                "ai_api_enabled": data["api_enabled"],
                "ai_api_url": data["api_url"],
                "ai_api_model": data["api_model"],
            }
        )

    @app.get("/v1/ai/settings", dependencies=auth)
    def ai_settings(db=Depends(session)):
        configured = selected_ai(db)
        return {
            "provider": configured.ai_provider,
            "ollama_model": configured.ollama_model,
            "api_enabled": configured.ai_api_enabled,
            "api_url": configured.ai_api_url,
            "api_model": configured.ai_api_model,
            "api_key_configured": bool(configured.ai_api_key.get_secret_value()),
            "fallback": "none",
        }

    @app.put("/v1/ai/settings", dependencies=auth)
    def select_ai(data: S.AISelection, db=Depends(session)):
        from urllib.parse import urlsplit

        # A UI-selected URL must never receive an environment key intended for another host.
        if str(data.api_url).rstrip("/") != settings.ai_api_url.rstrip("/"):
            fail(
                "set AI_API_URL locally before selecting this endpoint; existing keys cannot be redirected",
                422,
            )
        if urlsplit(str(data.api_url)).scheme != "https":
            fail("AI API endpoint requires HTTPS", 422)
        row = db.get(Integration, "ai_selection")
        if row is None:
            row = Integration(id="ai_selection")
            db.add(row)
        row.payload = data.model_dump(mode="json")
        db.flush()
        audit(
            db, "ai.selection_updated", "ai_selection", provider=data.provider, api_enabled=data.api_enabled
        )
        return ai_settings(db)

    @app.post("/v1/sources", dependencies=auth, status_code=201)
    def upload(file: UploadFile = File(), ocr: bool = False, db=Depends(session)):
        data = file.file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            fail("CV exceeds 10 MB", 413)
        sha = digest(data)
        existing = db.scalar(select(Source).where(Source.sha256 == sha))
        if existing:
            return serialize(existing)
        pages = extract_pdf(data, ocr=ocr)
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
        proposed = propose_facts(selected_ai(db), get(db, Source, profile.source_id).pages)
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
        if any(o.status in {"sending", "send_unknown", "delivered_to_test", "sent"} for o in pending):
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
        from datetime import timedelta

        recent = list(
            db.scalars(
                select(Outbox).where(
                    Outbox.company_id == job.company_id,
                    Outbox.status.in_(["sent", "delivered_to_test"]),
                    Outbox.completed_at > now() - timedelta(days=60),
                )
            )
        )
        parent = obj.content.get("followup_parent")
        if any(item.id != parent for item in recent):
            fail("company is in the 60-day contact cooldown; review a new opportunity manually")
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

    @app.post("/v1/campaigns", dependencies=auth, status_code=201)
    def create_campaign(data: S.CampaignInput, db=Depends(session)):
        get(db, Profile, data.profile_id)
        key = "campaign:" + uid()
        row = Integration(id=key, payload={**data.model_dump(), "packages": {}})
        db.add(row)
        audit(db, "campaign.created", key.removeprefix("campaign:"), mode=data.mode, enabled=data.enabled)
        return {"id": key, **row.payload}

    @app.get("/v1/campaigns", dependencies=auth)
    def campaigns(db=Depends(session)):
        return [
            {"id": r.id, **r.payload}
            for r in db.scalars(select(Integration).where(Integration.id.startswith("campaign:")))
        ]

    @app.post("/v1/campaigns/{campaign_id}/pause", dependencies=auth)
    def pause_campaign(campaign_id: str, db=Depends(session)):
        row = get(db, Integration, campaign_id)
        if not campaign_id.startswith("campaign:"):
            fail("campaign not found", 404)
        row.payload = {**row.payload, "enabled": False}
        for package_id in row.payload.get("packages", {}).values():
            for entry in db.scalars(
                select(Outbox).where(Outbox.package_id == package_id, Outbox.status == "queued")
            ):
                entry.status = "cancelled"
        audit(db, "campaign.paused", campaign_id.removeprefix("campaign:"))
        return {"status": "paused"}

    @app.post("/v1/campaigns/{campaign_id}/run", dependencies=auth)
    def run_campaign(campaign_id: str, db=Depends(session)):
        from fastapi import HTTPException

        row = db.get(Integration, campaign_id, with_for_update=True)
        if row is None or not campaign_id.startswith("campaign:"):
            fail("campaign not found", 404)
        policy = dict(row.payload)
        if not policy["enabled"]:
            fail("campaign is disabled")
        profile = get(db, Profile, policy["profile_id"])
        results, prepared = [], dict(policy.get("packages", {}))
        jobs = db.scalars(
            select(Opportunity)
            .join(Company)
            .where(Company.country.in_(policy["countries"]), Opportunity.role.in_(policy["roles"]))
            .order_by(Opportunity.created_at)
            .limit(200)
        )
        for job in jobs:
            if len(results) >= policy["maximum_packages"]:
                break
            key = job.id + ":" + str(profile.revision)
            if key in prepared:
                continue
            try:
                with db.begin_nested():
                    report = assessment(db, profile.id, job)
                    if report["role_coverage"] < policy["minimum_coverage"]:
                        continue
                    candidates = list(
                        db.scalars(
                            select(Contact)
                            .where(
                                Contact.company_id == job.company_id,
                                Contact.verified_at.is_not(None),
                                Contact.evidence_type.in_(
                                    ["published_named", "published_functional", "user_confirmed"]
                                ),
                            )
                            .order_by(Contact.created_at)
                        )
                    )
                    if not candidates:
                        results.append(
                            {
                                "opportunity_id": job.id,
                                "status": "manual_contact_required",
                                "url": job.source_url,
                            }
                        )
                        continue
                    result = prepare(
                        S.PackageInput(
                            profile_id=profile.id, opportunity_id=job.id, contact_id=candidates[0].id
                        ),
                        db,
                    )
                    package_id = result["id"]
                    if policy["mode"] == "policy_auto":
                        # No novel wording is generated in this lane; all candidate statements remain approved facts.
                        if report["blockers"] or any(
                            r["importance"] == "required" and r["status"] == "gap"
                            for r in report["requirement_mapping"]["requirements"]
                        ):
                            results.append(
                                {
                                    "opportunity_id": job.id,
                                    "package_id": package_id,
                                    "status": "needs_review",
                                    "blockers": report["blockers"],
                                }
                            )
                        else:
                            approve(package_id, S.Approval(package_hash=result["package_hash"]), db)
                            queue(package_id, db)
                            audit(
                                db,
                                "campaign.policy_approved",
                                package_id,
                                campaign_id=campaign_id,
                                package_hash=result["package_hash"],
                            )
                            results.append({"package_id": package_id, "status": "queued"})
                    else:
                        results.append({"package_id": package_id, "status": "needs_review"})
                    prepared[key] = package_id
            except HTTPException as error:
                results.append({"opportunity_id": job.id, "status": "held", "reason": error.detail})
        row.payload = {**policy, "packages": prepared}
        return {"results": results, "sending_performed": False}

    @app.post("/v1/campaigns/run", dependencies=auth)
    def run_campaign_request(data: S.CampaignRun, db=Depends(session)):
        return run_campaign(data.campaign_id, db)

    @app.get("/v1/packages/{package_id}/portal-handoff", dependencies=auth)
    def portal_handoff(package_id: str, db=Depends(session)):
        package = get(db, Package, package_id)
        job = get(db, Opportunity, package.opportunity_id)
        recorded = db.get(Integration, "portal:" + package.id)
        return {
            "package_id": package.id,
            "job_url": job.source_url,
            "status": recorded.payload["status"] if recorded else "awaiting_portal_submission",
            "submission": recorded.payload if recorded else None,
            "files": {fmt: f"/v1/packages/{package.id}/artifacts/{fmt}" for fmt in package.manifest},
            "missing_answers": [
                "Confirm work rights, sponsorship, availability and all legal attestations on the employer portal"
            ],
            "note": "Email dispatch is separate and never records portal submission. Download files through authenticated requests.",
        }

    @app.post("/v1/packages/{package_id}/portal-submission", dependencies=auth)
    def portal_submission(package_id: str, data: S.PortalConfirmation, db=Depends(session)):
        from datetime import datetime

        get(db, Package, package_id)
        try:
            submitted = datetime.fromisoformat(data.submitted_at)
            if submitted.tzinfo is None or submitted > now():
                raise ValueError()
        except ValueError:
            fail("supply a non-future ISO timestamp with timezone", 422)
        key = "portal:" + package_id
        row = db.get(Integration, key)
        if row is None:
            row = Integration(id=key)
            db.add(row)
        row.payload = {
            "status": "submitted",
            "reference": data.reference,
            "submitted_at": submitted.isoformat(),
            "evidence_type": "user_recorded",
        }
        audit(db, "portal.submission_recorded", package_id)
        return row.payload

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

    from fastapi.responses import HTMLResponse

    from . import gmail
    from . import research as research_adapter
    from .models import Delivery

    @app.get("/v1/gmail/status", dependencies=auth)
    def gmail_status(db=Depends(session)):
        account = db.get(Integration, "gmail")
        return {
            "connected": bool(account),
            "email": account.payload.get("email") if account else None,
            "live_enabled": settings.gmail_live_enabled,
        }

    @app.post("/v1/gmail/connect", dependencies=auth)
    def gmail_connect(db=Depends(session)):
        return gmail.begin(db, settings)

    @app.get("/oauth/gmail/callback")
    def gmail_callback(code: str, state: str, db=Depends(session)):
        gmail.finish(db, settings, code, state)
        return HTMLResponse(
            "<h1>Gmail connected</h1><p>You can close this tab and return to the local workspace.</p>"
        )

    @app.post("/v1/gmail/disconnect", dependencies=auth)
    def gmail_disconnect(db=Depends(session)):
        for key in ["gmail", "gmail_sync", "oauth_pending"]:
            obj = db.get(Integration, key)
            if obj:
                db.delete(obj)
        return {"connected": False}

    @app.post("/v1/gmail/sync", dependencies=auth)
    def gmail_sync(db=Depends(session)):
        return gmail.sync(db, settings)

    @app.post("/v1/gmail/dispatch", dependencies=auth)
    def gmail_dispatch():
        return gmail.live_dispatch(sessions, settings)

    @app.post("/v1/followups/plan", dependencies=auth)
    def followup_plan(db=Depends(session)):
        return gmail.plan_followups(db, settings)

    @app.get("/v1/tasks", dependencies=auth)
    def response_tasks(db=Depends(session)):
        return [
            {"id": row.id, **row.payload}
            for row in db.scalars(select(Integration).where(Integration.id.startswith("mailtask:")))
        ]

    @app.get("/v1/conversations", dependencies=auth)
    def conversations(db=Depends(session)):
        return [serialize(x) for x in db.scalars(select(Delivery).limit(200))]

    @app.post("/v1/companies/{company_id}/research", dependencies=auth)
    def research(company_id: str, db=Depends(session)):
        company = get(db, Company, company_id)
        result = research_adapter.public_page(company.source_url, company.domain)
        gmail.state(db, "research:" + company_id, {**result, "at": now().isoformat()})
        audit(db, "company.researched", company_id)
        return result

    @app.post("/v1/companies/{company_id}/discover-contacts", dependencies=auth)
    def discover_contacts(company_id: str, db=Depends(session)):
        company = get(db, Company, company_id)
        result = research(company_id, db)
        proposed = []
        for email in result["published_emails"][:20]:
            existing = db.scalar(
                select(Contact).where(Contact.company_id == company.id, Contact.email == email)
            )
            if existing:
                proposed.append(serialize(existing))
                continue
            position = result["text"].lower().find(email.lower())
            quote = result["text"][max(0, position - 180) : position + len(email) + 180]
            proposed.append(
                {
                    "email": email,
                    "source_url": result["url"],
                    "source_quote": quote,
                    "status": "candidate_only",
                    "name": None,
                    "role": None,
                    "instruction": "Review identity and role, then add and explicitly confirm a contact.",
                }
            )
        return {
            "contacts": proposed,
            "status": "requires_source_review" if proposed else "manual_contact_required",
            "official_url": result["url"],
            "automatically_confirmed": False,
        }

    @app.get("/v1/discovery/search", dependencies=auth)
    def discovery_search(query: str):
        if not 3 <= len(query) <= 300:
            fail("search query must contain 3–300 characters", 422)
        return research_adapter.search(settings, query)

    @app.post("/v1/operations/retention", dependencies=auth)
    def retention(dry_run: bool = True, db=Depends(session)):
        import shutil
        from datetime import datetime, timedelta

        referenced = set(db.scalars(select(Source.id))) | set(db.scalars(select(Package.id)))
        cutoff = now() - timedelta(days=1)
        orphans = [
            path
            for path in settings.artifact_dir.iterdir()
            if path.is_dir()
            and not path.is_symlink()
            and path.name not in referenced
            and datetime.fromtimestamp(path.stat().st_mtime, cutoff.tzinfo) < cutoff
        ]
        snapshots = []
        for row in db.scalars(select(Integration).where(Integration.id.startswith("research:"))):
            timestamp = datetime.fromisoformat(row.payload["at"])
            if timestamp < now() - timedelta(days=90) and "text" in row.payload:
                snapshots.append(row.id)
                if not dry_run:
                    row.payload = {
                        "url": row.payload["url"],
                        "at": row.payload["at"],
                        "content_hash": digest(row.payload["text"].encode()),
                        "status": "expired_snapshot",
                    }
        if not dry_run:
            for path in orphans:
                shutil.rmtree(path)
            audit(
                db,
                "retention.executed",
                "retention",
                orphan_count=len(orphans),
                snapshot_count=len(snapshots),
            )
        return {
            "dry_run": dry_run,
            "orphan_directories": [p.name for p in orphans],
            "expired_snapshots": snapshots,
            "note": "Referenced CVs/packages and suppression records are retained. Backups have their own retention.",
        }

    @app.get("/v1/operations/readiness", dependencies=auth)
    def readiness(db=Depends(session)):
        import httpx

        checks = {
            "gmail_connected": bool(db.get(Integration, "gmail")),
            "gmail_client_configured": bool(
                settings.gmail_client_id and settings.gmail_client_secret.get_secret_value()
            ),
            "live_enabled": settings.gmail_live_enabled,
        }
        for name, url in {
            "pdf_converter": settings.gotenberg_url + "/health",
            "local_model": settings.ollama_url + "/api/tags",
            "search": settings.searxng_url + "/healthz",
        }.items():
            try:
                response = httpx.get(url, timeout=3)
                checks[name] = response.is_success
                if name == "local_model" and response.is_success:
                    checks["model_downloaded"] = any(
                        m.get("name") == settings.ollama_model for m in response.json().get("models", [])
                    )
            except (httpx.HTTPError, ValueError):
                checks[name] = False
        return {
            "checks": checks,
            "ready_for_live_pilot": all(
                checks.get(k, False)
                for k in ["gmail_connected", "gmail_client_configured", "live_enabled", "pdf_converter"]
            ),
            "note": "Readiness checks do not replace a reviewed test send and GPU benchmark.",
        }

    return app
