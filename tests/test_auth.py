from fastapi import HTTPException
from starlette.requests import Request

from rag_gateway.auth import authenticate


def test_missing_bearer_is_rejected():
    request = Request({"type": "http", "headers": []})
    try:
        authenticate(request)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("authentication should fail")
