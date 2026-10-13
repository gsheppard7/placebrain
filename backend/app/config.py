from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./placebrain.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    seed_on_startup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def resolve_database_url(url: str) -> str:
    """Anchor relative SQLite paths at the backend directory."""
    prefix = "sqlite:///./"
    if url.startswith(prefix):
        path = (BACKEND_ROOT / url.removeprefix(prefix)).resolve()
        return "sqlite:///" + str(path)
    return url
