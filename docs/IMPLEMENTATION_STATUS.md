# Implementation status — v0.2

## Implemented in code

- Local Streamlit workspace: CV upload, original source viewing, profile/fact review, companies, public search, official-source research, vacancy/speculative imports, contact evidence, CV/email review, downloads, queueing, pause, suppression and conversation status.
- PostgreSQL/Alembic persistence, locked Python dependencies and Docker/Windows setup.
- Approved-content CV selection, local Ollama proposals, DOCX/PDF generation and hash-bound approval.
- Gmail OAuth using PKCE/one-use state, encrypted refresh-token storage, authenticated sender identity and reconnect/disconnect controls.
- Live dispatch with explicit enable switch, current inbox checks, approved-package gates, eligibility/language checks, target-country send windows, daily/spacing limits and no blind retries.
- Gmail thread activity detection, company sequence cancellation, basic explicit opt-out/bounce suppression, stable Message-ID reconciliation and one reviewed follow-up after seven weekdays.
- Bounded SearXNG search and pinned-public-IP official-site fetching with HTTPS/domain/size/redirect restrictions. Greenhouse/Ashby reading remains available.
- Ten inactive n8n workflows connected to real API operations.
- Encrypted checkpoint script using installed restic, manual restore runbook and readiness screen.

## Verified here

Behavior tests cover package/profile integrity, suppression, duplicate queueing, migrations, actual native LibreOffice document conversion, Gmail adapter success/uncertainty/reply/follow-up/OAuth-state behavior, blocked private research destinations and Streamlit page rendering.

Gmail tests use a mock provider. UI tests use mock API responses. These tests exercise application behavior; they do not establish that your Google account, Windows Docker networking or GPU inference are configured.

## Required local setup and verification

1. Start the entire stack on Windows. This cloud environment has approximately 8 GB disk and could not hold all Docker layers; the full Compose smoke test has not passed here.
2. Download and benchmark the local model on your RTX 4060. No GPU is available here.
3. Enter your Google OAuth client credentials locally and authorize Gmail. No account secrets or Gmail session are available to this task.
4. Import and approve the actual CV facts, work-rights answers, contact evidence and first email package.
5. Configure independent encrypted backup storage and perform a restore drill.
6. Run a user-controlled test send, then a small reviewed company pilot before unattended operation.

## Practical limits

- Search is best-effort; source/identity review is required. There is no guaranteed free source for every employer or executive email.
- Vacancy imports do not submit employer portal forms. Those need their own supported adapters or manual submission evidence.
- Replies with new subjects outside known threads need manual Gmail review. Unclear replies and out-of-office activity conservatively stop follow-ups instead of making commitments automatically.
- Explicit plain-text opt-out phrases and sender-based bounces are recognized; other replies are flagged for review. This is not a universal multilingual semantic classifier.
- Follow-ups count weekdays, not national holidays, and need exact-package approval.
- Role prioritization currently uses explained role-tag coverage, not the architecture's full weighted requirement model. Company selection and new wording still need review.
- Full freeform policy-auto campaign generation, OCR for scanned CVs, automatic retention pruning and semantic company-wide agent research remain beyond this release. The current system can automatically dispatch approved packages through n8n; it does not invent or approve candidate facts or guessed contacts.

The project is substantially more functional than v0.1. It must not be described as completely installed or fully autonomous before the local prerequisites and remaining capability gaps are addressed.
