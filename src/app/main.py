from fastapi import FastAPI, HTTPException
from .core.logger import configure_logging
from .schemas import QueryRequest, QueryResponse
from .sqlgen import generate_sql
from .db import get_conn
from .summarizer import summarize

app = FastAPI(title="LLM Revenue Analyzer", version="0.1.0")

@app.on_event("startup")
async def _startup():
    configure_logging()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/v1/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    try:
        sql = await generate_sql(req.question)
        with get_conn() as conn:
            cur = conn.execute(sql)
            rows = [dict(r) for r in cur.fetchall()]
        summary = await summarize(req.question, rows)
        return QueryResponse(sql=sql, rows=rows, summary=summary)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
