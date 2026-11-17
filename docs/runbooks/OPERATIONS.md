# Operations — local first increment

## Start, stop, inspect

```powershell
docker compose up -d --build --wait
docker compose ps
docker compose logs --tail=60 api
powershell -File scripts/stop.ps1
```

Use `stop`, not `down -v`, to retain user data. The initial database script runs only when the PostgreSQL volume is new. Changing a password in `.env` does not rotate an already-created database role; preserve the original `.env` and use an explicit password-rotation procedure if needed.

The PostgreSQL initialization script must be readable by its container. Git tracks its executable bit; on Windows, ensure the repository is accessible to Docker Desktop. The app never mounts the original uploaded chat attachment into another service automatically.

The API runs its versioned migration before serving requests. If migration fails, inspect the error and restore from backup as appropriate. Do not mark an unknown schema as migrated to hide a failure.

## Secrets and access

Protect `.env`, Docker volume data and backups. `.env` contains the API key, n8n encryption key and database passwords. Never paste it into an issue or CI log. Ordinary workflow JSON exports omit secret values. OpenAPI docs are accessible only on a loopback-bound local service; all business-data operations require the API key.

PostgreSQL, Mailpit SMTP, Gotenberg and Ollama have no public host bindings. Do not expose the services using router port forwarding or a public tunnel without an additional access design. An `@gmail.com` sender, OAuth token and arbitrary SMTP server are not supported by the v0.1 dispatcher.

## Manual checkpoint before upgrades

Use scripts/backup.py and scripts/restore.py as described in BACKUP.md for encrypted checkpoints and isolated restore verification. The following manual procedure remains available for diagnostics:

1. Stop `api` and `n8n` to quiesce writes. If Appsmith is enabled, stop it too.
2. Make a PostgreSQL dump of both `career` and `n8n` using `pg_dump -Fc` inside `postgres`. Store byte output using a binary-safe tool; Windows PowerShell 5 redirection can corrupt binary output. A safe approach is `docker compose exec -T postgres pg_dump -U career -Fc -f /tmp/career.dump career`, followed by `docker compose cp postgres:/tmp/career.dump <private-backup-directory>`; repeat using the n8n role/database.
3. Copy the stopped API artifact directory and n8n's entire persistent state with `docker compose cp`. Include the `.env` recovery keys in a protected backup location. If Appsmith is used, follow its version-specific supported backup procedure; database dumps alone do not back up its application state.
4. Encrypt the checkpoint using an existing trusted local encryption tool and store it on independent storage. A plain dump on the same drive is not the architecture's encrypted independent backup.
5. Resume the services and test their health. Keep an upgrade checkpoint until the upgraded state is verified.

For restore, start in paused test mode, restore the matching database/artifact/key versions, and verify hashes before resuming. Gmail synchronization and uncertain-send reconciliation must succeed before outbound work resumes. Restored pending entries require review; do not blindly requeue them.

## Failure states

- HTTP 401: wrong/missing local API key.
- HTTP 409: stale approval, conflicting sequence, changed artifact/profile, unconfirmed contact or suppression. Read the returned explanation.
- HTTP 422: invalid source, malformed input or unsupported country; correct the input.
- HTTP 503 during generation: local converter/model unavailable. No package is approved by that failed attempt.
- `held`: dispatch validation failed; inspect the audit record and regenerate/review.
- `send_unknown`: a write might have succeeded. Inspect Mailpit using Message-ID; never automatically requeue it.
- Disk pressure: pause, stop nonessential optional services and inspect runtime storage. Do not delete database volumes to make a build succeed.

Generated orphan artifact directories from failed packages can be removed manually only after confirming their IDs are not referenced by the database. Automatic retention/deletion is not implemented yet.


## Conservative retention

`POST /v1/operations/retention` previews orphan artifact directories older than one day and raw company research snapshots older than 90 days. `?dry_run=false` applies that cleanup. Referenced original CVs/packages, citations/hashes and suppression records remain. The n8n maintenance workflow previews by default; it does not silently delete user data. Restic snapshots have independent retention and may retain locally deleted data.

## Cloud-specific setup

Managed cloud checkouts can have restrictive file modes. Make the PostgreSQL initialization script readable/executable (`chmod 755 infra/postgres/01-databases.sh`) before first startup. A partially initialized volume with missing application roles is not repaired by deleting user volumes: inspect roles/database state first and complete only demonstrably missing initialization steps. API/workspace Dockerfiles now make application files readable by their non-root users.

If the cloud HTTPS proxy uses a managed CA, supply its trusted CA bundle through an external build context and PIP_CERT; do not use trusted-host, disable TLS or change artifact hashes. Internal service names belong in NO_PROXY/no_proxy. This is implemented in the onboarding configuration, without storing certificates or secrets in Git.
