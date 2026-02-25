from __future__ import annotations

import uvicorn

from llm_revenue_analyzer.core.settings import get_settings


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "llm_revenue_analyzer.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        factory=False,
    )


if __name__ == "__main__":
    run()
