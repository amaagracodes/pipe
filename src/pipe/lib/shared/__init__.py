"""pipe.lib.shared — cross-cutting contracts + the shared-pipe interface.

Built on :mod:`pipe.lib.core`. Exposes:

  * the :class:`SharedPipe` interface for cross-cutting ops,
  * the generic data contracts (:class:`Document`, :class:`Detection`,
    :class:`Prediction`, ...) that every other module speaks in, and
  * the generic, multi-axis **jurisdiction / scope** model
    (:class:`Jurisdiction`, :class:`Scope`, :class:`Scoped`,
    :class:`ScopedRegistry`) that lets any payload be scoped to a locality and
    resolved by specificity + authority — nothing domain-specific.
"""

from pipe.lib.shared.interface import SharedPipe
from pipe.lib.shared.jurisdiction import ANY, Jurisdiction
from pipe.lib.shared.registry import ScopedRegistry
from pipe.lib.shared.scope import Scope, Scoped
from pipe.lib.shared.types import (
    Detection,
    Document,
    Prediction,
    Severity,
    Span,
)

__all__ = [
    # interface
    "SharedPipe",
    # data contracts
    "Document",
    "Detection",
    "Prediction",
    "Severity",
    "Span",
    # jurisdiction / scope model
    "Jurisdiction",
    "ANY",
    "Scope",
    "Scoped",
    "ScopedRegistry",
]
