"""pipe.lib.experts.interface — the interface for domain-expertise pipes.

An ``ExpertPipe`` is a :class:`~pipe.lib.core.Pipe` encapsulating domain
expertise — e.g. multilingual translation or domain-knowledge export — as an
atomic data-in/data-out op. This is the contract only; concrete experts are
added later. Subclasses implement ``forward`` (and optionally ``aforward`` /
``stream``) per the ``Pipe`` calling convention.
"""

from __future__ import annotations

from typing import Any

from pipe.lib.core import Pipe

__all__ = ["ExpertPipe"]


class ExpertPipe(Pipe):
    """Interface for domain-expertise ops (translation, knowledge export, ...)."""

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement forward()."
        )
