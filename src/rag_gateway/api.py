from fastapi import FastAPI, Request
import os
import httpx
from .auth import authenticate

app=FastAPI(title="RAG Gateway")
INGEST=os.getenv("RAG_INGESTION_URL","http://rag-ingestion:8000")
RETRIEVAL=os.getenv("RAG_RETRIEVAL_URL","http://rag-retrieval:8100")

async def forward(url, request, tenant, user):
    body=await request.body()
    headers={"content-type":request.headers.get("content-type","application/json"),"X-RAG-Tenant-ID":tenant,"X-RAG-User-ID":user}
    async with httpx.AsyncClient(timeout=300) as client:
        response=await client.request(request.method,url,content=body,headers=headers)
    response.raise_for_status()
    return response

@app.get("/healthz")
async def healthz(): return {"status":"ok"}

@app.post("/search")
async def search(request: Request):
    tenant,user=authenticate(request)
    response=await forward(RETRIEVAL+"/search",request,tenant,user)
    return response.json()

@app.post("/ingest")
async def ingest(request: Request):
    tenant,user=authenticate(request)
    response=await forward(INGEST+"/ingest",request,tenant,user)
    return response.json()

@app.post("/upload")
async def upload(request: Request):
    tenant,user=authenticate(request)
    response=await forward(INGEST+"/upload",request,tenant,user)
    return response.json()
