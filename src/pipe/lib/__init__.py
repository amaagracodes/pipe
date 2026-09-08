"""pipe.lib — the pure, stateless core: atomic data-in/data-out operations.

Zero runtime dependencies. No I/O, no framework, no global state. Safe to run
anywhere Python does, including Cloudflare's Pyodide runtime.
"""

from typing import AsyncIterator

__all__ = ["echo", "echo_stream"]


def echo(data: str) -> str:
    """The first atomic op: data in, data out."""
    return data


async def echo_stream(data: str, *, chunk_size: int = 16) -> AsyncIterator[str]:
    """Async streaming op: yield `data` back in chunks.

    A stand-in for genuinely incremental ops (e.g. token-by-token translation).
    Lets the serving layer stream a response instead of buffering it whole.
    """
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]
