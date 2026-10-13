import os
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.config import BACKEND_ROOT


def upgrade_database(url: str) -> None:
    os.environ["DATABASE_URL"] = url
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")


def backend_root() -> Path:
    return BACKEND_ROOT
