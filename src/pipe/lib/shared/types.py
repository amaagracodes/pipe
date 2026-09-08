"""pipe.lib.shared.types — the generic, domain-neutral data contracts.

These are the currency every pipe speaks: a :class:`Document` flows in, a
:class:`Prediction` flows out, carrying any :class:`Detection`s made along the
way. Nothing here is legal-specific — that's deliberate. Legal workflows are
built by *configuring* generic pipes over these generic types, so the same
machinery serves any domain.

stdlib only (dataclasses / enum) — Pyodide-safe, zero runtime deps. Values are
immutable (``frozen=True``) so a stage in a chain can't mutate a shared object
out from under a later stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import IntEnum
from typing import Any

from pipe.lib.shared.locale import Locale

__all__ = ["Severity", "Span", "Detection", "Document", "Prediction"]

# NOTE: jurisdiction is NOT a flat enum. Law varies hierarchically (country ->
# state -> city) and along non-geographic axes (subject-matter, personal law),
# so the model lives in :mod:`pipe.lib.shared.jurisdiction` (a territorial path
# + facets) with applicability/priority in :mod:`pipe.lib.shared.scope` and
# :mod:`pipe.lib.shared.registry`.


class Severity(IntEnum):
    """Ordered severity for a detection. Integer-backed so it compares/sorts."""

    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True, slots=True)
class Span:
    """A half-open character range ``[start, end)`` within a document's text."""

    start: int
    end: int

    def slice_of(self, text: str) -> str:
        return text[self.start : self.end]


@dataclass(frozen=True, slots=True)
class Detection:
    """A single finding a detector emits.

    Generic on purpose: ``kind`` names the finding (``"pii.email"``,
    ``"clause.indemnity"``, ``"privileged"`` — whatever a preset configures),
    ``label`` is the matched text, ``span`` locates it, ``severity`` ranks it.
    """

    kind: str
    label: str = ""
    span: Span | None = None
    severity: Severity = Severity.INFO
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Document:
    """The primary data payload flowing through a pipe: text plus metadata.

    ``locale`` (optional) records the language/region of the text so downstream
    pipes can respect it; it flows through a chain alongside the text. ``None``
    means unspecified (a handler may fall back to the ambient RequestContext).
    """

    text: str
    meta: dict[str, Any] = field(default_factory=dict)
    locale: "Locale | None" = None

    def with_text(self, text: str) -> "Document":
        """Return a copy with replaced text (immutability-friendly transform)."""
        return replace(self, text=text, meta=dict(self.meta))

    def with_locale(self, locale: "str | Locale") -> "Document":
        """Return a copy tagged with a locale (coerced from a string tag)."""
        loc = locale if isinstance(locale, Locale) else Locale.parse(locale)
        return replace(self, locale=loc, meta=dict(self.meta))


@dataclass(frozen=True, slots=True)
class Prediction:
    """The uniform output envelope, à la ``dspy.Prediction``.

    Wraps the (possibly transformed) :class:`Document` plus every
    :class:`Detection` accumulated so far, so any pipe's output is uniform and
    chainable — a detector can append findings and a transform can rewrite text
    while both return the same envelope.
    """

    document: Document
    detections: tuple[Detection, ...] = ()

    # --- convenience proxies ---------------------------------------------

    @property
    def text(self) -> str:
        return self.document.text

    # --- immutability-friendly builders ----------------------------------

    @classmethod
    def of(cls, value: "str | Document | Prediction") -> "Prediction":
        """Coerce a str / Document / Prediction into a Prediction."""
        if isinstance(value, Prediction):
            return value
        if isinstance(value, Document):
            return cls(document=value)
        return cls(document=Document(text=str(value)))

    def with_document(self, document: Document) -> "Prediction":
        return replace(self, document=document)

    def add_detections(self, *found: Detection) -> "Prediction":
        """Return a copy with additional detections appended."""
        if not found:
            return self
        return replace(self, detections=self.detections + tuple(found))

    def by_kind(self, prefix: str = "") -> tuple[Detection, ...]:
        """Detections whose ``kind`` starts with ``prefix`` (``""`` = all)."""
        return tuple(d for d in self.detections if d.kind.startswith(prefix))

    def max_severity(self) -> Severity:
        """Highest severity among detections (``INFO`` when there are none)."""
        return max((d.severity for d in self.detections), default=Severity.INFO)
