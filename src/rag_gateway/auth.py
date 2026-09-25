from __future__ import annotations
import os
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Request

def authenticate(request: Request) -> tuple[str, str | None]:
    header=request.headers.get("Authorization","")
    if not header.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    token=header[7:]
    secret=os.getenv("RAG_JWT_SECRET")
    jwks=os.getenv("RAG_JWKS_URL")
    algorithms=os.getenv("RAG_JWT_ALGORITHMS","RS256").split(",")
    try:
        if secret:
            claims=jwt.decode(token, secret, algorithms=algorithms, options={"verify_aud": False})
        elif jwks:
            key=PyJWKClient(jwks).get_signing_key_from_jwt(token).key
            claims=jwt.decode(token, key, algorithms=algorithms, options={"verify_aud": False})
        else:
            raise HTTPException(500, "JWT verifier is not configured")
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "invalid token") from exc
    tenant=claims.get("tenant_id") or claims.get("tid")
    user=claims.get("sub")
    if not tenant or not user:
        raise HTTPException(403, "token must contain tenant_id and sub")
    return str(tenant), str(user)
