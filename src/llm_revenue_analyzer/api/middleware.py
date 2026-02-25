from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from llm_revenue_analyzer.core.logging import set_request_id


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    set_request_id(request_id)
    request.state.request_id = request_id
    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    set_request_id(None)
    return response
