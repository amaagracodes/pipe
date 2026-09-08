"""pipe.lib.providers.satellite — Google AlphaEarth Foundations embeddings.

Wraps Google's **AlphaEarth Foundations** annual satellite embeddings as an
atomic ``ProviderPipe``: a location + year goes in, a 64-dimensional embedding
vector comes out — so a geospatial embedding lookup chains like any other pipe.
The embeddings live in the Earth Engine dataset
``GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL``.

⚠️ **Heavier optional integration — Earth Engine credentials required.** Unlike
the other providers, this is *not* a simple REST endpoint you can hit with an
API key + ``httpx``. It requires:

  1. the ``earthengine-api`` package (the importable module is ``ee``),
  2. a Google Cloud project with the **Earth Engine API enabled**, and
  3. authenticated credentials — either an interactive
     ``earthengine authenticate`` (OAuth) or a service account.

This module is an **honest, guarded scaffold**. It stays importable and
constructible with none of the above installed or configured; the heavy
dependency is imported lazily and initialization is attempted only at *call*
time. It does **not** fabricate embeddings — when a prerequisite is missing it
raises a clear, actionable error telling you exactly what to install or
configure:

  * ``ee`` not installed  → ``ModuleNotFoundError`` (``pip install earthengine-api``),
  * ``ee`` present but not authenticated / no project → ``RuntimeError`` with the
    exact ``earthengine authenticate`` / project-id guidance.

Because Earth Engine's Python client is synchronous and CPU/IO heavy, the async
path runs the same work in a thread via ``asyncio.to_thread`` rather than
pretending to be natively async.

    from pipe.lib.providers.satellite import SatelliteEmbedding

    sat = SatelliteEmbedding()                       # ok without ee installed
    vec = sat({"lat": 37.77, "lon": -122.42, "year": 2024})   # -> list[float] (len 64)

Input:  ``{"lat": <float>, "lon": <float>, "year": <int, default 2024>}``.
        ``lat``/``lon`` fall back to the ambient
        :class:`~pipe.lib.shared.GeoRequestContext` when omitted.
Output: ``list[float]`` — the 64-dimensional embedding vector for that
        location/year (documented shape; produced only when Earth Engine is
        available and authenticated).
"""

from __future__ import annotations

from typing import Any

from pipe.lib.providers.interface import ProviderPipe
from pipe.lib.shared import GeoRequestContext

__all__ = ["SatelliteEmbedding"]

_DATASET = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
_EMBEDDING_DIM = 64
_DEFAULT_YEAR = 2024


class SatelliteEmbedding(ProviderPipe):
    """Fetch AlphaEarth Foundations annual embeddings via Google Earth Engine.

    Args:
        project: Google Cloud project id with the Earth Engine API enabled. If
            omitted, Earth Engine uses its own default resolution; supplying it
            explicitly avoids the common "no project" initialization error.
        scale: sampling scale in metres for the embedding pixel (the dataset's
            native resolution is 10 m).
        default_year: annual mosaic year used when a call omits ``year``.
        name: optional pipe name.
    """

    def __init__(
        self,
        *,
        project: str | None = None,
        scale: float = 10.0,
        default_year: int = _DEFAULT_YEAR,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.project = project
        self.scale = scale
        self.default_year = default_year
        self._ee: Any | None = None  # lazily imported + initialized `ee` module

    # --- lazy Earth Engine bootstrap --------------------------------------

    def _get_ee(self) -> Any:
        """Import and initialize Earth Engine lazily, with actionable errors."""
        if self._ee is not None:
            return self._ee
        try:
            import ee  # heavy optional dependency: the `earthengine-api` package
        except ModuleNotFoundError as exc:  # pragma: no cover - import guard
            raise ModuleNotFoundError(
                "SatelliteEmbedding requires Google Earth Engine, which is not "
                "installed. Install it with `pip install earthengine-api` and "
                "then authenticate with `earthengine authenticate` (or configure "
                "a service account)."
            ) from exc

        try:
            if self.project is not None:
                ee.Initialize(project=self.project)
            else:
                ee.Initialize()
        except Exception as exc:  # broad: ee raises various auth/init errors
            raise RuntimeError(
                "Earth Engine is installed but could not be initialized. This "
                "usually means missing credentials or no Cloud project. Run "
                "`earthengine authenticate` (OAuth) or configure a service "
                "account, and pass project=<your-gcp-project-id> to "
                "SatelliteEmbedding(...) (the project must have the Earth Engine "
                f"API enabled). Underlying error: {exc}"
            ) from exc

        self._ee = ee
        return self._ee

    # --- request helpers --------------------------------------------------

    def _coords(self, data: dict[str, Any]) -> tuple[float, float, int]:
        """Resolve (lat, lon, year); lat/lon fall back to ambient GeoRequestContext."""
        if not isinstance(data, dict):
            raise TypeError(
                f"SatelliteEmbedding expects a dict "
                f"{{'lat':, 'lon':, 'year':}}, got {type(data).__name__}."
            )
        lat = data.get("lat")
        lon = data.get("lon")
        if lat is None or lon is None:
            ctx = self.ctx()
            if isinstance(ctx, GeoRequestContext):
                lat = lat if lat is not None else ctx.lat
                lon = lon if lon is not None else ctx.lon
        if lat is None or lon is None:
            raise ValueError(
                "SatelliteEmbedding requires 'lat' and 'lon' (either in the call "
                "data or via an ambient GeoRequestContext)."
            )
        year = int(data.get("year", self.default_year))
        return float(lat), float(lon), year

    def _embedding_at(self, ee: Any, lat: float, lon: float, year: int) -> list[float]:
        """Query the annual embedding image and sample the 64-band vector."""
        point = ee.Geometry.Point([lon, lat])
        image = (
            ee.ImageCollection(_DATASET)
            .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
            .filterBounds(point)
            .first()
        )
        sample = image.sample(region=point, scale=self.scale, numPixels=1).first()
        values = sample.toDictionary().getInfo()
        # AlphaEarth embedding bands are named A00..A63.
        vector = [float(values[f"A{i:02d}"]) for i in range(_EMBEDDING_DIM)]
        return vector

    # --- the atomic op: location/year in, 64-float vector out -------------

    def forward(self, data: dict[str, Any]) -> list[float]:
        ee = self._get_ee()
        lat, lon, year = self._coords(data)
        return self._embedding_at(ee, lat, lon, year)

    async def aforward(self, data: dict[str, Any]) -> list[float]:
        import asyncio

        # Earth Engine's client is synchronous; run it off the event loop.
        return await asyncio.to_thread(self.forward, data)

    def __repr__(self) -> str:
        return (
            f"SatelliteEmbedding(dataset={_DATASET!r}, dim={_EMBEDDING_DIM}, "
            f"project={self.project!r}, ready={self._ee is not None})"
        )
