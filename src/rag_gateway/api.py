from fastapi import FastAPI, Request
from fastapi.responses import Response
import os
import httpx
from .auth import authenticate

app=FastAPI(title="RAG Gateway")
INGEST=os.getenv("RAG_INGESTION_URL","http://pst-agent:8000")
RETRIEVAL=os.getenv("RAG_RETRIEVAL_URL","http://rag-retrieval:8100")

async def forward(url, request, tenant, user):
    body=await request.body()
    headers={"content-type":request.headers.get("content-type","application/json"),"X-RAG-Tenant-ID":tenant,"X-RAG-User-ID":user}
    async with httpx.AsyncClient(timeout=300) as client:
        return await client.request(request.method,url,content=body,headers=headers)

def passthrough(response: httpx.Response) -> Response:
    return Response(content=response.content, status_code=response.status_code, media_type=response.headers.get("content-type"))

@app.get("/healthz")
async def healthz(): return {"status":"ok"}

@app.post("/search")
async def search(request: Request):
    tenant,user=authenticate(request)
    return passthrough(await forward(RETRIEVAL+"/search",request,tenant,user))

@app.post("/ingest")
async def ingest(request: Request):
    tenant,user=authenticate(request)
    return passthrough(await forward(INGEST+"/ingest",request,tenant,user))

@app.post("/upload")
async def upload(request: Request):
    tenant,user=authenticate(request)
    return passthrough(await forward(INGEST+"/upload",request,tenant,user))
