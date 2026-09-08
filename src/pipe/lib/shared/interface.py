"""pipe.lib.shared.interface — the interface for shared, cross-cutting pipes.

A ``SharedPipe`` is a :class:`~pipe.lib.core.Pipe` used by more than one module
(utility transforms, normalization, adapters that other layers reuse). This is
the contract only; concrete ops are added later. Subclasses implement
``forward`` (and optionally ``aforward`` / ``stream``) per the ``Pipe`` calling
convention.
"""

from __future__ import annotations

from typing import Any

from pipe.lib.core import Pipe

__all__ = ["SharedPipe"]


class SharedPipe(Pipe):
    """Interface for cross-cutting ops reused across modules."""

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement forward()."
        )
