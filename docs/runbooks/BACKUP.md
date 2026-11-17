# Encrypted checkpoints and restore

Install the free restic CLI on the host. Put its password in a protected file outside the repository. Use an existing independent disk as the repository destination.

```powershell
python scripts/backup.py --repository E:\CareerBackups --password-file C:\Private\restic-password.txt --init
```

Omit `--init` on later runs. Schedule the command with Windows Task Scheduler if daily backups are desired. PostgreSQL must be running; API/n8n containers must have been created. The script stops running writers, dumps career/n8n, copies artifacts and n8n state, encrypts with restic, and restarts only the writers that were previously running. It never prints credentials. Temporary local copies and Docker volume storage are plaintext until encrypted; protect the host disk.

Restore into an isolated local copy first:

1. Run `restic --repo <repo> --password-file <file> snapshots` and select the exact snapshot.
2. Restore using `restic ... restore <snapshot> --target <private-directory>`. It contains `career.dump`, `n8n.dump`, `artifacts`, `n8n_state` and `recovery.env` under the backed-up temporary directory path.
3. Stop api/workspace/n8n. Preserve a checkpoint of current data before replacing it. Restore matching recovery credentials; do not combine encrypted tokens with a different API key or n8n encryption key.
4. Copy dumps into postgres, then use `pg_restore -U career --clean --if-exists -d career /tmp/career.dump` and the corresponding n8n role/database. Restore the artifact and n8n-state directory contents using `docker compose cp`; retain ownership expected by each container.
5. Set `GMAIL_LIVE_ENABLED=false` before starting. Apply migrations, inspect document hashes, connect Gmail, synchronize/reconcile send attempts, then explicitly enable the reviewed campaign again.
6. Check `restic ... check` periodically. Test restore monthly; a successful backup command alone is not evidence that restoration works.

Independent storage and the restic password are user-supplied prerequisites. This development environment has neither, so no encrypted backup/restore drill is claimed. Old snapshots retain deleted data until retention/prune is applied deliberately with restic.
