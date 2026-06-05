"""Test endpoint /api/health.

TestClient viene istanziato SENZA context-manager: in questo modo Starlette
NON esegue il lifespan (che si connetterebbe ad Atlas + seed). L'endpoint
/health non tocca il DB, quindi il test è isolato e offline.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_ok():
    client = TestClient(app)  # no `with` -> lifespan non eseguito
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "PlayerStock"
    assert body["version"].endswith("fase1")
