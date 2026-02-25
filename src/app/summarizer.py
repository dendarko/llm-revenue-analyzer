import json
from __future__ import annotations
import httpx
from .settings import settings

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"

async def summarize(question: str, rows: list[dict]) -> str:
    if settings.llm_provider != "openai":
        raise NotImplementedError("Only openai is wired in this template.")
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required.")

    system = "Summarize the tabular results clearly for a business audience. Use bullets and key numbers."
    user = {"question": question, "rows": rows[:50]}  # cap
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role":"system","content":system},{"role":"user","content":json.dumps(user)}],
        "temperature": 0.2
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(OPENAI_CHAT_URL, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
