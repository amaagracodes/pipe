"""pipe.lib.core.ops — concrete atomic ops built on the :class:`Pipe` interface.

Each op is a ``Pipe`` subclass: it implements ``forward`` (and, where it makes
sense, ``stream``) and is invoked by calling the instance. Module-level
singletons plus thin function wrappers preserve pipe's flat public API
(``pipe.echo("hi")``) so existing callers keep working.
"""

from __future__ import annotations

from typing import AsyncIterator

from pipe.lib.core.pipe import Pipe

__all__ = ["Echo", "EchoStream", "echo", "echo_stream"]


class Echo(Pipe):
    """The first atomic op: data in, data out."""

    def forward(self, data: str) -> str:
        return data


class EchoStream(Pipe):
    """Async streaming op: yield ``data`` back in chunks.

    A stand-in for genuinely incremental ops (e.g. token-by-token
    translation). Lets the serving layer stream a response instead of
    buffering it whole.
    """

    def __init__(self, *, chunk_size: int = 16, name: str | None = None) -> None:
        super().__init__(name=name)
        self.chunk_size = chunk_size

    async def stream(
        self, data: str, *, chunk_size: int | None = None
    ) -> AsyncIterator[str]:
        size = chunk_size if chunk_size is not None else self.chunk_size
        for i in range(0, len(data), size):
            yield data[i : i + size]

    async def aforward(self, data: str, *, chunk_size: int | None = None) -> str:
        """Buffer the stream into a single string."""
        return "".join([chunk async for chunk in self.stream(data, chunk_size=chunk_size)])


# --- flat, backward-compatible function API --------------------------------

_echo = Echo()
_echo_stream = EchoStream()


def echo(data: str) -> str:
    """The first atomic op: data in, data out."""
    return _echo(data)


def echo_stream(data: str, *, chunk_size: int = 16) -> AsyncIterator[str]:
    """Async streaming op: yield ``data`` back in chunks."""
    return _echo_stream.astream(data, chunk_size=chunk_size)
