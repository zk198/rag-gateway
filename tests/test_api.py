from fastapi.testclient import TestClient
import httpx

from rag_gateway import api


def test_healthz():
    client = TestClient(api.app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_authenticates_and_injects_derived_context(monkeypatch):
    calls = []

    def fake_authenticate(request):
        assert request.headers["x-rag-tenant-id"] == "attacker-tenant"
        return "token-tenant", "token-user"

    async def fake_search(query, limit, tenant, user):
        calls.append((query, limit, tenant, user))
        return [{"text": "ok"}]

    monkeypatch.setattr(api, "authenticate", fake_authenticate)
    monkeypatch.setattr(api.service, "search", fake_search)

    client = TestClient(api.app)
    response = client.post(
        "/search",
        json={"query": "hello"},
        headers={"X-RAG-Tenant-ID": "attacker-tenant"},
    )

    assert response.status_code == 200
    assert response.json() == [{"text": "ok"}]
    assert calls == [("hello", 10, "token-tenant", "token-user")]


def test_upload_uses_ingestion_backend(monkeypatch):
    async def fake_upload(body, content_type, tenant, user):
        return httpx.Response(201, content=b"ok")

    monkeypatch.setattr(api, "authenticate", lambda request: ("t1", "u1"))
    monkeypatch.setattr(api.service, "upload", fake_upload)

    client = TestClient(api.app)
    response = client.post("/upload", content=b"data")
    assert response.status_code == 201
    assert response.text == "ok"


def test_user_read_routes_require_auth(monkeypatch):
    from fastapi import HTTPException

    def reject(request):
        raise HTTPException(status_code=401, detail="missing token")

    monkeypatch.setattr(api, "authenticate", reject)
    client = TestClient(api.app)
    assert client.get("/sources").status_code == 401


def test_mcp_only_exposes_llm_routes():
    from rag_gateway.mcp import mcp

    assert mcp is not None
