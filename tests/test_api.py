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

    async def fake_forward(url, request, tenant, user):
        calls.append((url, tenant, user, await request.body()))
        return httpx.Response(
            200,
            content=b'{"ok":true}',
            headers={"content-type": "application/json"},
        )

    monkeypatch.setattr(api, "authenticate", fake_authenticate)
    monkeypatch.setattr(api, "forward", fake_forward)

    client = TestClient(api.app)
    response = client.post(
        "/search",
        json={"query": "hello"},
        headers={"X-RAG-Tenant-ID": "attacker-tenant"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert calls == [
        (
            api.RETRIEVAL + "/search",
            "token-tenant",
            "token-user",
            b'{"query":"hello"}',
        )
    ]


def test_upload_uses_ingestion_backend(monkeypatch):
    calls = []

    monkeypatch.setattr(api, "authenticate", lambda request: ("t1", "u1"))

    async def fake_forward(url, request, tenant, user):
        calls.append((url, tenant, user))
        return httpx.Response(201, content=b"ok")

    monkeypatch.setattr(api, "forward", fake_forward)

    client = TestClient(api.app)
    response = client.post("/upload", content=b"data")

    assert response.status_code == 201
    assert calls == [(api.INGEST + "/upload", "t1", "u1")]


def test_forward_maps_downstream_timeout_to_504(monkeypatch):
    class TimeoutClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def request(self, *args, **kwargs):
            raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(api.httpx, "AsyncClient", lambda *a, **k: TimeoutClient())

    client = TestClient(api.app)
    response = client.post(
        "/search",
        json={"query": "hello"},
        headers={"Authorization": "Bearer token"},
    )

    assert response.status_code == 401
