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

## November 17 continuation

Implemented in this increment:

- Detect/install native Windows Ollama through winget, inspect real NVIDIA VRAM, pull the exact requested model, validate metadata/digest/structured inference and save a private verification report. The requested default is Qwen3.5 9B; no older-model fallback is used.
- Explicit local/OpenAI-compatible API selection and model/endpoint configuration in Streamlit. Keys remain in local environment configuration; API access is off by default and never a fallback. Redirecting an existing API key to a different UI-selected host is blocked.
- Stored bounded campaigns with draft/review/policy-auto modes, country/role scope, deterministic approved-content preparation, repeat-run deduplication, pause/cancel and preserved send gates. Known eligibility/language/seniority blockers and mandatory literal skill gaps prevent policy approval.
- Literal source requirement mapping with approved fact IDs and visible gaps; published email candidates without invented names/roles or automatic confirmation.
- Separate portal handoff/submission evidence, authenticated artifact routes and user-recorded submission references. Email status never implies portal submission.
- National public holiday scheduling, conservative new-subject contact-message holds and visible response tasks, additional multilingual opt-out phrases and a 60-day company cooldown.
- Optional bounded local Poppler/Tesseract OCR, retention preview/apply for stale raw research/orphan artifacts, checkpoint SHA-256 manifests and automated isolated database/artifact restore verification.
- Docker non-root source-read permissions, internal proxy exclusions and cloud-specific trusted-CA build setup.

## Verified here

Behavior tests cover package/profile integrity, suppression, duplicate queueing, migrations, actual native LibreOffice document conversion, Gmail adapter success/uncertainty/reply/follow-up/OAuth-state behavior, blocked private research destinations and Streamlit page rendering.

Gmail tests use a mock provider. UI tests use mock API responses. These tests exercise application behavior; they do not establish that your Google account, Windows Docker networking or GPU inference are configured.

## Required local setup and verification

1. Validate the entire stack on Windows. The Linux cloud core stack and real PostgreSQL/Gotenberg/Mailpit smoke test now pass; this does not validate Windows Docker Desktop networking.
2. Run the exact model verification/benchmark on your RTX 4060. Qwen’s official repository confirms Qwen3.5-9B exists; this cloud could not reach the Ollama library/registry, so its exact Ollama artifact/digest and GPU inference remain unverified. No GPU is available here.
3. Enter your Google OAuth client credentials locally and authorize Gmail. No account secrets or Gmail session are available to this task.
4. Import and approve the actual CV facts, work-rights answers, contact evidence and first email package.
5. Configure independent encrypted backup storage and perform a restore drill.
6. Run a user-controlled test send, then a small reviewed company pilot before unattended operation.

## Practical limits

- Search is best-effort; source/identity review is required. There is no guaranteed free source for every employer or executive email.
- Vacancy imports do not submit employer portal forms. Those need their own supported adapters or manual submission evidence.
- Replies with new subjects outside known threads need manual Gmail review. Unclear replies and out-of-office activity conservatively stop follow-ups instead of making commitments automatically.
- Explicit plain-text opt-out phrases and sender-based bounces are recognized; other replies are flagged for review. This is not a universal multilingual semantic classifier.
- Follow-ups count weekdays and national holidays; regional holidays need review. Follow-ups need exact-package approval.
- Role prioritization currently uses explained role-tag coverage, not the architecture's full weighted requirement model. Company selection and new wording still need review.
- Full freeform company-research agents, semantic weighted ranking, approved paraphrase/translation banks, automatic mailbox identity verification and complete personal-profile deletion remain beyond this increment. Campaign automation operates on stored opportunities and explicitly confirmed contacts; retention covers stale research and orphan artifacts, not wholesale record deletion. The current system can automatically dispatch approved packages through n8n; it does not invent or approve candidate facts or guessed contacts.

The project is substantially more functional than v0.1. It must not be described as completely installed or fully autonomous before the local prerequisites and remaining capability gaps are addressed.


Current cloud evidence: 49 automated tests passed in the final run (no skipped tests). Native scanned-PDF OCR, mocked API/Gmail contracts, policy-auto gates, repeated campaign runs, portal state separation and retention are covered. The actual core smoke exercised real PostgreSQL migrations, Gotenberg PDF roundtrip, idempotent queueing, concurrent dispatch and exactly one Mailpit message/attachment. n8n 2.32.5 started and all 13 current inactive workflows imported successfully. An encrypted restic checkpoint restored both databases into isolated temporary PostgreSQL databases and verified package hashes; it used synthetic data on the same cloud disk. No real Gmail OAuth, paid API call, employer email, independent-drive restore or Windows/GPU benchmark was performed.
