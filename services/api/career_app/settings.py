from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./career.db"
    api_key: SecretStr = Field(min_length=32)
    artifact_dir: Path = Path("./artifacts")
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "qwen3:8b"
    gotenberg_url: str = "http://gotenberg:3000"
    mail_transport: str = "mailpit"
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    mail_from: str = "candidate@example.test"
    max_upload_bytes: int = 10 * 1024 * 1024
    gmail_client_id: str = ""
    gmail_client_secret: SecretStr = SecretStr("")
    gmail_redirect_uri: str = "http://localhost:8000/oauth/gmail/callback"
    gmail_live_enabled: bool = False
    searxng_url: str = "http://searxng:8080"
