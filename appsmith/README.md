# Appsmith CE connection and initial workspace configuration

The API is usable through `/docs` now. A finished Appsmith application export is **not** included in v0.1; these are concrete datasource and page instructions for the next UI milestone. Starting the `ui` profile installs the existing Appsmith builder, not a preconfigured dashboard.

```powershell
docker compose --profile ui up -d appsmith
```

Open `http://localhost:8080`, create the local owner account and an application named **Career Workspace**. Appsmith is optional and relatively memory-intensive; enable it after the core stack is healthy.

## Datasource

Create an **Authenticated API** datasource:

- Base URL: `http://api:8000` (the container service name, not localhost).
- Authentication: API key/header as supported by the pinned builder.
- Header: `X-API-Key`, value the private key from `.env`.
- Keep the key in the server-side datasource, never a JS object, widget or exported shared query.

Use API queries rather than exposing a database-owner credential to the application. Route parameters use selected row IDs from the corresponding API response.

## Pages to configure

| Page | Query | Widgets/actions |
|---|---|---|
| Overview | `GET /v1/overview`, `GET /v1/outbox` | Counts, status table, pause button `POST /v1/outbox/pause` |
| Profile | `GET /v1/profiles`, `GET /v1/profiles/{id}/facts` | Profile selector; fact/source-quote table; approve/revoke buttons |
| Companies | `GET /v1/companies`, `POST /v1/companies` | Company table, domain/country/source form |
| Opportunities | `GET /v1/opportunities`, assessment endpoint | Vacancy/speculative filter, role/eligibility labels, assessment JSON |
| Contacts | `GET /v1/contacts`, `POST /v1/contacts`, confirmation action | Evidence quote/URL and review status |
| Review | `GET /v1/packages/{id}`, artifact endpoint, `PATCH`, `/approve` | Exact subject/body, fact list, artifact download, approve latest hash |
| Operations | `GET /v1/audit`, outbox table | Audit table, unknown-send status, recover, resume-test |

A prepare action calls `POST /v1/packages` using selected profile/opportunity/contact IDs. A queue action uses only the approved package ID. Bind action results to query refreshes; display server 409/422 explanations instead of treating failures as success.

Artifact downloads require authenticated API responses. Do not paste the API key into download URLs or make documents public to support a viewer. Until an authenticated Appsmith binary-download query is configured and tested, download through the API's interactive docs.

Do not add a Gmail send button in the UI before the live transport milestone and inbox synchronization are implemented.
