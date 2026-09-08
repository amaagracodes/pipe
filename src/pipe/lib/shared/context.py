"""pipe.lib.shared.context — the RequestContext hierarchy.

Cross-cutting request data (locale, jurisdiction, currency, request id) should
travel *ambiently*, not be threaded through every ``forward`` signature. This
module defines the data; the thread-local plumbing + ``Pipe.context(...)`` /
``Pipe.require_context(...)`` live in :mod:`pipe.lib.core`.

Design (per product direction): ``RequestContext`` is the **base** with the
universal fields; each domain **extends** it to declare the fields its handlers
need. A handler asks for its context type via ``require_context`` and gets a
clear error if the ambient context is missing or the wrong type — so required
context is explicit and self-documenting per domain, not a bag of optionals.

    with Pipe.context(FinancialRequestContext(locale="hi-IN", currency="INR")):
        FormatMoney()(Money.of("1234567.89", "INR"))   # reads ctx ambiently
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pipe.lib.shared.jurisdiction import ANY, Jurisdiction
from pipe.lib.shared.locale import UND, Locale

__all__ = [
    "RequestContext",
    "FinancialRequestContext",
    "LegalRequestContext",
    "GeoRequestContext",
]


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Base ambient context: fields every request may carry.

    ``locale`` drives i18n; ``request_id`` aids tracing; ``extra`` is a free-form
    escape hatch. Domain subclasses add their required fields.
    """

    locale: Locale = UND
    request_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Coerce a string locale to a Locale for ergonomic construction.
        if not isinstance(self.locale, Locale):
            object.__setattr__(self, "locale", Locale.parse(self.locale))

    def require(self) -> "RequestContext":
        """Validate that required fields are present; return self.

        The base has no hard requirements. Subclasses override to enforce theirs
        and raise a clear error when a needed field is missing.
        """
        return self


@dataclass(frozen=True, slots=True)
class FinancialRequestContext(RequestContext):
    """Context for finance/banking handlers. Requires a ``currency``."""

    currency: str | None = None

    def require(self) -> "FinancialRequestContext":
        if not self.currency:
            raise ValueError(
                "FinancialRequestContext requires 'currency' (e.g. 'USD', 'INR')."
            )
        return self


@dataclass(frozen=True, slots=True)
class LegalRequestContext(RequestContext):
    """Context for legal handlers. Requires a ``jurisdiction``."""

    jurisdiction: Jurisdiction = ANY

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.jurisdiction, Jurisdiction):
            object.__setattr__(self, "jurisdiction", Jurisdiction.parse(self.jurisdiction))

    def require(self) -> "LegalRequestContext":
        # ANY (empty path) is treated as "not specified" for legal work.
        if self.jurisdiction.depth == 0 and not self.jurisdiction.facets:
            raise ValueError(
                "LegalRequestContext requires a 'jurisdiction' (e.g. 'us/ny', 'in/mh')."
            )
        return self


@dataclass(frozen=True, slots=True)
class GeoRequestContext(RequestContext):
    """Context for geospatial handlers. Requires a reference point (lat, lon)."""

    lat: float | None = None
    lon: float | None = None

    def require(self) -> "GeoRequestContext":
        if self.lat is None or self.lon is None:
            raise ValueError("GeoRequestContext requires 'lat' and 'lon'.")
        return self
