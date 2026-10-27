from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Path, Query
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from .. import __version__, to_words
from . import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.environ.get("JEGEDE_AUTO_MIGRATE", "1") != "0" and os.environ.get("DATABASE_URL"):
        db.migrate()
    yield


app = FastAPI(title="Jegede", version=__version__, description="Backend for Yoruba-language apps.", lifespan=lifespan)
COLUMNS = "id, kind, body, meta, created_at"


class EntryIn(BaseModel):
    kind: str = Field("entry", min_length=1, max_length=50)
    body: str = Field(..., min_length=1, max_length=10000)
    meta: Dict[str, Any] = Field(default_factory=dict)


class EntryOut(BaseModel):
    id: int
    kind: str
    body: str
    meta: Dict[str, Any]
    created_at: Any


@app.get("/health")
def health():
    try:
        with db.connect() as conn:
            conn.execute("SELECT 1")
    except Exception:
        raise HTTPException(503, "database unavailable")
    return {"status": "ok", "version": __version__}


@app.post("/entries", response_model=EntryOut, status_code=201)
def create_entry(entry: EntryIn):
    with db.connect() as conn:
        return conn.execute(
            f"INSERT INTO jegede.entries (kind, body, meta) VALUES (%s, %s, %s) RETURNING {COLUMNS}",
            (entry.kind, entry.body, Jsonb(entry.meta)),
        ).fetchone()


@app.get("/entries/{entry_id}", response_model=EntryOut)
def get_entry(entry_id: int):
    with db.connect() as conn:
        row = conn.execute(f"SELECT {COLUMNS} FROM jegede.entries WHERE id = %s", (entry_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "entry not found")
    return row


@app.get("/entries", response_model=List[EntryOut])
def list_entries(kind: Optional[str] = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    with db.connect() as conn:
        return conn.execute(
            f"SELECT {COLUMNS} FROM jegede.entries WHERE (%(kind)s::text IS NULL OR kind = %(kind)s) ORDER BY sort_key, id LIMIT %(limit)s OFFSET %(offset)s",
            {"kind": kind, "limit": limit, "offset": offset},
        ).fetchall()


@app.get("/search", response_model=List[EntryOut])
def search(q: str = Query(..., min_length=1, max_length=200), kind: Optional[str] = None, limit: int = Query(20, ge=1, le=100)):
    with db.connect() as conn:
        return conn.execute(
            f"""WITH q AS (SELECT jegede.fold(%(q)s) AS f, jegede.nfc(%(q)s) AS n)
                SELECT {COLUMNS} FROM jegede.entries e, q
                WHERE e.body_search LIKE '%%' || jegede.like_escape(q.f) || '%%'
                  AND (%(kind)s::text IS NULL OR e.kind = %(kind)s)
                ORDER BY (e.body = q.n) DESC, (e.body_search = q.f) DESC,
                         (e.body_search LIKE jegede.like_escape(q.f) || '%%') DESC,
                         e.sort_key, e.id LIMIT %(limit)s""",
            {"q": q, "kind": kind, "limit": limit},
        ).fetchall()


@app.get("/numbers/{n}")
def number_words(n: int = Path(..., ge=0, le=100), tones: bool = True):
    return {"number": n, "words": to_words(n, tones=tones)}
