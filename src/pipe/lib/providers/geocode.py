"""pipe.lib.providers.geocode — a place-name → coordinates provider pipe.

One atomic op: **a place name in → its coordinates out**. It calls
`Open-Meteo <https://open-meteo.com>`_'s geocoding search endpoint, a free,
no-key, no-auth service.

    from pipe.lib.providers.geocode import Geocode

    geo = Geocode()
    geo("Berlin")
    # -> {"name": "Berlin", "lat": 52.52437, "lon": 13.41053, "country": "Germany"}

Internationalization is a first-class concern: the geocoder's result ``language``
can be set explicitly (``language="hi"``) or, when omitted, is taken as a
*fallback* from the ambient :class:`~pipe.lib.shared.RequestContext` locale
(``self.ctx().locale``). Explicit args always win over ambient context.

No API key is needed and none is sent. Provides both a sync ``forward``
(``httpx.Client``) and async ``aforward`` (``httpx.AsyncClient``); ``httpx`` is
imported lazily inside the methods so importing this module stays cheap.
"""

from __future__ import annotations

from typing import Any

from pipe.lib.providers.interface import ProviderPipe

__all__ = ["Geocode"]

_ENDPOINT = "https://geocoding-api.open-meteo.com/v1/search"


class Geocode(ProviderPipe):
    """Resolve a place name to coordinates via Open-Meteo geocoding (no key).

    Args:
        language: optional result language (ISO-639-1, e.g. ``"en"``, ``"hi"``).
            When omitted, it falls back to the ambient ``RequestContext`` locale
            (if any); explicit values always win over context.
        timeout: HTTP timeout in seconds.
        name: optional pipe name (see :class:`~pipe.lib.core.Pipe`).
    """

    def __init__(
        self,
        *,
        language: str | None = None,
        timeout: float = 30.0,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.language = language
        self.timeout = timeout

    # --- i18n: explicit language wins; ambient locale is the fallback -----

    def _language(self) -> str | None:
        if self.language:
            return self.language
        ctx = self.ctx()
        if ctx is not None:
            locale = getattr(ctx, "locale", None)
            # Locale.language is a lowercase ISO-639 code; "und" means unknown.
            lang = getattr(locale, "language", None)
            if lang and lang != "und":
                return lang
        return None

    # --- request/response helpers ----------------------------------------

    @staticmethod
    def _name(payload: Any) -> str:
        name = payload.strip() if isinstance(payload, str) else ""
        if not name:
            raise ValueError("Geocode expects a non-empty place-name string.")
        return name

    def _params(self, name: str) -> dict[str, Any]:
        params: dict[str, Any] = {"name": name, "count": 1}
        language = self._language()
        if language:
            params["language"] = language
        return params

    @staticmethod
    def _parse(data: dict[str, Any], name: str) -> dict[str, Any]:
        results = data.get("results")
        if not results:
            raise ValueError(f"No geocoding results for {name!r}.")
        top = results[0]
        return {
            "name": top.get("name"),
            "lat": top.get("latitude"),
            "lon": top.get("longitude"),
            "country": top.get("country"),
        }

    # --- the atomic op: place name in, coordinates out --------------------

    def forward(self, data: str) -> dict[str, Any]:
        import httpx

        name = self._name(data)
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(_ENDPOINT, params=self._params(name))
            resp.raise_for_status()
            return self._parse(resp.json(), name)

    async def aforward(self, data: str) -> dict[str, Any]:
        import httpx

        name = self._name(data)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(_ENDPOINT, params=self._params(name))
            resp.raise_for_status()
            return self._parse(resp.json(), name)

    def __repr__(self) -> str:
        return f"Geocode(language={self.language!r})"
