"""pipe.lib.detectors — detection pipes (e.g. language / PII / quality detection).

Built on :mod:`pipe.lib.core`. Exposes the :class:`DetectorPipe` interface.
"""

from pipe.lib.detectors.interface import DetectorPipe

__all__ = ["DetectorPipe"]
