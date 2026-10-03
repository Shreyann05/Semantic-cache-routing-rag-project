from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from app.service import RAGService
app=FastAPI(title="Semantic Cache RAG")
service=RAGService()
class Query(BaseModel): query:str=Field(min_length=1,max_length=2000)
@app.get("/health")
def health(): return {"status":"ok"}
@app.post("/query")
def query(body:Query):
 if not body.query.strip():raise HTTPException(422,"query cannot be blank")
 try:return service.query(body.query)
 except RuntimeError as exc: raise HTTPException(503,"LLM service unavailable") from exc
@app.get("/metrics")
def metrics():return service.metrics.summary()
@app.get("/evaluation")
def evaluation():
 from pathlib import Path
 import json
 p=Path("data/runtime/benchmark.json"); return json.loads(p.read_text()) if p.exists() else {"detail":"Run scripts/benchmark.py first"}
