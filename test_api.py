import unicodedata

import pytest
from fastapi.testclient import TestClient

from conftest import requires_db

pytestmark = requires_db


@pytest.fixture
def client(db_url):
    from jegede.api.app import app

    with TestClient(app) as c:
        yield c


def add(client, body, kind="word", **meta):
    r = client.post("/entries", json={"kind": kind, "body": body, "meta": meta})
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_stored_text_is_nfc(client):
    nfd = unicodedata.normalize("NFD", "iṣẹ́")
    e = add(client, nfd)
    assert e["body"] == unicodedata.normalize("NFC", "iṣẹ́")
    assert client.get(f"/entries/{e['id']}").json()["body"] == e["body"]


def test_search_ignores_diacritics_and_case(client):
    add(client, "iṣẹ́")
    add(client, "isu")
    assert [e["body"] for e in client.get("/search", params={"q": "ISE"}).json()] == ["iṣẹ́"]
    assert [e["body"] for e in client.get("/search", params={"q": "iṣẹ"}).json()] == ["iṣẹ́"]


def test_search_ranks_exact_accents_first(client):
    add(client, "ise")
    add(client, "iṣe")
    add(client, "iṣẹ́")
    got = [e["body"] for e in client.get("/search", params={"q": "iṣẹ́"}).json()]
    assert got[0] == "iṣẹ́"
    assert set(got) == {"ise", "iṣe", "iṣẹ́"}


def test_search_prefix_beats_substring(client):
    add(client, "bọ̀ọ̀lù")
    add(client, "ọ̀bọ̀")
    got = [e["body"] for e in client.get("/search", params={"q": "bo"}).json()]
    assert got[0] == "bọ̀ọ̀lù"


def test_search_wildcards_are_literal(client):
    add(client, "ọmọ")
    assert client.get("/search", params={"q": "%"}).json() == []
    assert client.get("/search", params={"q": "_"}).json() == []


def test_list_is_in_yoruba_order(client):
    for w in ["ṣe", "se", "gbogbo", "ga", "ẹja", "eba", "tẹ", "te"]:
        add(client, w)
    got = [e["body"] for e in client.get("/entries").json()]
    assert got == ["eba", "ẹja", "ga", "gbogbo", "se", "ṣe", "te", "tẹ"]


def test_kind_filter_and_pagination(client):
    add(client, "a", kind="x")
    add(client, "b", kind="y")
    add(client, "d", kind="x")
    assert [e["body"] for e in client.get("/entries", params={"kind": "x"}).json()] == ["a", "d"]
    assert len(client.get("/entries", params={"limit": 1, "offset": 1}).json()) == 1


def test_meta_roundtrip_and_404(client):
    e = add(client, "ọmọ", meaning="child", tags=["noun"])
    assert client.get(f"/entries/{e['id']}").json()["meta"] == {"meaning": "child", "tags": ["noun"]}
    assert client.get("/entries/9999").status_code == 404


def test_validation(client):
    assert client.post("/entries", json={"body": ""}).status_code == 422
    assert client.get("/search").status_code == 422


def test_numbers_endpoint(client):
    assert client.get("/numbers/21").json() == {"number": 21, "words": "ọ̀kanlélógún"}
    assert client.get("/numbers/21", params={"tones": "false"}).json()["words"] == "okanlelogun"
    assert client.get("/numbers/101").status_code == 422
