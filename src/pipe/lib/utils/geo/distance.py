"""pipe.lib.utils.geo.distance — pure great-circle distance pipes.

Deterministic geospatial math over ``(lat, lon)`` points. No network, stdlib
math only.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from pipe.lib.core import Pipe

__all__ = ["Haversine"]

# Mean Earth radius (km) — the standard value used by the haversine formula.
EARTH_RADIUS_KM = 6371.0088


def _coerce_point(p: Any) -> tuple[float, float]:
    """Coerce ``[lat, lon]`` / ``(lat, lon)`` into a ``(float, float)`` tuple."""
    lat, lon = p[0], p[1]
    return float(lat), float(lon)


class Haversine(Pipe):
    """Great-circle distance in kilometres between two ``(lat, lon)`` points.

    Input is a dict ``{"a": [lat, lon], "b": [lat, lon]}`` or a 2-tuple of
    points ``((lat, lon), (lat, lon))``. Output is the distance in km (float),
    using the haversine formula with Earth radius ``6371.0088`` km.
    """

    def forward(self, data: Any) -> float:
        if isinstance(data, dict):
            a = _coerce_point(data["a"])
            b = _coerce_point(data["b"])
        else:
            # Iterable of two points: ((lat, lon), (lat, lon)).
            first, second = data[0], data[1]
            a = _coerce_point(first)
            b = _coerce_point(second)

        lat1, lon1 = a
        lat2, lon2 = b

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)

        h = (
            math.sin(d_phi / 2) ** 2
            + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))
        return EARTH_RADIUS_KM * c
