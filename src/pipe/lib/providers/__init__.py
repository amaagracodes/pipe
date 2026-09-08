"""pipe.lib.providers — pipes wrapping external model/service backends.

Built on :mod:`pipe.lib.core`. Exposes the :class:`ProviderPipe` interface and
concrete providers:

  * :class:`OpenRouterProvider` — text chat completions (via DSPy/LiteLLM).
  * :class:`STT` — audio-bytes-in / text-out transcription (direct HTTP to
    OpenRouter's ``/audio/transcriptions`` endpoint).
"""

from pipe.lib.providers.interface import ProviderPipe
from pipe.lib.providers.openrouter import OpenRouterProvider
from pipe.lib.providers.stt import STT

__all__ = ["ProviderPipe", "OpenRouterProvider", "STT"]
