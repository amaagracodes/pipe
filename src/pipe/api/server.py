"""Production ASGI server entrypoint (container / Cloud Run).

Cloud Run injects the port to listen on via the ``PORT`` env var (default 8080)
and expects the process to bind 0.0.0.0. This module exposes the ASGI ``app``
for ``uvicorn pipe.api.server:app`` and a ``main()`` for direct execution.
"""

import os

import uvicorn

from pipe.api.app import create_app

app = create_app()


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(
        "pipe.api.server:app",
        host="0.0.0.0",
        port=port,
        log_level=os.environ.get("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
