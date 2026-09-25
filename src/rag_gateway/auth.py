from __future__ import annotations

import os

import jwt
from fastapi import HTTPException, Request
from jwt import PyJWKClient


def authenticate_token(token: str) -> tuple[str, str]:
    secret = os.getenv("RAG_JWT_SECRET")
    jwks = os.getenv("RAG_JWKS_URL")
    algorithms = [
        value.strip()
        for value in os.getenv(
            "RAG_JWT_ALGORITHMS", "HS256" if secret else "RS256"
        ).split(",")
        if value.strip()
    ]
    issuer = os.getenv("RAG_JWT_ISSUER")
    audience = os.getenv("RAG_JWT_AUDIENCE")

    if not algorithms:
        raise HTTPException(500, "JWT algorithms are not configured")

    try:
        if secret:
            claims = jwt.decode(
                token, secret, algorithms=algorithms, issuer=issuer, audience=audience,
                options={"verify_iss": issuer is not None, "verify_aud": audience is not None},
            )
        elif jwks:
            key = PyJWKClient(jwks).get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token, key, algorithms=algorithms, issuer=issuer, audience=audience,
                options={"verify_iss": issuer is not None, "verify_aud": audience is not None},
            )
        else:
            raise HTTPException(500, "JWT verifier is not configured")
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "invalid token") from exc

    tenant = claims.get("tenant_id") or claims.get("tid")
    user = claims.get("sub")
    if not tenant or not user:
        raise HTTPException(403, "token must contain tenant_id and sub")
    return str(tenant), str(user)


def authenticate(request: Request) -> tuple[str, str]:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or not header[7:].strip():
        raise HTTPException(401, "Bearer token required")
    return authenticate_token(header[7:].strip())
