import os

import pytest

TEST_DB = os.environ.get("JEGEDE_TEST_DATABASE_URL")

requires_db = pytest.mark.skipif(
    not TEST_DB, reason="set JEGEDE_TEST_DATABASE_URL to run database tests"
)


@pytest.fixture
def db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", TEST_DB)
    from jegede.api import db

    db.migrate()
    with db.connect() as conn:
        conn.execute("TRUNCATE jegede.entries RESTART IDENTITY")
    return TEST_DB
