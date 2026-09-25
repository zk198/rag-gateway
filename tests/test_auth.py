import jwt
import pytest
from fastapi import HTTPException

from rag_gateway.auth import authenticate_token


def test_authenticate_token_requires_identity_claims(monkeypatch):
    monkeypatch.setenv("RAG_JWT_SECRET", "secret")
    token = jwt.encode({"sub": "u1"}, "secret", algorithm="HS256")
    with pytest.raises(HTTPException) as exc:
        authenticate_token(token)
    assert exc.value.status_code == 403


def test_authenticate_token_accepts_tenant_and_subject(monkeypatch):
    monkeypatch.setenv("RAG_JWT_SECRET", "secret")
    token = jwt.encode({"sub": "u1", "tenant_id": "t1"}, "secret", algorithm="HS256")
    assert authenticate_token(token) == ("t1", "u1")
