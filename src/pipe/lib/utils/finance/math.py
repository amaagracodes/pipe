"""pipe.lib.utils.finance.math — pure financial math pipes.

Deterministic calculations over numbers or number sequences. No network.
Values are plain floats; use the currency module for money representation and
rounding at the presentation edge.
"""

from __future__ import annotations

from typing import Sequence

from pipe.lib.core import Pipe

__all__ = [
    "Percent",
    "PnL",
    "ReturnPct",
    "SimpleInterest",
    "CompoundInterest",
    "CAGR",
    "SMA",
    "EMA",
    "Volatility",
]


class Percent(Pipe):
    """Multiply a value by ``rate`` (rate=0.2 -> 20% of the input)."""

    def __init__(self, rate: float, *, name: str | None = None) -> None:
        super().__init__(name=name)
        self.rate = rate

    def forward(self, value: float) -> float:
        return float(value) * self.rate


class PnL(Pipe):
    """Profit/loss: (exit - entry) * qty. Input ``{"entry","exit","qty"?}``."""

    def forward(self, data: dict) -> float:
        return (float(data["exit"]) - float(data["entry"])) * float(data.get("qty", 1))


class ReturnPct(Pipe):
    """Percentage return: (exit-entry)/entry * 100. Input ``{"entry","exit"}``."""

    def forward(self, data: dict) -> float:
        entry = float(data["entry"])
        if entry == 0:
            raise ValueError("ReturnPct undefined for entry == 0")
        return (float(data["exit"]) - entry) / entry * 100.0


class SimpleInterest(Pipe):
    """Simple interest final amount: principal * (1 + rate*years)."""

    def __init__(self, *, rate: float, years: float, name: str | None = None) -> None:
        super().__init__(name=name)
        self.rate = rate
        self.years = years

    def forward(self, principal: float) -> float:
        return float(principal) * (1 + self.rate * self.years)


class CompoundInterest(Pipe):
    """Compound interest final amount: principal * (1 + rate/n)^(n*years)."""

    def __init__(self, *, rate: float, years: float, periods_per_year: int = 1, name: str | None = None) -> None:
        super().__init__(name=name)
        self.rate = rate
        self.years = years
        self.n = periods_per_year

    def forward(self, principal: float) -> float:
        return float(principal) * (1 + self.rate / self.n) ** (self.n * self.years)


class CAGR(Pipe):
    """Compound annual growth rate (fraction) over ``years``. Input ``{"begin","end"}``."""

    def __init__(self, *, years: float, name: str | None = None) -> None:
        super().__init__(name=name)
        if years <= 0:
            raise ValueError("years must be > 0")
        self.years = years

    def forward(self, data: dict) -> float:
        begin = float(data["begin"])
        if begin <= 0:
            raise ValueError("CAGR undefined for begin <= 0")
        return (float(data["end"]) / begin) ** (1 / self.years) - 1


class SMA(Pipe):
    """Simple moving average of the trailing ``window`` values in a series."""

    def __init__(self, window: int, *, name: str | None = None) -> None:
        super().__init__(name=name)
        if window <= 0:
            raise ValueError("window must be > 0")
        self.window = window

    def forward(self, series: Sequence[float]) -> float:
        vals = [float(x) for x in series][-self.window :]
        if not vals:
            raise ValueError("empty series")
        return sum(vals) / len(vals)


class EMA(Pipe):
    """Exponential moving average over a series (returns the final EMA)."""

    def __init__(self, window: int, *, name: str | None = None) -> None:
        super().__init__(name=name)
        if window <= 0:
            raise ValueError("window must be > 0")
        self.window = window

    def forward(self, series: Sequence[float]) -> float:
        vals = [float(x) for x in series]
        if not vals:
            raise ValueError("empty series")
        k = 2 / (self.window + 1)
        ema = vals[0]
        for x in vals[1:]:
            ema = x * k + ema * (1 - k)
        return ema


class Volatility(Pipe):
    """Population standard deviation of a series (a simple volatility proxy)."""

    def forward(self, series: Sequence[float]) -> float:
        vals = [float(x) for x in series]
        n = len(vals)
        if n == 0:
            raise ValueError("empty series")
        mean = sum(vals) / n
        return (sum((x - mean) ** 2 for x in vals) / n) ** 0.5
