from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    sql: str
    rows: list[dict]
    summary: str
