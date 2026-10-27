from __future__ import annotations

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL, e.g. postgresql://user:pass@host/dbname")
    return url


def connect() -> psycopg.Connection:
    return psycopg.connect(database_url(), row_factory=dict_row)


def migrate() -> None:
    sql_path = Path(__file__).resolve().parents[3] / "001_init.sql"
    with connect() as conn:
        conn.execute(sql_path.read_text(encoding="utf-8"))
