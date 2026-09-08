"""pipe.lib.detectors — detection pipes (e.g. language / PII / clause detection).

Built on :mod:`pipe.lib.core`. Exposes the :class:`DetectorPipe` interface plus
generic, reusable detectors (:class:`RegexDetector`, :class:`KeywordDetector`)
that are configured — not subclassed — to serve any domain.
"""

from pipe.lib.detectors.generic import KeywordDetector, RegexDetector, Rule
from pipe.lib.detectors.interface import DetectorPipe

__all__ = ["DetectorPipe", "Rule", "RegexDetector", "KeywordDetector"]
