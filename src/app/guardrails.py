from __future__ import annotations
import re

ALLOWED_TABLES = {"invoices", "subscriptions", "accounts"}

def basic_sql_safety(sql: str) -> str:
    sql_clean = sql.strip().rstrip(";")
    if re.search(r"\b(drop|delete|truncate|alter|update|insert)\b", sql_clean, re.I):
        raise ValueError("Write operations are not allowed.")
    if not re.search(r"\bselect\b", sql_clean, re.I):
        raise ValueError("Only SELECT queries are allowed.")
    # naive table allowlist
    for m in re.finditer(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)\b", sql_clean, re.I):
        if m.group(1).lower() not in ALLOWED_TABLES:
            raise ValueError(f"Table not allowed: {m.group(1)}")
    return sql_clean
