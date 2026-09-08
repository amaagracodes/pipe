"""Local development server.

Runs the exact same FastAPI app as the Cloudflare Worker, but via uvicorn so
it can be tested locally without the Workers/Pyodide runtime.

    uv run --extra api --with uvicorn python -m pipe.api.dev

Binds 0.0.0.0 by default so it is reachable on localhost, LAN, and tailnet.
Override with PIPE_HOST / PIPE_PORT.
"""

import os

import uvicorn

from pipe.api.app import create_app

app = create_app()


def main() -> None:
    host = os.environ.get("PIPE_HOST", "0.0.0.0")
    port = int(os.environ.get("PIPE_PORT", "8787"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
