"""Generate local secrets once; never overwrite an existing .env."""

import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if path.exists():
    raise SystemExit(".env already exists; preserved without modification")
keys = ["POSTGRES_PASSWORD", "CAREER_DB_PASSWORD", "N8N_DB_PASSWORD", "API_KEY", "N8N_ENCRYPTION_KEY"]
values = {key: secrets.token_hex(32) for key in keys}
values.update(MAIL_TRANSPORT="mailpit", MAIL_FROM="candidate@example.test", OLLAMA_MODEL="qwen3:8b")
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as f:
    f.write("\n".join(f"{k}={v}" for k, v in values.items()) + "\n")
print("Created protected .env. Values are not printed. Keep it out of Git.")
