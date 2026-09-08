"""pipe.lib.shared — cross-cutting helpers shared across modules.

Built on :mod:`pipe.lib.core`. Exposes the :class:`SharedPipe` interface.
"""

from pipe.lib.shared.interface import SharedPipe

__all__ = ["SharedPipe"]
