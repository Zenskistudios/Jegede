from __future__ import annotations

import os
from importlib import resources

import psycopg
from psycopg.rows import dict_row


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL, e.g. postgresql://user:pass@host/dbname")
    return url


def connect() -> psycopg.Connection:
    # One connection per request: simple and fine for v0.1.
    # TODO: switch to psycopg_pool for production load.
    return psycopg.connect(database_url(), row_factory=dict_row)


def migrate() -> None:
    sql = resources.files("jegede").joinpath("sql/001_init.sql").read_text(encoding="utf-8")
    with connect() as conn:
        conn.execute(sql)
