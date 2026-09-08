"""pipe.lib.detectors.interface — the interface for detection pipes.

A ``DetectorPipe`` is a :class:`~pipe.lib.core.Pipe` that inspects its input and
emits a verdict (e.g. language identification, PII detection, quality scoring)
as an atomic data-in/data-out op. This is the contract only; concrete detectors
are added later. Subclasses implement ``forward`` (and optionally ``aforward``)
per the ``Pipe`` calling convention.
"""

from __future__ import annotations

from typing import Any

from pipe.lib.core import Pipe

__all__ = ["DetectorPipe"]


class DetectorPipe(Pipe):
    """Interface for detection ops (language / PII / quality / ...)."""

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"{type(self).__name__} must implement forward()."
        )
