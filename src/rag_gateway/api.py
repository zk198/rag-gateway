from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .auth import authenticate
from .models import GatewaySettings, SearchRequest
from .service import RAGService

settings = GatewaySettings(
    retrieval_url=os.getenv("RAG_RETRIEVAL_URL", "http://rag-retrieval:8100"),
    ingestion_url=os.getenv("RAG_INGESTION_URL", "http://pst-agent:8000"),
    timeout_seconds=float(os.getenv("RAG_DOWNSTREAM_TIMEOUT_SECONDS", "60")),
)
service = RAGService(settings)

app = FastAPI(title="RAG Gateway", version="0.2.0")

UI_ORIGINS = [
    origin.strip()
    for origin in os.getenv("RAG_UI_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=UI_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def downstream_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TimeoutError):
        return HTTPException(504, "downstream timeout")
    if isinstance(exc, ConnectionError):
        return HTTPException(502, "downstream unavailable")
    return HTTPException(502, "downstream request failed")


@app.get("/healthz", tags=["internal"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/search", operation_id="search_knowledge", tags=["llm"])
async def search(request: SearchRequest, http_request: Request) -> list[dict]:
    tenant, user = authenticate(http_request)
    try:
        return await service.search(request.query, request.limit, tenant, user)
    except Exception as exc:
        raise downstream_error(exc) from exc


@app.get("/sources", operation_id="list_sources", tags=["llm"])
async def sources(request: Request) -> list[dict]:
    tenant, user = authenticate(request)
    try:
        return await service.get_sources(tenant, user)
    except Exception as exc:
        raise downstream_error(exc) from exc


@app.get("/sources/{source_name}", tags=["internal"])
async def source(request: Request, source_name: str) -> dict:
    tenant, user = authenticate(request)
    try:
        return await service.get_source(source_name, tenant, user)
    except Exception as exc:
        raise downstream_error(exc) from exc


@app.get("/stats", tags=["internal"])
async def stats(request: Request) -> dict:
    tenant, user = authenticate(request)
    try:
        return await service.get_stats(tenant, user)
    except Exception as exc:
        raise downstream_error(exc) from exc


@app.get("/messages/{message_id}", operation_id="get_message", tags=["llm"])
async def message(request: Request, message_id: str) -> dict:
    tenant, user = authenticate(request)
    try:
        return await service.get_message(message_id, tenant, user)
    except Exception as exc:
        raise downstream_error(exc) from exc


@app.get("/documents/{document_id}", operation_id="get_document", tags=["llm"])
async def document(request: Request, document_id: str) -> dict:
    tenant, user = authenticate(request)
    try:
        return await service.get_document(document_id, tenant, user)
    except Exception as exc:
        raise downstream_error(exc) from exc


@app.post("/ingest", tags=["internal"])
async def ingest(request: Request) -> Response:
    tenant, user = authenticate(request)
    response = await service.ingest(
        await request.body(),
        request.headers.get("content-type", "application/json"),
        tenant,
        user,
    )
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )


@app.post("/upload", tags=["internal"])
async def upload(request: Request) -> Response:
    tenant, user = authenticate(request)
    response = await service.upload(
        await request.body(),
        request.headers.get("content-type", "application/octet-stream"),
        tenant,
        user,
    )
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )
