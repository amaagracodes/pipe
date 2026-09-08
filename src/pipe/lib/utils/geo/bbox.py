"""pipe.lib.utils.geo.bbox — pure bounding-box pipes.

Compute the axis-aligned bounding box of a set of points, and test point
containment against a fixed box. No network, stdlib only.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from pipe.lib.core import Pipe

__all__ = ["BoundingBox", "PointInBBox"]


class BoundingBox(Pipe):
    """Axis-aligned bounding box of an iterable of ``[lat, lon]`` points.

    Input is an iterable of ``[lat, lon]`` points. Output is a dict
    ``{"min_lat", "min_lon", "max_lat", "max_lon"}`` (floats). Raises
    ``ValueError`` when given no points.
    """

    def forward(self, points: Iterable[Sequence[float]]) -> dict:
        lats: list[float] = []
        lons: list[float] = []
        for p in points:
            lats.append(float(p[0]))
            lons.append(float(p[1]))
        if not lats:
            raise ValueError("BoundingBox requires at least one point")
        return {
            "min_lat": min(lats),
            "min_lon": min(lons),
            "max_lat": max(lats),
            "max_lon": max(lons),
        }


class PointInBBox(Pipe):
    """Whether a ``[lat, lon]`` point falls inside a fixed bounding box.

    Constructed with a bbox dict ``{"min_lat", "min_lon", "max_lat",
    "max_lon"}``. Input is a ``[lat, lon]`` point; output is ``bool`` (inclusive
    of the box edges).
    """

    def __init__(self, bbox: dict, *, name: str | None = None) -> None:
        super().__init__(name=name)
        self.min_lat = float(bbox["min_lat"])
        self.min_lon = float(bbox["min_lon"])
        self.max_lat = float(bbox["max_lat"])
        self.max_lon = float(bbox["max_lon"])

    def forward(self, point: Sequence[float]) -> bool:
        lat = float(point[0])
        lon = float(point[1])
        return (
            self.min_lat <= lat <= self.max_lat
            and self.min_lon <= lon <= self.max_lon
        )
