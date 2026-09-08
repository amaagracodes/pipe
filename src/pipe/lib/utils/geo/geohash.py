"""pipe.lib.utils.geo.geohash — pure geohash encoding pipe.

Standard base32 geohash algorithm, implemented with the stdlib only (no
external libraries).
"""

from __future__ import annotations

from typing import Sequence

from pipe.lib.core import Pipe

__all__ = ["GeohashEncode"]

# Geohash base32 alphabet (excludes a, i, l, o).
_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


class GeohashEncode(Pipe):
    """Encode a ``[lat, lon]`` point into a geohash string.

    Constructed with ``precision`` (number of geohash characters, default 9).
    Input is a ``[lat, lon]`` point; output is the geohash ``str``.
    """

    def __init__(self, precision: int = 9, *, name: str | None = None) -> None:
        super().__init__(name=name)
        if precision < 1:
            raise ValueError("precision must be >= 1")
        self.precision = int(precision)

    def forward(self, point: Sequence[float]) -> str:
        lat = float(point[0])
        lon = float(point[1])

        lat_range = [-90.0, 90.0]
        lon_range = [-180.0, 180.0]

        geohash: list[str] = []
        bits = [16, 8, 4, 2, 1]
        bit = 0
        ch = 0
        even = True  # start bisecting longitude

        while len(geohash) < self.precision:
            if even:
                mid = (lon_range[0] + lon_range[1]) / 2
                if lon >= mid:
                    ch |= bits[bit]
                    lon_range[0] = mid
                else:
                    lon_range[1] = mid
            else:
                mid = (lat_range[0] + lat_range[1]) / 2
                if lat >= mid:
                    ch |= bits[bit]
                    lat_range[0] = mid
                else:
                    lat_range[1] = mid

            even = not even
            if bit < 4:
                bit += 1
            else:
                geohash.append(_BASE32[ch])
                bit = 0
                ch = 0

        return "".join(geohash)
