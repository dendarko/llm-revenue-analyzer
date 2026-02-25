from __future__ import annotations
import sqlite3
from urllib.parse import urlparse
from .settings import settings

def _sqlite_path(url: str) -> str:
    # sqlite:///./demo.db
    u = urlparse(url)
    return u.path.lstrip("/") if u.path else "demo.db"

def get_conn() -> sqlite3.Connection:
    if not settings.database_url.startswith("sqlite"):
        raise NotImplementedError("This template includes SQLite only. Extend for Postgres/MySQL.")
    path = _sqlite_path(settings.database_url)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn
