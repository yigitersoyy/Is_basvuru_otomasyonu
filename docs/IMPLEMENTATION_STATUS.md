# Implementation status — v0.1

This is a working first increment of the architecture, not the complete autonomous application. Preparation and local testing are implemented; external outreach remains unimplemented.

## Implemented

- Compose foundation for PostgreSQL, API, Gotenberg, Mailpit, n8n and optional Ollama/Appsmith; loopback browser ports and private backend network.
- Separate n8n/application database roles and an explicit initial Alembic migration.
- Protected local secret generation, locked Python dependencies, Windows start/stop scripts and GitHub Actions checks.
- CV PDF import, source hashes/pages, optional structured local-model extraction, manual fact entry and explicit approval/revocation.
- Approved-statement selection for five role profiles. Historical content is selected unchanged rather than freely rewritten.
- Company/role/country records, vacancy/speculative separation and public ATS readers.
- Contact evidence storage, explicit confirmation and stale/guessed-contact blocks.
- DOCX/PDF generation, text validation, page/size checks, manifests and authenticated downloads.
- Exact package hash approval, edit/revision invalidation, outbox uniqueness, persistent pause, suppression and uncertain-send holds.
- Local Mailpit dispatch code with a stable Message-ID and no external transport option.
- Seven inactive n8n exports referencing real API endpoints.

## Verification performed in this development environment

- Behavior tests cover fact evidence, missing skills/languages, speculative wording, hash approval, file tampering, revision invalidation, duplicate queueing, company sequence exclusion, contact evidence, suppression, pause and uncertain-send recovery.
- Schema was applied to PostgreSQL 17.7 using Alembic-generated SQL. Database-role initialization was exercised. The final migration is also applied and compared with SQLAlchemy metadata by the automated tests.
- Real DOCX generation and native LibreOffice PDF conversion were exercised with synthetic content, including a Turkish name; final PDF text is checked.
- Compose syntax, loopback bindings, workflow-to-API routing and inactive workflow defaults are checked.
- Optional Ollama/Appsmith image tags were checked via registry manifests, without downloading their large layers.

## Environment limitations and checks still required

The development computer has approximately 8 GB of disk, no configured RTX GPU and no Gmail authorization. Downloading the n8n/Gotenberg layers exceeded its rootless Docker storage limit. Therefore:

- Full Compose startup and the `scripts/smoke.py` Gotenberg/PostgreSQL/Mailpit roundtrip remain to be run on the Windows host.
- n8n workflow import/activation has not been exercised in a running instance.
- Appsmith has not been installed/configured into a finished user interface.
- GPU inference quality/latency and local model extraction have not been benchmarked on the RTX 4060.
- No live email, OAuth request or employer contact has been made.

The smoke test is included for the local environment; unit tests use synthetic documents and a mocked transport where a real backend is unavailable. They do not establish live email delivery or safe concurrent behavior on SQLite. Production dispatch is designed for PostgreSQL row locks and a partial unique index.

## Next milestones

1. Run the complete Docker smoke test on Windows and bind the local n8n credentials.
2. Build and export the Appsmith pages using the setup contract; test review/download flows.
3. Import Yiğit's CV into private runtime storage, confirm factual statements, work rights, languages, disclosure rules and preferences. Benchmark the chosen Ollama artifact and record its digest.
4. Add bounded company research, permitted source fetch/cache, scored requirement extraction, contact discovery and official-channel fallbacks. Current ATS imports and pasted data do not provide company-wide autonomous discovery.
5. Implement campaign policies, eligibility hard filters, timezone/business-day scheduling and source refreshes. Current role matching is tag coverage, not the architecture's weighted score.
6. Implement Gmail OAuth, send reconciliation, incremental inbox synchronization, manual-reply detection, bounce/opt-out handling and a single follow-up. Add the corresponding provider contract tests before enabling a live dispatcher.
7. Add encrypted backup/restore automation, source retention, independent health notifications and the full remaining workflow inventory.
8. Complete the architecture acceptance matrix and a user-configured live pilot.

No milestone should report `sent` merely because a test message reached Mailpit or a portal application package was prepared.
