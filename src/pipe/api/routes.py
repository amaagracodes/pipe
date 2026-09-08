"""HTTP route handlers.

Each handler is thin and async: parse input, call a ``pipe.lib`` atomic op,
return output. Three response styles coexist:

  * JSON ops        — /echo (buffered)
  * streaming ops   — /echo/stream (incremental data stream)
  * server-rendered — /status (Jinja2 template, for API-driven dynamic pages)

The static frontend (public/) is mounted last at "/" so API routes and /docs
take priority; index.html is served at "/".
"""

from fastapi import FastAPI, Request, UploadFile
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

    # --- LLM (OpenRouter) -------------------------------------------------

    @app.post("/llm", tags=["llm"])
    async def llm(prompt: str, model: str = "openai/gpt-4o-mini", max_tokens: int = 256) -> dict:
        """Test route: send a prompt to OpenRouter and return the completion.

        Reads the key from $OPENROUTER_API_KEY (injected in the deployment).
        Returns a 4xx-shaped JSON error rather than a 500 when the LLM stack or
        key is unavailable, so it's safe to probe.
        """
        from fastapi import HTTPException

        from pipe.lib.providers import OpenRouterProvider

        provider = OpenRouterProvider(model=model, max_tokens=max_tokens)
        try:
            text = await provider.acall(prompt)
        except ModuleNotFoundError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        except RuntimeError as exc:  # missing key
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:  # upstream/LLM error — don't leak internals
            raise HTTPException(status_code=502, detail=f"LLM call failed: {type(exc).__name__}") from exc
        return {"model": provider.model, "prompt": prompt, "completion": text}

    # --- legal atomic ops -------------------------------------------------

    @app.get("/legal/ops", tags=["legal"])
    async def legal_ops() -> dict:
        """List the available atomic legal operations and rule categories."""
        from pipe.lib.experts import legal

        return {
            "operations": [
                "detect_pii", "spot_clauses", "identify_statutes",
                "extract_citations", "screen_privilege",
            ],
            "categories": sorted(legal.categories()),
            "rule_count": len(legal.RULES),
        }

    @app.post("/legal/detect", tags=["legal"])
    async def legal_detect(text: str, jurisdiction: str = "us", op: str = "detect_pii") -> dict:
        """Run one atomic legal op over text for a given jurisdiction.

        ``op`` is one of the names from ``GET /legal/ops``; ``jurisdiction`` is a
        hierarchical code like ``us``, ``us/ny``, ``in/mh`` (optionally with
        facets appended later). Returns the detections found.
        """
        from fastapi import HTTPException

        from pipe.lib.experts.legal import (
            DetectPII, ExtractCitations, IdentifyStatutes, ScreenPrivilege, SpotClauses,
        )

        ops = {
            "detect_pii": DetectPII,
            "spot_clauses": SpotClauses,
            "identify_statutes": IdentifyStatutes,
            "extract_citations": ExtractCitations,
            "screen_privilege": ScreenPrivilege,
        }
        op_cls = ops.get(op)
        if op_cls is None:
            raise HTTPException(status_code=400, detail=f"unknown op {op!r}; choose from {sorted(ops)}")
        result = op_cls(jurisdiction)(text)
        return {
            "op": op,
            "jurisdiction": jurisdiction,
            "detections": [
                {
                    "kind": d.kind,
                    "label": d.label,
                    "severity": d.severity.name,
                    "span": [d.span.start, d.span.end] if d.span else None,
                }
                for d in result.detections
            ],
            "meta": result.document.meta,
        }

    # --- speech-to-text (OpenRouter) --------------------------------------

    @app.post("/stt", tags=["llm"])
    async def stt(
        file: UploadFile,
        model: str = "openai/whisper-large-v3",
        language: str | None = None,
    ) -> dict:
        """Transcribe an uploaded audio file to text (audio bytes in, text out).

        Accepts a multipart file upload; the audio format is inferred from the
        filename extension (falls back to ``wav``). Reads the key from
        $OPENROUTER_API_KEY. Errors map like /llm (503 missing key, 502 upstream).
        """
        from fastapi import HTTPException

        from pipe.lib.providers import STT

        audio = await file.read()
        # Derive the container format from the upload's extension.
        fmt = "wav"
        if file.filename and "." in file.filename:
            fmt = file.filename.rsplit(".", 1)[-1].lower()

        provider = STT(model=model, language=language)
        try:
            text = await provider.acall(audio, format=fmt)
        except RuntimeError as exc:  # missing key
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:  # upstream/transcription error — don't leak internals
            raise HTTPException(status_code=502, detail=f"STT call failed: {type(exc).__name__}") from exc
        return {"model": provider.model, "format": fmt, "text": text}

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
