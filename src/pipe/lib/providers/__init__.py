"""pipe.lib.providers — pipes wrapping external model/service backends.

Built on :mod:`pipe.lib.core`. Exposes the :class:`ProviderPipe` interface and
concrete providers. :class:`OpenRouterProvider` is importable without the
optional ``llm`` extra installed — it only requires DSPy when actually called.
"""

from pipe.lib.providers.interface import ProviderPipe
from pipe.lib.providers.openrouter import OpenRouterProvider

__all__ = ["ProviderPipe", "OpenRouterProvider"]
