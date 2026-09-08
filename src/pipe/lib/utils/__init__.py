"""pipe.lib.utils — purpose folder for reusable pipe utilities.

Root folders under ``lib/`` are *purpose*-specific (core, shared, providers,
detectors, experts, utils). Domain groupings are NOT roots — they nest here:

  * :mod:`~pipe.lib.utils.finance` — finance/banking math, validators, money.
  * :mod:`~pipe.lib.utils.geo`     — pure geospatial math (haversine, geohash…).
  * :mod:`~pipe.lib.utils.search`  — search-relevance analyzers (SEO/AEO/GEO).
  * :mod:`~pipe.lib.utils.flow`    — control-flow combinators (Map/Filter/Branch).

Only pipes that carry real weight live here — genuine domain logic or
composition machinery. Trivial one-liners are intentionally not wrapped.
"""

from pipe.lib.utils.finance import (
    CAGR,
    EMA,
    SMA,
    CompoundInterest,
    FormatMoney,
    IBANCheck,
    LuhnCheck,
    Money,
    Percent,
    PnL,
    ReturnPct,
    SimpleInterest,
    Volatility,
)
from pipe.lib.utils.flow import Branch, Filter, Map
from pipe.lib.utils.geo import BoundingBox, GeohashEncode, Haversine, PointInBBox
from pipe.lib.utils.search.relevance import AEOAnalyzer, GEOAnalyzer, SEOAnalyzer

__all__ = [
    # finance
    "Percent",
    "PnL",
    "ReturnPct",
    "SimpleInterest",
    "CompoundInterest",
    "CAGR",
    "SMA",
    "EMA",
    "Volatility",
    "LuhnCheck",
    "IBANCheck",
    "Money",
    "FormatMoney",
    # geo
    "Haversine",
    "BoundingBox",
    "PointInBBox",
    "GeohashEncode",
    # search relevance
    "SEOAnalyzer",
    "AEOAnalyzer",
    "GEOAnalyzer",
    # flow
    "Map",
    "Filter",
    "Branch",
]
