from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    artifacts_dir: Path = Path("ml/artifacts")
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://your-vercel-domain.vercel.app",
    ]
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
