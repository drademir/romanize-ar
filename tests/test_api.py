"""FastAPI endpoint tests."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "romanize-ar"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "disambiguator_loaded" in body


def test_romanize_get():
    r = client.get("/api/romanize", params={"text": "كتاب", "scheme": "ijmes", "use_disambig": False})
    assert r.status_code == 200
    body = r.json()
    assert body["input"] == "كتاب"
    assert body["scheme"] == "ijmes"
    assert body["output"]
    assert body["disambiguated"] is False


def test_romanize_post():
    r = client.post("/api/romanize", json={"text": "سلام", "scheme": "ala-lc", "use_disambig": False})
    assert r.status_code == 200
    assert r.json()["scheme"] == "ala-lc"


def test_romanize_empty_rejected():
    r = client.get("/api/romanize", params={"text": "   "})
    assert r.status_code == 400


def test_batch():
    r = client.post(
        "/api/romanize/batch",
        json={"items": ["كتاب", "سلام", "علم"], "scheme": "ijmes", "use_disambig": False},
    )
    assert r.status_code == 200
    assert len(r.json()["results"]) == 3


def test_invalid_scheme():
    r = client.get("/api/romanize", params={"text": "x", "scheme": "buckwalter"})
    assert r.status_code == 422  # pydantic Literal validation
