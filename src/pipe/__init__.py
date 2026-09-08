"""pipe — atomic, data-in/data-out operations for multilingual translation
and domain-expertise knowledge export.

One top-level package with two parts:
  * pipe.lib — the pure, dependency-free core ops (imported here for a flat
    public API: ``import pipe; pipe.echo("hi")``).
  * pipe.api — the optional serving adapter (FastAPI / Cloudflare Worker).
    NOT imported here, so the core stays dependency-free; import it explicitly
    (``from pipe.api.app import create_app``) with the ``[api]`` extra installed.
"""

from pipe.lib import Chain, Echo, EchoStream, Pipe, echo, echo_stream

__all__ = ["Pipe", "Chain", "Echo", "EchoStream", "echo", "echo_stream"]

__version__ = "0.1.0"
