import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def uid() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Record:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Source(Record, Base):
    __tablename__ = "sources"
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    filename: Mapped[str] = mapped_column(String(255))
    pages: Mapped[list] = mapped_column(JSON)


class Profile(Record, Base):
    __tablename__ = "profiles"
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254))
    location: Mapped[str] = mapped_column(String(160))
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id"))
    revision: Mapped[int] = mapped_column(Integer, default=1)


class Fact(Record, Base):
    __tablename__ = "facts"
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    section: Mapped[str] = mapped_column(String(40))
    text: Mapped[str] = mapped_column(Text)
    source_page: Mapped[int] = mapped_column(Integer)
    source_quote: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Company(Record, Base):
    __tablename__ = "companies"
    name: Mapped[str] = mapped_column(String(200))
    domain: Mapped[str] = mapped_column(String(253), unique=True)
    country: Mapped[str] = mapped_column(String(2))
    source_url: Mapped[str] = mapped_column(Text)


class Opportunity(Record, Base):
    __tablename__ = "opportunities"
    __table_args__ = (UniqueConstraint("company_id", "external_key"),)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    external_key: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(String(40))
    description: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    eligibility: Mapped[str] = mapped_column(String(20), default="unknown")
    required_languages: Mapped[list] = mapped_column(JSON, default=list)


class Contact(Record, Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("company_id", "email"),)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(254))
    title: Mapped[str] = mapped_column(String(160))
    evidence_type: Mapped[str] = mapped_column(String(30))
    source_url: Mapped[str] = mapped_column(Text)
    source_quote: Mapped[str] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Package(Record, Base):
    __tablename__ = "packages"
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"))
    profile_revision: Mapped[int] = mapped_column(Integer)
    opportunity_id: Mapped[str] = mapped_column(ForeignKey("opportunities.id"))
    contact_id: Mapped[str] = mapped_column(ForeignKey("contacts.id"))
    fact_ids: Mapped[list] = mapped_column(JSON)
    content: Mapped[dict] = mapped_column(JSON)
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    recipient: Mapped[str] = mapped_column(String(254))
    manifest: Mapped[dict] = mapped_column(JSON)
    package_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="needs_review")
    approved_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Outbox(Record, Base):
    __tablename__ = "outbox"
    __table_args__ = (
        Index(
            "uq_active_company_sequence",
            "company_id",
            unique=True,
            postgresql_where=text("status IN ('queued','sending','send_unknown')"),
            sqlite_where=text("status IN ('queued','sending','send_unknown')"),
        ),
    )
    package_id: Mapped[str] = mapped_column(ForeignKey("packages.id"), unique=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    message_id: Mapped[str] = mapped_column(String(200), unique=True)
    attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)


class Suppression(Record, Base):
    __tablename__ = "suppressions"
    scope: Mapped[str] = mapped_column(String(20))
    value: Mapped[str] = mapped_column(String(254), index=True)
    reason: Mapped[str] = mapped_column(String(200))
    __table_args__ = (UniqueConstraint("scope", "value"),)


class Audit(Record, Base):
    __tablename__ = "audit_events"
    action: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(36))
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class Control(Base):
    __tablename__ = "system_control"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    dispatch_paused: Mapped[bool] = mapped_column(Boolean, default=False)


class Integration(Base):
    __tablename__ = "integrations"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[str] = mapped_column(ForeignKey("outbox.id"), primary_key=True)
    provider_id: Mapped[str] = mapped_column(String(100))
    thread_id: Mapped[str] = mapped_column(String(100), index=True)
    replied: Mapped[bool] = mapped_column(Boolean, default=False)
    event: Mapped[str] = mapped_column(String(40), default="awaiting_reply")
