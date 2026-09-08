"""pipe.lib.utils.flow — control-flow combinator pipes.

These take *other pipes* as arguments and apply them, so composition scales
beyond a straight ``a >> b`` line: run a pipe over each item of a list, keep
items matching a predicate, or route to one of two pipes on a condition. All
pure — they add no I/O of their own, only orchestrate the pipes you give them.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from pipe.lib.core import Pipe

__all__ = ["Map", "Filter", "Branch"]


class Map(Pipe):
    """Apply an inner pipe to every item of an iterable input.

        Map(Lowercase())(["A", "B"])   # -> ["a", "b"]
    """

    def __init__(self, pipe: Pipe, *, name: str | None = None) -> None:
        super().__init__(name=name)
        if not isinstance(pipe, Pipe):
            raise TypeError(f"Map needs a Pipe, got {type(pipe).__name__}")
        self.pipe = pipe

    def forward(self, data: Iterable[Any]) -> list[Any]:
        return [self.pipe(item) for item in data]

    async def aforward(self, data: Iterable[Any]) -> list[Any]:
        return [await self.pipe.acall(item) for item in data]


class Filter(Pipe):
    """Keep items of an iterable for which ``predicate`` is truthy."""

    def __init__(self, predicate: Callable[[Any], bool], *, name: str | None = None) -> None:
        super().__init__(name=name)
        self.predicate = predicate

    def forward(self, data: Iterable[Any]) -> list[Any]:
        return [item for item in data if self.predicate(item)]


class Branch(Pipe):
    """Route input to ``if_true`` or ``if_false`` based on ``predicate``.

    Both branches are pipes; only the selected one runs. A missing branch acts
    as identity (passes the input through unchanged).
    """

    def __init__(
        self,
        predicate: Callable[[Any], bool],
        if_true: Pipe | None = None,
        if_false: Pipe | None = None,
        *,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.predicate = predicate
        self.if_true = if_true
        self.if_false = if_false

    def _run(self, branch: Pipe | None, data: Any) -> Any:
        return branch(data) if branch is not None else data

    def forward(self, data: Any) -> Any:
        branch = self.if_true if self.predicate(data) else self.if_false
        return self._run(branch, data)

    async def aforward(self, data: Any) -> Any:
        branch = self.if_true if self.predicate(data) else self.if_false
        return await branch.acall(data) if branch is not None else data
