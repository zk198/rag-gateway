from fastapi.testclient import TestClient

from rag_gateway import api


def test_rag_ui_read_contract(monkeypatch):
    monkeypatch.setattr(api, "authenticate", lambda request: ("t1", "u1"))
    async def sources(*args):
        return [{"source_name": "mail"}]

    async def stats(*args):
        return {"documents": 3}

    async def message(*args):
        return {"id": "m1", "subject": "Hello"}

    async def document(*args):
        return {"id": "d1", "title": "Doc"}

    monkeypatch.setattr(api.service, "get_sources", sources)
    monkeypatch.setattr(api.service, "get_stats", stats)
    monkeypatch.setattr(api.service, "get_message", message)
    monkeypatch.setattr(api.service, "get_document", document)

    client = TestClient(api.app)

    assert client.get("/sources").json() == [{"source_name": "mail"}]
    assert client.get("/stats").json() == {"documents": 3}
    assert client.get("/messages/m1").json()["subject"] == "Hello"
    assert client.get("/documents/d1").json()["title"] == "Doc"


def test_rag_ui_upload_contract(monkeypatch):
    class Response:
        status_code = 201
        content = b'{"status":"accepted"}'
        headers = {"content-type": "application/json"}

    async def fake_upload(body, content_type, tenant, user):
        assert body
        assert content_type.startswith("multipart/form-data;")
        assert (tenant, user) == ("t1", "u1")
        return Response()

    monkeypatch.setattr(api, "authenticate", lambda request: ("t1", "u1"))
    monkeypatch.setattr(api.service, "upload", fake_upload)

    client = TestClient(api.app)
    response = client.post(
        "/upload",
        files={"file": ("test.txt", b"hello", "text/plain")},
        data={"source_name": "mail"},
    )

    assert response.status_code == 201
    assert response.json() == {"status": "accepted"}
