"""pipe.lib.providers.flights — a flight status / schedules provider pipe.

Wraps the `AviationStack <https://aviationstack.com>`_ REST API as an atomic
``ProviderPipe``: a flight identifier goes in, the parsed flight record comes
out — so a live-flight lookup chains like any other pipe.

This is a **credentialed** integration: it needs an AviationStack access key.
The pipe stays importable and constructible without one; the key is only
required at *call* time. When it's missing, calling raises a clear, actionable
``RuntimeError`` telling you exactly which env var to set. The key is read from
the environment by default and is **never** logged or echoed — ``repr`` shows a
``has_key`` boolean only.

Networking uses ``httpx`` (already a dependency), imported lazily inside the
call methods so importing this module costs nothing. Both a sync path
(``httpx.Client``) and an async path (``httpx.AsyncClient``) are provided.

i18n: internationalization is a first-class concern across this package, so the
pipe accepts a :class:`~pipe.lib.shared.Locale` (or a BCP-47 string) and passes
its language subtag to AviationStack via the ``lang`` parameter so localized
fields (e.g. airport/city names) can come back in the caller's language when
the backend supports it. An explicit ``locale`` on the call wins; otherwise the
ambient :class:`~pipe.lib.shared.RequestContext` locale is used as a fallback.

    from pipe.lib.providers.flights import Flights

    flights = Flights()
    rec = flights({"flight_iata": "AA100"})   # -> dict (parsed flight record)
    rec = flights("AA100")                      # a bare code works too
    rec = await flights.acall({"flight_iata": "AA100"})   # async

Input:  ``{"flight_iata": "AA100"}`` (or a bare flight-code string ``"AA100"``).
Output: ``dict`` — the parsed flight record from AviationStack's ``data[0]``.
"""

from __future__ import annotations

import os
from typing import Any

from pipe.lib.providers.interface import ProviderPipe
from pipe.lib.shared import Locale, RequestContext

__all__ = ["Flights"]

_ENV_KEY = "AVIATIONSTACK_API_KEY"
_ENDPOINT = "http://api.aviationstack.com/v1/flights"


class Flights(ProviderPipe):
    """Look up live flight status / schedules via AviationStack.

    Args:
        api_key: AviationStack access key. Defaults to
            ``$AVIATIONSTACK_API_KEY``. Held only in memory; never logged or
            echoed (``repr`` shows only whether one is configured).
        locale: default :class:`~pipe.lib.shared.Locale` (or BCP-47 string) used
            to request localized fields; falls back to the ambient
            ``RequestContext`` locale, then to none.
        timeout: HTTP timeout in seconds.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        locale: "str | Locale | None" = None,
        timeout: float = 30.0,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.timeout = timeout
        self.locale = Locale.parse(locale) if locale is not None else None
        # Resolve the key once; keep it private and out of repr/logs.
        self._api_key = api_key or os.environ.get(_ENV_KEY)

    # --- request/response helpers ----------------------------------------

    @staticmethod
    def _flight_iata(data: "dict[str, Any] | str") -> str:
        """Coerce the call input to a flight IATA code.

        Accepts a bare code string (``"AA100"``) or a dict carrying the code
        under ``flight_iata`` / ``flight`` / ``iata``.
        """
        if isinstance(data, str):
            code = data.strip()
        elif isinstance(data, dict):
            raw = data.get("flight_iata") or data.get("flight") or data.get("iata")
            code = str(raw).strip() if raw is not None else ""
        else:
            raise TypeError(
                f"Flights expects a flight code str or a dict, got {type(data).__name__}."
            )
        if not code:
            raise ValueError(
                "Flights requires a flight IATA code, e.g. {'flight_iata': 'AA100'}."
            )
        return code

    def _resolve_locale(self) -> "Locale | None":
        """Explicit locale wins; else the ambient RequestContext locale."""
        if self.locale is not None:
            return self.locale
        ctx = self.ctx()
        if isinstance(ctx, RequestContext):
            return ctx.locale
        return None

    def _params(self, data: "dict[str, Any] | str") -> dict[str, Any]:
        if not self._api_key:
            raise RuntimeError(
                f"Flights has no AviationStack API key. Set the ${_ENV_KEY} "
                "environment variable, or pass api_key=... to Flights(...). "
                "Get a key at https://aviationstack.com."
            )
        params: dict[str, Any] = {
            "access_key": self._api_key,
            "flight_iata": self._flight_iata(data),
        }
        locale = self._resolve_locale()
        if locale is not None and locale.language and locale.language != "und":
            # Language hint for localized fields where the backend supports it.
            params["lang"] = locale.language
        return params

    @staticmethod
    def _first_record(payload: dict[str, Any]) -> dict[str, Any]:
        """Extract the first flight record; surface API errors clearly."""
        if isinstance(payload, dict) and "error" in payload:
            err = payload["error"]
            message = err.get("message") if isinstance(err, dict) else err
            raise RuntimeError(f"AviationStack API error: {message}")
        data = payload.get("data") if isinstance(payload, dict) else None
        if not data:
            raise ValueError("AviationStack returned no flight records for that query.")
        return data[0]

    # --- the atomic op: flight code in, flight record out -----------------

    def forward(self, data: "dict[str, Any] | str") -> dict[str, Any]:
        import httpx

        params = self._params(data)
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(_ENDPOINT, params=params)
            resp.raise_for_status()
            return self._first_record(resp.json())

    async def aforward(self, data: "dict[str, Any] | str") -> dict[str, Any]:
        import httpx

        params = self._params(data)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(_ENDPOINT, params=params)
            resp.raise_for_status()
            return self._first_record(resp.json())

    def __repr__(self) -> str:
        # Never include the key; show only whether one is configured.
        loc = self.locale.tag if self.locale is not None else None
        return f"Flights(locale={loc!r}, has_key={bool(self._api_key)})"
