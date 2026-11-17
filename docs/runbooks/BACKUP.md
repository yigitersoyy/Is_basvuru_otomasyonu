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


## Automated isolated restore verification

New checkpoints include a SHA-256 manifest for database dumps, artifacts, n8n state and recovery configuration. After a checkpoint:

```powershell
python scripts/restore.py --repository E:\CareerBackups --password-file C:\Private\restic-password.txt --snapshot EXACT_SNAPSHOT_ID --target C:\Private\restore-drill
```

Use an empty protected target. The tool checks restic integrity, restores only the checkpoint subtree, verifies every manifest hash, restores both dumps into uniquely named temporary PostgreSQL databases and checks all package artifact hashes against the restored career database. It drops only those temporary databases afterward. It never replaces production databases or starts a sender. Restored files contain plaintext recovery keys; protect/remove the drill target when no longer needed.

This verification passed in the cloud using synthetic data and an encrypted restic repository on the same cloud disk. It proves the tested restore path, not independent-drive disaster recovery or Windows filesystem behavior. Provision independent storage locally before relying on backups.

During the production restore procedure above, set live sending off, persist the global pause and hold all restored pending messages for Gmail reconciliation before any resume. Never treat an old `queued` row as authorization to resend after restoring an older snapshot. Run the independent checkpoint before replacing current data.
