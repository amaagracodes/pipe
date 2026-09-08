"""FastAPI application factory.

Builds the app and mounts routes. Two frontend paths coexist by design:

  * Static assets (``public/``) — the landing page and any purely-static files.
    On Cloudflare these are served via the Workers ASSETS binding; locally via
    Starlette's StaticFiles. Best for content with no per-request data.

  * Jinja2 templates (``pipe/api/templates/``) — for API-driven, server-rendered
    pages that DO need per-request/dynamic data. Kept for API-based sites.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

import pipe

_BASE_DIR = Path(__file__).resolve().parent
# The static frontend directory. Priced from an env var first (set in the
# container image to /app/public), falling back to the repo layout for local
# dev (src/pipe/api/app.py -> repo root is 4 levels up). When the package is
# pip-installed the repo-relative guess won't exist, which is why the container
# sets PIPE_PUBLIC_DIR explicitly.
PUBLIC_DIR = Path(
    os.environ.get("PIPE_PUBLIC_DIR", str(Path(__file__).resolve().parents[3] / "public"))
)
# Server-side templates for dynamic, API-driven pages.
TEMPLATES = Jinja2Templates(directory=str(_BASE_DIR / "templates"))


def create_app() -> FastAPI:
    # When served behind a reverse proxy under a path prefix (e.g.
    # /proxy/8787), set PIPE_ROOT_PATH to that prefix so FastAPI generates the
    # correct URLs for /docs, /openapi.json, etc. Empty (default) = served at
    # the domain root, as on Cloudflare Workers.
    root_path = os.environ.get("PIPE_ROOT_PATH", "")

    app = FastAPI(
        title="pipe-broker",
        version=pipe.__version__,
        description=(
            "Atomic, data-in/data-out operations for multilingual translation "
            "and domain-expertise knowledge export."
        ),
        root_path=root_path,
    )

    # Routes are registered separately to keep concerns split.
    from pipe.api.routes import register_routes

    register_routes(app)
    return app
