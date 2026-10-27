"""The SQL functions and the Python functions must agree exactly."""
import unicodedata

import pytest

from jegede import fold, sort_string
from conftest import requires_db

pytestmark = requires_db

WORDS = [
    "iṣẹ́", "Ọ̀gbọ́n", "ẹja", "egbo", "gbogbo", "ga", "gan", "ọmọ́", "ọmọ",
    "ṢE", "se", "sun", "Ẹ̀kọ́", "olu", "tẹ", "te", "wàá", "yorùbá", "hello world",
    "a-b", "1 2 3", "ẹ̀bùn", "ÈGBÈ", "gbọ́n", "gẹ̀gẹ̀",
]


@pytest.fixture
def conn(db_url):
    from jegede.api import db

    with db.connect() as c:
        yield c


@pytest.mark.parametrize("word", WORDS)
@pytest.mark.parametrize("form", ["NFC", "NFD"])
def test_fold_and_sort_parity(conn, word, form):
    w = unicodedata.normalize(form, word)
    row = conn.execute(
        "SELECT jegede.fold(%s) AS f, jegede.sort_key(%s) AS s", (w, w)
    ).fetchone()
    assert row["f"] == fold(w)
    assert row["s"] == sort_string(w)


def test_sql_sort_order_matches_alphabet(conn):
    words = ["ọmọ", "olu", "ẹja", "egbo", "eba", "gan", "gbogbo", "ga", "ṣe", "se", "sun", "tẹ", "te"]
    rows = conn.execute(
        "SELECT w FROM unnest(%s::text[]) AS w ORDER BY jegede.sort_key(w) COLLATE \"C\"",
        (words,),
    ).fetchall()
    assert [r["w"] for r in rows] == [
        "eba", "egbo", "ẹja", "ga", "gan", "gbogbo",
        "olu", "ọmọ", "se", "sun", "ṣe", "te", "tẹ",
    ]
