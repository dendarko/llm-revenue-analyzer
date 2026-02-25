from __future__ import annotations
import httpx
from .settings import settings
from .guardrails import basic_sql_safety

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

SQL_SYSTEM = """You are a senior analytics engineer. 
Generate ONE safe SQL SELECT query for SQLite for the user's question.
Use only these tables: invoices(id, account_id, amount, currency, invoice_date), subscriptions(id, account_id, mrr, start_date, end_date), accounts(id, name).
Return SQL only. No markdown."""

async def generate_sql(question: str) -> str:
    if settings.llm_provider != "openai":
        raise NotImplementedError("Only openai is wired in this template.")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role":"system","content":SQL_SYSTEM},{"role":"user","content":question}],
        "temperature": 0.0
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(OPENAI_CHAT_URL, json=payload, headers=headers)
        r.raise_for_status()
        sql = r.json()["choices"][0]["message"]["content"]
    return basic_sql_safety(sql)
