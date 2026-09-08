"""pipe.lib.core.chain — the composite that sequences atomic ops.

``Chain`` runs ``Pipe``s left-to-right, each op's output feeding the next.
Crucially ``Chain`` *is a* ``Pipe``, so a chain composes exactly like a single
op — this is what keeps individual ops atomic: they never learn about each
other; ``Chain`` owns the sequencing.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator

from pipe.lib.core.pipe import Pipe

__all__ = ["Chain"]


class Chain(Pipe):
    """A composite atomic op: run ``Pipe``s left-to-right, output feeding input.

    ``Chain`` *is a* ``Pipe`` — so a chain composes exactly like a single op
    (chain it further, call it, stream it, introspect it)::

        clean >> translate >> export          # -> Chain(clean, translate, export)
        pipeline = clean.then(translate)        # same thing, no operator

    Streaming applies the leading ops eagerly, then streams the final op, so an
    incremental tail (e.g. token-by-token translation) still streams to callers.
    """

    def __init__(self, *stages: Pipe, name: str | None = None) -> None:
        super().__init__(name=name)
        if not stages:
            raise ValueError("Chain needs at least one Pipe.")
        for s in stages:
            if not isinstance(s, Pipe):
                raise TypeError(f"Chain stages must be Pipes, got {type(s).__name__}")
        self.stages: list[Pipe] = list(stages)

    def forward(self, data: Any) -> Any:
        for stage in self.stages:
            data = stage(data)
        return data

    async def aforward(self, data: Any) -> Any:
        for stage in self.stages:
            data = await stage.acall(data)
        return data

    async def stream(self, data: Any) -> AsyncIterator[Any]:
        # Run every stage but the last synchronously via acall, then stream the tail.
        *head, tail = self.stages
        for stage in head:
            data = await stage.acall(data)
        async for chunk in tail.astream(data):
            yield chunk

    def __iter__(self) -> Iterator[Pipe]:
        return iter(self.stages)

    def __len__(self) -> int:
        return len(self.stages)
