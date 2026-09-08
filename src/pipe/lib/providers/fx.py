"""pipe.lib.providers.fx — a currency-conversion provider pipe (Frankfurter).

One atomic op: **an amount in one currency → the converted amount in another**.
It calls the `Frankfurter <https://frankfurter.dev>`_ API — a free, no-key,
no-auth foreign-exchange service backed by ECB reference rates.

    from pipe.lib.providers.fx import FxRates

    fx = FxRates()
    fx({"amount": 100, "from": "USD", "to": "EUR"})
    # -> {"amount": 100.0, "from": "USD", "to": "EUR",
    #     "rate": 0.92, "result": 92.0, "date": "2024-01-05"}

    # Historical rates for a fixed date:
    FxRates(date="2020-01-02")({"amount": 100, "from": "USD", "to": "EUR"})

No API key is needed and none is sent. Provides both a sync ``forward``
(``httpx.Client``) and async ``aforward`` (``httpx.AsyncClient``); ``httpx`` is
imported lazily inside the methods so importing this module stays cheap.
"""

from __future__ import annotations

from typing import Any

from pipe.lib.providers.interface import ProviderPipe

__all__ = ["FxRates"]

_BASE_URL = "https://api.frankfurter.dev/v1"


class FxRates(ProviderPipe):
    """Convert an amount between currencies via Frankfurter (no key).

    Args:
        date: optional ``"YYYY-MM-DD"`` for historical rates. When set, requests
            hit ``/v1/{date}``; otherwise ``/v1/latest`` (most recent rates).
        timeout: HTTP timeout in seconds.
        name: optional pipe name (see :class:`~pipe.lib.core.Pipe`).
    """

    def __init__(
        self,
        *,
        date: str | None = None,
        timeout: float = 30.0,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.date = date
        self.timeout = timeout

    # --- request/response helpers ----------------------------------------

    def _path(self) -> str:
        # A plain historical date hits /v1/{date}; otherwise the latest rates.
        return f"{_BASE_URL}/{self.date}" if self.date else f"{_BASE_URL}/latest"

    @staticmethod
    def _parse(data: dict[str, Any], base: str, quote: str, amount: float) -> dict[str, Any]:
        rates = data.get("rates")
        if not isinstance(rates, dict) or quote not in rates:
            raise ValueError(
                f"Frankfurter response missing rate for {quote!r}: keys={list(rates or {})}"
            )
        # Frankfurter returns the rate for the requested `amount` (its `amount`
        # query param), so `result` is read directly and `rate` is per-unit.
        result = float(rates[quote])
        rate = result / amount if amount else 0.0
        return {
            "amount": amount,
            "from": base,
            "to": quote,
            "rate": rate,
            "result": result,
            "date": data.get("date"),
        }

    @staticmethod
    def _inputs(payload: dict[str, Any]) -> tuple[float, str, str]:
        try:
            amount = float(payload["amount"])
            base = str(payload["from"]).upper()
            quote = str(payload["to"]).upper()
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "FxRates expects {'amount': float, 'from': 'USD', 'to': 'EUR'}"
            ) from exc
        return amount, base, quote

    def _params(self, amount: float, base: str, quote: str) -> dict[str, Any]:
        return {"base": base, "symbols": quote, "amount": amount}

    # --- the atomic op: amount in, converted amount out -------------------

    def forward(self, data: dict[str, Any]) -> dict[str, Any]:
        import httpx

        amount, base, quote = self._inputs(data)
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(self._path(), params=self._params(amount, base, quote))
            resp.raise_for_status()
            return self._parse(resp.json(), base, quote, amount)

    async def aforward(self, data: dict[str, Any]) -> dict[str, Any]:
        import httpx

        amount, base, quote = self._inputs(data)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(self._path(), params=self._params(amount, base, quote))
            resp.raise_for_status()
            return self._parse(resp.json(), base, quote, amount)

    def __repr__(self) -> str:
        return f"FxRates(date={self.date!r})"
