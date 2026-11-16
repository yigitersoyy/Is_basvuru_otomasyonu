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

Automated encrypted backup/restore is a later milestone. Until it exists, avoid storing the only copy of important material in this increment. For a controlled local checkpoint:

1. Stop `api` and `n8n` to quiesce writes. If Appsmith is enabled, stop it too.
2. Make a PostgreSQL dump of both `career` and `n8n` using `pg_dump -Fc` inside `postgres`. Store byte output using a binary-safe tool; Windows PowerShell 5 redirection can corrupt binary output. A safe approach is `docker compose exec -T postgres pg_dump -U career -Fc -f /tmp/career.dump career`, followed by `docker compose cp postgres:/tmp/career.dump <private-backup-directory>`; repeat using the n8n role/database.
3. Copy the stopped API artifact directory and n8n's entire persistent state with `docker compose cp`. Include the `.env` recovery keys in a protected backup location. If Appsmith is used, follow its version-specific supported backup procedure; database dumps alone do not back up its application state.
4. Encrypt the checkpoint using an existing trusted local encryption tool and store it on independent storage. A plain dump on the same drive is not the architecture's encrypted independent backup.
5. Resume the services and test their health. Keep an upgrade checkpoint until the upgraded state is verified.

For restore, start in paused test mode, restore the matching database/artifact/key versions, and verify hashes before resuming. When Gmail support is later introduced, provider reconciliation must occur before outbound work resumes; the current release has no Gmail restore reconciliation.

## Failure states

- HTTP 401: wrong/missing local API key.
- HTTP 409: stale approval, conflicting sequence, changed artifact/profile, unconfirmed contact or suppression. Read the returned explanation.
- HTTP 422: invalid source, malformed input or unsupported country; correct the input.
- HTTP 503 during generation: local converter/model unavailable. No package is approved by that failed attempt.
- `held`: dispatch validation failed; inspect the audit record and regenerate/review.
- `send_unknown`: a write might have succeeded. Inspect Mailpit using Message-ID; never automatically requeue it.
- Disk pressure: pause, stop nonessential optional services and inspect runtime storage. Do not delete database volumes to make a build succeed.

Generated orphan artifact directories from failed packages can be removed manually only after confirming their IDs are not referenced by the database. Automatic retention/deletion is not implemented yet.
