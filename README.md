# Job Application and Outreach Automation

A personal job-search workspace built around **n8n, local Ollama, PostgreSQL, Gotenberg and Streamlit**. Targets junior applied AI, RAG/LLM integration, automation/Power Platform, data/BI and selected graduate ML roles in Türkiye and selected European countries.

**Current release: v0.2 — local workspace, Gmail integration and sourced research.** Gmail OAuth, live dispatch, reply checks, reviewed follow-ups and the ready-to-use Streamlit interface are implemented. Real Gmail authorization, full Docker/GPU testing and the first live pilot still require your local setup. Live sending is disabled by default.

The local interface uses **Streamlit** instead of the initially proposed Appsmith, reducing setup and memory use while retaining n8n orchestration. Appsmith remains an optional legacy builder profile.

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
- Ten inactive n8n workflows connected to implemented API routes.
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
| Ready-to-use local workspace | http://localhost:8080 |

At `/docs`, use **Authorize** and the `API_KEY` from your private `.env` in the `X-API-Key` field. There is no shared default password. Complete n8n's local owner-account setup separately.

Open the workspace to upload the CV, review facts, add researched opportunities/contacts, preview documents, approve packages and manage conversations. Then read [Gmail setup](docs/runbooks/GMAIL.md), [n8n setup](n8n/README.md) and [encrypted backups](docs/runbooks/BACKUP.md).

For public company/vacancy discovery, run `docker compose --profile research up -d searxng` and use the workspace search. Official-page research only fetches HTTPS sources on the selected company domain; public IPs are pinned, redirects are blocked and responses are bounded. Published addresses require review before contact confirmation.


### Optional local model on your RTX 4060

```powershell
docker compose -f compose.yaml -f compose.gpu.yaml --profile ai up -d ollama
docker compose exec ollama ollama pull qwen3:8b
```

Verify actual VRAM with `nvidia-smi`. The 8B model may need a shorter context or a 4B replacement if GPU memory is insufficient. Set `OLLAMA_MODEL=qwen3:4b` in `.env`, pull that model, and recreate `api` when switching. Inference concurrency is one; cloud features are disabled. The model only proposes facts: it never approves or sends content. Manual fact entry works without a GPU or model.

For CPU-only inference, use `docker compose --profile ai up -d ollama`. The optional legacy Appsmith builder is available with `docker compose --profile legacy-appsmith up -d appsmith` at port 8081; the default Streamlit workspace needs no page configuration.

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
services/workspace/      Ready-to-use Streamlit user interface
appsmith/                Optional legacy builder configuration
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
