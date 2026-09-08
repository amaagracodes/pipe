"""pipe.api — a thin, stateless serving layer over the pipe.lib core ops.

An *adapter*: it wires the atomic operations in ``pipe.lib`` to an HTTP surface
(FastAPI) suitable for running as a Cloudflare Python Worker. It owns no
business logic. Requires the ``[api]`` extra (fastapi, jinja2).
"""

from pipe.api.app import create_app

__all__ = ["create_app"]
