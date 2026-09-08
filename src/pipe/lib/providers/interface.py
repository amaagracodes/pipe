"""pipe.lib.providers.interface — the interface for backend-wrapping pipes.

A ``ProviderPipe`` is a :class:`~pipe.lib.core.Pipe` that adapts an external
model or service backend into an atomic data-in/data-out op, so a backend call
chains like any other pipe. This is the contract only; concrete providers are
added later. Subclasses implement ``forward`` (and typically ``aforward`` for
real I/O) per the ``Pipe`` calling convention.
"""

from __future__ import annotations

from typing import Any

from pipe.lib.core import Pipe

__all__ = ["ProviderPipe"]


class ProviderPipe(Pipe):
    """Interface for ops that wrap an external model/service backend."""

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement forward()."
        )
