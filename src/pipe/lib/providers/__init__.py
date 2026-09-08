"""pipe.lib.providers — pipes wrapping external model/service backends.

Built on :mod:`pipe.lib.core`. Exposes the :class:`ProviderPipe` interface.
"""

from pipe.lib.providers.interface import ProviderPipe

__all__ = ["ProviderPipe"]
