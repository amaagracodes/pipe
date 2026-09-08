# syntax=docker/dockerfile:1

# --- build/runtime image for the pipe API on Cloud Run ---------------------
# Real CPython (not WASM), so any pure-Python or native dependency works —
# this is exactly what Cloudflare Workers could not offer.
FROM python:3.12-slim AS runtime

# Container hygiene + no bytecode files, unbuffered logs for Cloud Run.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first (better layer caching). All runtime deps
# (FastAPI + Jinja2 + uvicorn + DSPy) are declared in [project].dependencies,
# so a plain install pulls the whole stack — no optional extras to forget.
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install . uvicorn

# Static frontend served by the app (StaticFiles) at "/".
COPY public ./public
# Tell the app where the static site lives inside the image.
ENV PIPE_PUBLIC_DIR=/app/public

# Cloud Run sets $PORT (default 8080); the server entrypoint binds 0.0.0.0:$PORT.
ENV PORT=8080
EXPOSE 8080

# Drop root for runtime.
RUN useradd --create-home --uid 10001 appuser
USER appuser

CMD ["python", "-m", "pipe.api.server"]
