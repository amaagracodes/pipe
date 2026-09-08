"""pipe.lib.providers.weather — a current-weather provider pipe (Open-Meteo).

One atomic op: **a latitude/longitude in → current weather conditions out**. It
calls `Open-Meteo <https://open-meteo.com>`_'s forecast endpoint, a free, no-key,
no-auth weather API.

    from pipe.lib.providers.weather import Weather

    wx = Weather()
    wx({"lat": 52.52, "lon": 13.41})
    # -> {"temperature": 8.1, "windspeed": 12.5, "winddirection": 210,
    #     "weathercode": 3, "is_day": 1, "time": "2024-01-05T14:00"}

No API key is needed and none is sent. Provides both a sync ``forward``
(``httpx.Client``) and async ``aforward`` (``httpx.AsyncClient``); ``httpx`` is
imported lazily inside the methods so importing this module stays cheap.
"""

from __future__ import annotations

from typing import Any

from pipe.lib.providers.interface import ProviderPipe

__all__ = ["Weather"]

_ENDPOINT = "https://api.open-meteo.com/v1/forecast"


class Weather(ProviderPipe):
    """Fetch current weather for a coordinate via Open-Meteo (no key).

    Args:
        temperature_unit: ``"celsius"`` (default) or ``"fahrenheit"``.
        windspeed_unit: ``"kmh"`` (default), ``"ms"``, ``"mph"``, ``"kn"``.
        timeout: HTTP timeout in seconds.
        name: optional pipe name (see :class:`~pipe.lib.core.Pipe`).
    """

    def __init__(
        self,
        *,
        temperature_unit: str = "celsius",
        windspeed_unit: str = "kmh",
        timeout: float = 30.0,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.temperature_unit = temperature_unit
        self.windspeed_unit = windspeed_unit
        self.timeout = timeout

    # --- request/response helpers ----------------------------------------

    @staticmethod
    def _coords(payload: dict[str, Any]) -> tuple[float, float]:
        try:
            lat = float(payload["lat"])
            lon = float(payload["lon"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Weather expects {'lat': float, 'lon': float}") from exc
        return lat, lon

    def _params(self, lat: float, lon: float) -> dict[str, Any]:
        return {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "temperature_unit": self.temperature_unit,
            "windspeed_unit": self.windspeed_unit,
        }

    @staticmethod
    def _parse(data: dict[str, Any]) -> dict[str, Any]:
        current = data.get("current_weather")
        if not isinstance(current, dict):
            raise ValueError(
                f"Open-Meteo response missing 'current_weather': keys={list(data)}"
            )
        return current

    # --- the atomic op: coordinate in, conditions out ---------------------

    def forward(self, data: dict[str, Any]) -> dict[str, Any]:
        import httpx

        lat, lon = self._coords(data)
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(_ENDPOINT, params=self._params(lat, lon))
            resp.raise_for_status()
            return self._parse(resp.json())

    async def aforward(self, data: dict[str, Any]) -> dict[str, Any]:
        import httpx

        lat, lon = self._coords(data)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(_ENDPOINT, params=self._params(lat, lon))
            resp.raise_for_status()
            return self._parse(resp.json())

    def __repr__(self) -> str:
        return (
            f"Weather(temperature_unit={self.temperature_unit!r}, "
            f"windspeed_unit={self.windspeed_unit!r})"
        )
