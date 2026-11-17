import hashlib
import json
import re
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select

from .models import Audit, Contact, Fact, Opportunity, Package, Profile, Suppression, now

ROOT = Path(__file__).resolve().parents[3]
ROLES = json.loads((ROOT / "config/roles.json").read_text())


def fail(message: str, status: int = 409):
    raise HTTPException(status, detail=message)


def get(session, model, key):
    obj = session.get(model, key)
    if obj is None:
        fail(f"{model.__name__} not found", 404)
    return obj


def audit(session, action: str, entity_id: str, **details):
    session.add(Audit(action=action, entity_id=entity_id, details=details))


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(package: Package) -> str:
    fields = {
        k: getattr(package, k)
        for k in (
            "profile_id",
            "profile_revision",
            "opportunity_id",
            "contact_id",
            "fact_ids",
            "content",
            "subject",
            "body",
            "recipient",
            "manifest",
        )
    }
    return digest(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode())


def relevant_facts(session, profile_id: str, role: str) -> list[Fact]:
    facts = list(session.scalars(select(Fact).where(Fact.profile_id == profile_id, Fact.approved.is_(True))))
    if not facts:
        fail("approve candidate facts before generating a package")
    tags = ROLES[role]["tags"]
    scored = sorted(facts, key=lambda f: (-sum(t in f.text.lower() or t in f.tags for t in tags), f.id))
    selected = []
    for section, maximum in [
        ("summary", 1),
        ("experience", 6),
        ("skills", 3),
        ("projects", 3),
        ("education", 2),
        ("languages", 2),
    ]:
        selected.extend([f for f in scored if f.section == section][:maximum])
    return selected


def assessment(session, profile_id: str, opportunity: Opportunity):
    profile = get(session, Profile, profile_id)
    facts = relevant_facts(session, profile.id, opportunity.role)
    text = " ".join(f.text.lower() for f in facts)
    role_tags = ROLES[opportunity.role]["tags"]
    hits = {tag: [f.id for f in facts if tag in f.text.lower() or tag in f.tags] for tag in role_tags}
    # This is a role-tag coverage heuristic, never an ATS score or a hiring probability.
    score = round(100 * sum(bool(ids) for ids in hits.values()) / len(hits))
    blockers = []
    if opportunity.eligibility != "eligible":
        blockers.append("work eligibility is " + opportunity.eligibility)
    for lang in opportunity.required_languages:
        if lang.lower() not in text:
            blockers.append("required language needs confirmation: " + lang)
    if re.search(r"\b(senior|principal|lead|head of|director)\b", opportunity.title, re.I):
        blockers.append("seniority requires manual review")
    from .matching import requirement_map

    return {
        "requirement_mapping": requirement_map(opportunity, facts),
        "role_coverage": score,
        "evidence": hits,
        "missing_tags": [t for t, ids in hits.items() if not ids],
        "blockers": blockers,
        "method": "approved_fact_role_tag_coverage_v1",
    }


def suppressed(session, company_id: str, email: str) -> bool:
    return (
        session.scalar(
            select(Suppression.id).where(
                ((Suppression.scope == "company") & (Suppression.value == company_id))
                | ((Suppression.scope == "email") & (Suppression.value == email.lower()))
            )
        )
        is not None
    )


def check_package(session, package: Package, artifact_dir: Path):
    profile = get(session, Profile, package.profile_id)
    if profile.revision != package.profile_revision:
        fail("profile changed; regenerate the package")
    for fid in package.fact_ids:
        fact = get(session, Fact, fid)
        if not fact.approved or fact.profile_id != profile.id:
            fail("package contains a fact that is no longer approved")
    contact = get(session, Contact, package.contact_id)
    opportunity = get(session, Opportunity, package.opportunity_id)
    if contact.company_id != opportunity.company_id or contact.email != package.recipient:
        fail("recipient/company mismatch")
    if contact.evidence_type == "inferred_or_unconfirmed" or contact.verified_at is None:
        fail("contact must be explicitly confirmed before queueing")
    verified = contact.verified_at
    if verified.tzinfo is None:
        from datetime import UTC

        verified = verified.replace(tzinfo=UTC)
    if (now() - verified).days >= 30:
        fail("contact confirmation is stale")
    if suppressed(session, opportunity.company_id, contact.email):
        fail("contact or company is suppressed")
    # The first milestone permits unknown work rights only for an explicitly reviewed inquiry.
    if opportunity.eligibility == "ineligible":
        fail("candidate is ineligible for this opportunity")
    for fmt, metadata in package.manifest.items():
        path = artifact_dir / package.id / ("cv." + fmt)
        if not path.is_file() or digest(path.read_bytes()) != metadata["sha256"]:
            fail("artifact missing or changed; regenerate the package")
    if fingerprint(package) != package.package_hash:
        fail("package content changed")
    if "\r" in package.subject or "\n" in package.subject:
        fail("invalid mail subject")
    return opportunity, contact


def serialize(obj):
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
