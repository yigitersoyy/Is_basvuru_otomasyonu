"""Initial personal workspace schema. Future changes require new migration revisions."""

from alembic import op
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def table(name, *columns, **kw):
    return op.create_table(
        name,
        Column("id", String(36), primary_key=True),
        Column("created_at", DateTime(timezone=True), nullable=False),
        *columns,
        **kw,
    )


def upgrade():
    op.create_table(
        "system_control",
        Column("id", String(20), primary_key=True),
        Column("dispatch_paused", Boolean, nullable=False),
    )
    op.execute("INSERT INTO system_control (id, dispatch_paused) VALUES ('global', false)")
    table(
        "sources",
        Column("sha256", String(64), nullable=False, unique=True),
        Column("filename", String(255), nullable=False),
        Column("pages", JSON, nullable=False),
    )
    table(
        "profiles",
        Column("name", String(160), nullable=False),
        Column("email", String(254), nullable=False),
        Column("location", String(160), nullable=False),
        Column("source_id", String(36), ForeignKey("sources.id"), nullable=False),
        Column("revision", Integer, nullable=False),
    )
    table(
        "facts",
        Column("profile_id", String(36), ForeignKey("profiles.id"), nullable=False, index=True),
        Column("section", String(40), nullable=False),
        Column("text", Text, nullable=False),
        Column("source_page", Integer, nullable=False),
        Column("source_quote", Text, nullable=False),
        Column("tags", JSON, nullable=False),
        Column("approved", Boolean, nullable=False),
        Column("approved_at", DateTime(timezone=True)),
    )
    table(
        "companies",
        Column("name", String(200), nullable=False),
        Column("domain", String(253), nullable=False, unique=True),
        Column("country", String(2), nullable=False),
        Column("source_url", Text, nullable=False),
    )
    table(
        "opportunities",
        Column("company_id", String(36), ForeignKey("companies.id"), nullable=False, index=True),
        Column("external_key", String(255), nullable=False),
        Column("title", String(200), nullable=False),
        Column("kind", String(20), nullable=False),
        Column("role", String(40), nullable=False),
        Column("description", Text, nullable=False),
        Column("source_url", Text, nullable=False),
        Column("eligibility", String(20), nullable=False),
        Column("required_languages", JSON, nullable=False),
        UniqueConstraint("company_id", "external_key"),
    )
    table(
        "contacts",
        Column("company_id", String(36), ForeignKey("companies.id"), nullable=False, index=True),
        Column("name", String(160), nullable=False),
        Column("email", String(254), nullable=False),
        Column("title", String(160), nullable=False),
        Column("evidence_type", String(30), nullable=False),
        Column("source_url", Text, nullable=False),
        Column("source_quote", Text, nullable=False),
        Column("verified_at", DateTime(timezone=True)),
        UniqueConstraint("company_id", "email"),
    )
    table(
        "packages",
        Column("profile_id", String(36), ForeignKey("profiles.id"), nullable=False),
        Column("profile_revision", Integer, nullable=False),
        Column("opportunity_id", String(36), ForeignKey("opportunities.id"), nullable=False),
        Column("contact_id", String(36), ForeignKey("contacts.id"), nullable=False),
        Column("fact_ids", JSON, nullable=False),
        Column("content", JSON, nullable=False),
        Column("subject", String(200), nullable=False),
        Column("body", Text, nullable=False),
        Column("recipient", String(254), nullable=False),
        Column("manifest", JSON, nullable=False),
        Column("package_hash", String(64), nullable=False),
        Column("status", String(30), nullable=False),
        Column("approved_hash", String(64)),
    )
    table(
        "outbox",
        Column("package_id", String(36), ForeignKey("packages.id"), nullable=False, unique=True),
        Column("company_id", String(36), ForeignKey("companies.id"), nullable=False, index=True),
        Column("status", String(30), nullable=False, index=True),
        Column("due_at", DateTime(timezone=True), nullable=False, index=True),
        Column("message_id", String(200), nullable=False, unique=True),
        Column("attempted_at", DateTime(timezone=True)),
        Column("completed_at", DateTime(timezone=True)),
        Column("error_code", String(50)),
    )
    # A database guarantee in addition to application-level company locking.
    op.create_index(
        "uq_active_company_sequence",
        "outbox",
        ["company_id"],
        unique=True,
        postgresql_where=text("status IN ('queued','sending','send_unknown')"),
        sqlite_where=text("status IN ('queued','sending','send_unknown')"),
    )
    table(
        "suppressions",
        Column("scope", String(20), nullable=False),
        Column("value", String(254), nullable=False, index=True),
        Column("reason", String(200), nullable=False),
        UniqueConstraint("scope", "value"),
    )
    table(
        "audit_events",
        Column("action", String(80), nullable=False),
        Column("entity_id", String(36), nullable=False),
        Column("details", JSON, nullable=False),
    )


def downgrade():
    for name in [
        "system_control",
        "audit_events",
        "suppressions",
        "outbox",
        "packages",
        "contacts",
        "opportunities",
        "companies",
        "facts",
        "profiles",
        "sources",
    ]:
        op.drop_table(name)
