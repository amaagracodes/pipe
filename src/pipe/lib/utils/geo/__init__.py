"""pipe.lib.utils.geo — geospatial math pipes (pure, no network).

Domain grouping nested under the ``utils`` purpose folder. Every pipe here is
deterministic and depends only on the stdlib ``math`` module:

  * :mod:`~pipe.lib.utils.geo.distance` — :class:`Haversine` great-circle km.
  * :mod:`~pipe.lib.utils.geo.bbox`     — :class:`BoundingBox` /
    :class:`PointInBBox` axis-aligned bounding boxes.
  * :mod:`~pipe.lib.utils.geo.geohash`  — :class:`GeohashEncode` standard
    base32 geohash encoding.
"""

from pipe.lib.utils.geo.bbox import BoundingBox, PointInBBox
from pipe.lib.utils.geo.distance import Haversine
from pipe.lib.utils.geo.geohash import GeohashEncode

__all__ = [
    "Haversine",
    "BoundingBox",
    "PointInBBox",
    "GeohashEncode",
]
