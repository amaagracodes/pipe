"""pipe.lib.utils.finance.currency — currency primitives (pure, no FX network).

Money must never be a bare float: different currencies have different minor-unit
scales (USD/EUR = 2 places, JPY = 0, BHD/KWD = 3), and rounding must respect
that. These primitives model the *representation* of money — the value type,
currency metadata, correct rounding, and minor-unit (integer cents) conversion.

Live conversion *rates* are a network concern handled by an FX provider; nothing
here touches the network.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Mapping

from pipe.lib.core import Pipe

__all__ = ["Currency", "CURRENCIES", "Money", "RoundMoney", "ToMinorUnits", "FromMinorUnits", "FormatMoney"]


@dataclass(frozen=True, slots=True)
class Currency:
    """ISO-4217-ish currency metadata: code + number of minor-unit decimals."""

    code: str
    decimals: int = 2

    def quantum(self) -> Decimal:
        """The smallest representable step, e.g. Decimal('0.01') for 2 decimals."""
        return Decimal(1).scaleb(-self.decimals)


#: A small, extend-as-needed registry of common currencies with correct scales.
CURRENCIES: Mapping[str, Currency] = {
    "USD": Currency("USD", 2),
    "EUR": Currency("EUR", 2),
    "GBP": Currency("GBP", 2),
    "INR": Currency("INR", 2),
    "JPY": Currency("JPY", 0),   # no minor unit
    "KRW": Currency("KRW", 0),
    "BHD": Currency("BHD", 3),   # three-decimal currencies
    "KWD": Currency("KWD", 3),
    "CHF": Currency("CHF", 2),
    "CAD": Currency("CAD", 2),
    "AUD": Currency("AUD", 2),
    "CNY": Currency("CNY", 2),
}


def currency_of(code: "str | Currency") -> Currency:
    """Resolve a currency code to :class:`Currency` (default 2 decimals if unknown)."""
    if isinstance(code, Currency):
        return code
    c = str(code).upper()
    return CURRENCIES.get(c, Currency(c, 2))


@dataclass(frozen=True, slots=True)
class Money:
    """An amount in a specific currency. Amount held as ``Decimal`` for exactness.

    Construct from any number-like: ``Money("19.99", "USD")``. Arithmetic is
    intentionally minimal and currency-checked — mixing currencies raises rather
    than silently producing a wrong total.
    """

    amount: Decimal
    currency: Currency

    @classmethod
    def of(cls, amount: "str | int | float | Decimal", code: "str | Currency" = "USD") -> "Money":
        return cls(amount=Decimal(str(amount)), currency=currency_of(code))

    def _check(self, other: "Money") -> None:
        if self.currency.code != other.currency.code:
            raise ValueError(
                f"currency mismatch: {self.currency.code} vs {other.currency.code}"
            )

    def __add__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def rounded(self) -> "Money":
        """Round to the currency's minor unit using banker's rounding."""
        q = self.amount.quantize(self.currency.quantum(), rounding=ROUND_HALF_EVEN)
        return Money(q, self.currency)

    def minor_units(self) -> int:
        """Integer amount in the smallest unit (e.g. cents). USD 1.99 -> 199."""
        scaled = self.rounded().amount.scaleb(self.currency.decimals)
        return int(scaled.to_integral_value(rounding=ROUND_HALF_EVEN))

    def __str__(self) -> str:
        return f"{self.rounded().amount} {self.currency.code}"


class RoundMoney(Pipe):
    """Round a :class:`Money` to its currency's minor unit (banker's rounding)."""

    def forward(self, money: Money) -> Money:
        return money.rounded()


class ToMinorUnits(Pipe):
    """Convert a :class:`Money` to an integer count of minor units (cents)."""

    def forward(self, money: Money) -> int:
        return money.minor_units()


class FromMinorUnits(Pipe):
    """Build a :class:`Money` from integer minor units for a given currency.

    Input mapping ``{"units": int, "currency": "USD"}`` (or a bare int with the
    currency fixed at construction).
    """

    def __init__(self, currency: "str | Currency | None" = None, *, name: str | None = None) -> None:
        super().__init__(name=name)
        self.currency = currency_of(currency) if currency is not None else None

    def forward(self, data: "int | dict") -> Money:
        if isinstance(data, dict):
            units = int(data["units"])
            cur = currency_of(data.get("currency", self.currency or "USD"))
        else:
            if self.currency is None:
                raise ValueError("FromMinorUnits needs a currency (constructor or input dict)")
            units = int(data)
            cur = self.currency
        amount = Decimal(units).scaleb(-cur.decimals)
        return Money(amount, cur)


class FormatMoney(Pipe):
    """Format a :class:`Money` as a locale-aware currency string.

    Uses babel's CLDR data so grouping and decimal marks are correct per
    locale: ``1,234.56`` (en-US), ``1.234,56`` (de-DE), ``1,23,456.78`` (en-IN
    Indian grouping), etc. Locale precedence: explicit ``locale`` arg, else the
    ambient :class:`~pipe.lib.shared.FinancialRequestContext` /
    :class:`RequestContext` locale, else ``en``.

    If babel isn't installed it falls back to a plain ``<amount> <code>`` string
    (so the pipe still works, just not locale-formatted).
    """

    def __init__(self, locale: "str | None" = None, *, name: str | None = None) -> None:
        super().__init__(name=name)
        self._locale = locale

    def _resolve_locale(self) -> str:
        if self._locale:
            return self._locale
        ctx = self.ctx()
        if ctx is not None and getattr(ctx, "locale", None) is not None:
            tag = ctx.locale.tag
            if tag and tag != "und":
                return tag
        return "en"

    def forward(self, money: Money) -> str:
        m = money.rounded()
        locale = self._resolve_locale()
        try:
            from babel.numbers import format_currency

            # babel wants underscores (e.g. en_IN); accept BCP-47 hyphens too.
            return format_currency(m.amount, m.currency.code, locale=locale.replace("-", "_"))
        except Exception:
            # babel missing or locale unknown — safe, non-localized fallback.
            return f"{m.amount} {m.currency.code}"
