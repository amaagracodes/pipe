"""pipe.lib.utils.finance — finance/banking pipes (pure, no network).

Domain grouping nested under the ``utils`` purpose folder:
  * :mod:`~pipe.lib.utils.finance.math`     — interest, returns, moving averages.
  * :mod:`~pipe.lib.utils.finance.validate` — Luhn / IBAN checksum validators.
  * :mod:`~pipe.lib.utils.finance.currency` — Money type + currency-aware rounding
    and minor-unit conversion. (Locale-aware formatting added by the i18n work.)
"""

from pipe.lib.utils.finance.currency import (
    CURRENCIES,
    Currency,
    FormatMoney,
    FromMinorUnits,
    Money,
    RoundMoney,
    ToMinorUnits,
)
from pipe.lib.utils.finance.math import (
    CAGR,
    EMA,
    SMA,
    CompoundInterest,
    Percent,
    PnL,
    ReturnPct,
    SimpleInterest,
    Volatility,
)
from pipe.lib.utils.finance.validate import IBANCheck, LuhnCheck

__all__ = [
    # math
    "Percent", "PnL", "ReturnPct", "SimpleInterest", "CompoundInterest",
    "CAGR", "SMA", "EMA", "Volatility",
    # validators
    "LuhnCheck", "IBANCheck",
    # currency
    "Currency", "CURRENCIES", "Money", "RoundMoney", "ToMinorUnits", "FromMinorUnits", "FormatMoney",
]
