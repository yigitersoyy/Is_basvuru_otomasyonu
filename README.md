# Job Application and Outreach Automation

A personal job-search workspace built around **n8n, local Ollama, PostgreSQL, Gotenberg and Appsmith CE**. Targets junior applied AI, RAG/LLM integration, automation/Power Platform, data/BI and selected graduate ML roles in Türkiye and selected European countries.

**Current release: v0.1 — evidence-backed CV preparation and local test outbox.** This is the first implementation increment of the [full architecture](docs/Job_Application_Outreach_Architecture_EN.md). Live Gmail sending, reply synchronization, unattended contact discovery and a finished Appsmith application are still pending. Nothing in this release sends email to real recipients: dispatch is restricted to the local Mailpit service.

## What works

- Authenticated FastAPI workspace with an interactive local interface at `/docs`.
- PDF CV upload with immutable source hashes and page-by-page extracted text.
- Manual or optional local-LLM fact proposals, explicit fact approval/revocation and source-quote checks.
- Five role profiles based on the supplied candidate CV; deterministic selection of approved statements.
- Company, vacancy and speculative opportunity records; public Greenhouse/Ashby imports.
- Contact evidence and a separate user-confirmation step; guessed addresses cannot be confirmed.
- DOCX generation using docxtpl and local PDF conversion through Gotenberg.
- Exact package review and hash-bound approval, revision invalidation, authenticated artifact download.
- Durable PostgreSQL outbox, company sequence uniqueness, suppression, persistent pause and uncertain-send holds.
- Seven inactive n8n workflows connected to implemented API routes.
- Windows start/stop scripts, migration, locked dependencies and CI checks.

## Windows 11 quick start

Install Python 3.12+, Git, Docker Desktop with its WSL 2 backend, and current NVIDIA drivers if using GPU inference. Allow **at least 60 GB free disk** for the full optional stack and models. Docker Desktop is free for personal use. The app uses existing hardware, electricity and internet; it does not require a paid AI API or software subscription.

```powershell
git clone https://github.com/yigitersoyy/Is_basvuru_otomasyonu.git
cd Is_basvuru_otomasyonu
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

`start.ps1` generates local secrets once and starts the core stack. `.env` must stay private. If PowerShell policy prohibits script execution, run the equivalent commands directly:

```powershell
python scripts/configure.py
docker compose up -d --build --wait
```

| Application | Local address |
|---|---|
| Workspace API / interactive review | http://localhost:8000/docs |
| n8n | http://localhost:5678 |
| Local test mailbox | http://localhost:8025 |
| Appsmith, optional `ui` profile | http://localhost:8080 |

At `/docs`, use **Authorize** and the `API_KEY` from your private `.env` in the `X-API-Key` field. There is no shared default password. Complete n8n's local owner-account setup separately.

Read [the first-use walkthrough](docs/runbooks/FIRST_USE.md), [n8n setup](n8n/README.md), and [Appsmith setup](appsmith/README.md).

### Optional local model on your RTX 4060

```powershell
docker compose -f compose.yaml -f compose.gpu.yaml --profile ai up -d ollama
docker compose exec ollama ollama pull qwen3:8b
```

Verify actual VRAM with `nvidia-smi`. The 8B model may need a shorter context or a 4B replacement if GPU memory is insufficient. Set `OLLAMA_MODEL=qwen3:4b` in `.env`, pull that model, and recreate `api` when switching. Inference concurrency is one; cloud features are disabled. The model only proposes facts in v0.1: it never approves or sends content. Manual fact entry works without a GPU or model.

For CPU-only inference, use `docker compose --profile ai up -d ollama`. Appsmith can be started with `docker compose --profile ui up -d appsmith`; its screens still require the configuration in the setup guide.

## Verification

Development uses [uv](https://docs.astral.sh/uv/):

```sh
uv sync --locked
uv run ruff check services migrations scripts tests
uv run pytest -q
```

After the core Docker stack starts:

```sh
docker compose exec -T api python scripts/smoke.py
```

The smoke script uses a synthetic candidate, performs real PDF conversion, queues one reviewed message, races two dispatch calls and checks that exactly one matching message with its PDF appears in Mailpit. Run it against a test database without other queued messages. It creates synthetic records and does not delete existing user records.

See [verification and current limitations](docs/IMPLEMENTATION_STATUS.md) for which checks actually ran in the development environment. A passing unit suite alone does not verify the full Docker/GPU/OAuth installation.

## Repository layout

```text
services/api/career_app/  Private API, document handling, matching and outbox rules
migrations/              Versioned database schema
config/roles.json        Candidate-specific role families, no private CV/contact data
n8n/workflows/           Importable inactive workflows
appsmith/                Datasource, page and query configuration guide
scripts/                 Windows setup, configuration and integration checks
tests/                   Behavior and document validation tests
docs/runbooks/           First-use and operations instructions
```

## Architecture documents

- [English architecture plan — Markdown](docs/Job_Application_Outreach_Architecture_EN.md)
- [English architecture plan — PDF](docs/Job_Application_Outreach_Architecture_EN.pdf)
- [English architecture plan — Word](docs/Job_Application_Outreach_Architecture_EN.docx)
- [Implementation status and remaining milestones](docs/IMPLEMENTATION_STATUS.md)

Original CV uploads, generated application documents, secrets and database contents are local runtime data, excluded from Git. Public professional addresses require appropriate evidence and review; free infrastructure cannot guarantee that every employer has a usable contact address.
