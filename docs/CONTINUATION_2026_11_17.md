# Implementation continuation — 17 November 2026

This increment was developed in the selected Linux cloud environment at `/workspace/Is_basvuru_otomasyonu`, not on the user's Windows computer. The initial checkout was clean at commit `1e159e1`; no AGENTS.md files were found. Public CV/private account data was not imported. Source changes were authorized by the user's continuation request after environment onboarding.

## Delivered

Read AI.md and CAMPAIGNS.md under docs/runbooks for current user flows. Changes include local/API selection with explicit API opt-in and endpoint/key separation; fresh Windows Ollama setup with actual VRAM reporting and exact artifact checks; bounded campaign preparation and policy approval from unchanged approved facts; sourced literal skill mapping; published contact candidates without inferred identities; manual portal handoff/confirmation; national holidays and new-subject mail review tasks; local OCR; orphan/research retention; and encrypted checkpoint manifests with isolated restore verification. Existing hash, approval, suppression, pause, active-company and uncertain-send controls remain; queueing also enforces a company cooldown.

## Executed evidence

- Frozen uv install succeeded and repeated successfully. Ruff lint and formatting checks passed.
- Final automated suite: **49 passed, zero skipped**. Includes real local scanned-PDF OCR, native LibreOffice conversion, provider contract/error behavior, campaign idempotency/approval gates, portal state separation, retention and Gmail scenarios. Hosted API/Gmail provider calls use mocks.
- Full Linux core Compose stack started: PostgreSQL, API, Gotenberg, Mailpit, Streamlit and n8n. Non-root file permissions and internal proxy exclusions were corrected. The cloud build supplies the existing trusted CA bundle through an external build context; TLS verification was retained.
- The actual smoke test passed twice: PostgreSQL migrations, real DOCX/PDF roundtrip, approved-fact package generation, exact approval, idempotent queueing, two concurrent dispatchers and exactly one matching Mailpit message with its PDF attachment. No external email was sent.
- Authenticated HTTP checks passed for overview, roles, AI settings, campaigns and response tasks; live sending remained disabled. Native Streamlit health and existing mocked page-render tests passed.
- n8n health returned HTTP 200; all **13 inactive workflows** imported successfully. No workflow was activated and real account/API credentials remain unbound. The official Docker Hub n8n 2.32.5 artifact resolved to `sha256:3647d2b986f03174a7c0c6a0cd57bc870a769ea7a5538838b94d9714b57e9057` and was used under the repository's registry alias because docker.n8n.io was blocked.
- Official restic v0.18.1 binary checksum was verified. A synthetic encrypted checkpoint restored both databases into temporary PostgreSQL databases and verified checkpoint/package artifact hashes. The active database was not replaced. This used the same cloud disk, not an independent backup device.
- Reusable cloud install/start instructions and requested network additions were saved as a draft and the install script was exercised successfully. Saving does not publish the environment or establish restoration into a new task.

## Model/hardware boundary

The official Qwen3.5 repository confirms the 9B release. The optional container pins the official Ollama stable repository tag v0.40.16. The desired runtime tag is qwen3.5:9b, replacing old defaults; exact Ollama artifact/quantization/digest and actual generation remain pending because the cloud network blocked direct library/registry access. The Windows bootstrap must pull and validate that exact artifact and stop if unavailable. It never substitutes qwen3:8b or a hosted provider. No Windows PowerShell execution, winget installation, GPU/VRAM benchmark or real Gmail authorization was performed here.

## Remaining scope — do not claim full architecture completion

Campaign automation currently works on stored opportunities and confirmed contacts. It is not a complete autonomous company-selection/research agent. Literal requirement mapping supplements the role heuristic; full semantic weighted ranking, approved multilingual paraphrase banks, whole-profile deletion and automatic professional mailbox/role verification are not implemented. Public search, contact discovery and source accessibility remain best effort; unsupported portals have an explicit manual path. Alias/forwarded replies and regional holidays still require review. No live account, paid-provider request or employer outreach has been validated.

The next implementation increment can extend these software gaps without waiting for a CV/account. User-only prerequisites should be requested together: actual source CV and disclosure/fact review; work rights/sponsorship by country, relocation/work arrangement, availability, salary and exclusions; local GPU/model report; secure local Gmail OAuth and optional API binding; independent backup location and sender/campaign approval. Never request keys/passwords in chat or commit private runtime data.
