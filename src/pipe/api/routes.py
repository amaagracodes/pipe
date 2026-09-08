"""HTTP route handlers.

Each handler is thin and async: parse input, call a ``pipe.lib`` atomic op,
return output. Three response styles coexist:

  * JSON ops        — /echo (buffered)
  * streaming ops   — /echo/stream (incremental data stream)
  * server-rendered — /status (Jinja2 template, for API-driven dynamic pages)

The static frontend (public/) is mounted last at "/" so API routes and /docs
take priority; index.html is served at "/".
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

import pipe
from pipe.api.app import PUBLIC_DIR, TEMPLATES


def register_routes(app: FastAPI) -> None:
    @app.get("/echo", tags=["ops"])
    async def echo(data: str = "") -> dict:
        """Echo atomic op: returns the input unchanged (data in, data out)."""
        return {"data": pipe.echo(data)}

    @app.get("/echo/stream", tags=["ops"])
    async def echo_stream(data: str = "", chunk_size: int = 16) -> StreamingResponse:
        """Streaming echo: sends the input back incrementally as a data stream."""
        return StreamingResponse(
            pipe.echo_stream(data, chunk_size=chunk_size),
            media_type="text/plain; charset=utf-8",
        )

    @app.get("/status", response_class=HTMLResponse, include_in_schema=False)
    async def status(request: Request, data: str = "pong"):
        """Server-rendered (Jinja2) page — kept for dynamic, API-driven sites."""
        return TEMPLATES.TemplateResponse(
            request,
            "status.html",
            {
                "version": pipe.__version__,
                "echoed": pipe.echo(data),
                "ops": ["echo", "echo_stream"],
            },
        )

    # Static frontend, mounted LAST so the API routes above (and /docs,
    # /openapi.json) match first. html=True serves index.html at "/". The
    # public/ directory ships in the container image (and exists in local dev).
    # The is_dir guard just keeps the app importable in environments where the
    # directory isn't present (e.g. running the ops library without the site).
    if PUBLIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")
