"""pipe.lib.providers — pipes wrapping external model/service backends.

Built on :mod:`pipe.lib.core`. Exposes the :class:`ProviderPipe` interface and
concrete providers:

  * :class:`OpenRouterProvider` — text chat completions (via DSPy/LiteLLM).
  * :class:`STT` — audio-bytes-in / text-out transcription (OpenRouter).
  * :class:`FxRates` — currency conversion (Frankfurter, no key).
  * :class:`Weather` — current weather by lat/lon (Open-Meteo, no key).
  * :class:`Geocode` — place-name -> coordinates (Open-Meteo, no key).
  * :class:`Flights` — flight status (AviationStack; requires an API key).
  * :class:`SatelliteEmbedding` — AlphaEarth satellite embeddings (requires
    Google Earth Engine credentials + a GCP project).
"""

from pipe.lib.providers.flights import Flights
from pipe.lib.providers.fx import FxRates
from pipe.lib.providers.geocode import Geocode
from pipe.lib.providers.interface import ProviderPipe
from pipe.lib.providers.openrouter import OpenRouterProvider
from pipe.lib.providers.satellite import SatelliteEmbedding
from pipe.lib.providers.stt import STT
from pipe.lib.providers.weather import Weather

__all__ = [
    "ProviderPipe",
    "OpenRouterProvider",
    "STT",
    "FxRates",
    "Weather",
    "Geocode",
    "Flights",
    "SatelliteEmbedding",
]
