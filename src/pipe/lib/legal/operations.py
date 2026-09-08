"""pipe.lib.legal.operations — atomic legal operations, one act per pipe.

Each class here is a single :class:`~pipe.lib.core.Pipe` that performs *one*
act a legal professional does — detect PII, spot clauses, screen for privilege,
extract citations, redact. They are atomic: no internal multi-step chaining.
Callers compose them with ``>>`` when they want a pipeline; that is deliberately
not baked in here.

Every op is *jurisdiction-aware*: it resolves the rules applicable to a target
:class:`~pipe.lib.shared.Jurisdiction` from the scoped :data:`~.catalog.RULES`
registry (authority- and specificity-ordered, with lex-specialis override), so
the same op behaves correctly for ``us/ny`` vs ``us/wa/king/seattle`` vs
``in`` with ``domain``/``personal_law`` facets. The jurisdiction is fixed at
construction; leave it unset for jurisdiction-neutral (ANY) rules only.

All ops take and return the shared :class:`~pipe.lib.shared.Prediction`
envelope (a bare ``str``/``Document`` is coerced), so they interoperate with
every other pipe.
"""

from __future__ import annotations

from typing import Callable, Iterable

from pipe.lib.detectors import Rule
from pipe.lib.experts.interface import ExpertPipe
from pipe.lib.legal.catalog import RULES
from pipe.lib.shared import (
    ANY,
    Detection,
    Jurisdiction,
    Prediction,
    Severity,
    Span,
)

__all__ = [
    "DetectPII",
    "SpotClauses",
    "IdentifyStatutes",
    "ExtractCitations",
    "ScreenPrivilege",
    "Redact",
]


def _resolve(jurisdiction: Jurisdiction, categories: Iterable[str] | None) -> list[Rule]:
    """Applicable rules for a jurisdiction, de-duplicated per ``kind``.

    Uses the registry's lex-specialis override (a more specific / higher
    authority rule wins for the same ``kind``), then optionally filters to a set
    of top-level categories (``{"pii"}``, ``{"clause"}``, ...).
    """
    rules = RULES.resolve_by(jurisdiction, key=lambda r: r.kind)
    if categories is not None:
        cats = set(categories)
        rules = [r for r in rules if r.kind.split(".", 1)[0] in cats]
    return rules


class _RuleScan(ExpertPipe):
    """Shared base: scan text with jurisdiction-resolved rules, emit Detections.

    Not exported — each concrete op fixes which categories it scans, so it stays
    a single-purpose atomic operation while reusing one scanning implementation.
    """

    categories: tuple[str, ...] | None = None

    def __init__(
        self,
        jurisdiction: str | Jurisdiction = ANY,
        *,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.jurisdiction = (
            jurisdiction if isinstance(jurisdiction, Jurisdiction)
            else Jurisdiction.parse(jurisdiction)
        )
        self._rules = [
            r.compile() for r in _resolve(self.jurisdiction, self.categories)
        ]

    def forward(self, data: "str | Prediction") -> Prediction:
        pred = Prediction.of(data)
        text = pred.text
        found: list[Detection] = []
        for cr in self._rules:
            for m in cr.regex.finditer(text):
                found.append(
                    Detection(
                        kind=cr.kind,
                        label=m.group(0),
                        span=Span(m.start(), m.end()),
                        severity=cr.severity,
                    )
                )
        return pred.add_detections(*found)


class DetectPII(_RuleScan):
    """Atomic op: find personally identifiable information for a jurisdiction.

    Emits ``pii.*`` detections (SSN in the US, Aadhaar/PAN in India, etc.).
    Does not modify text — pair with :class:`Redact` if masking is wanted.
    """

    categories = ("pii",)


class SpotClauses(_RuleScan):
    """Atomic op: identify contract clauses applicable in a jurisdiction.

    Emits ``clause.*`` detections (indemnity, arbitration, non-compete —
    with the jurisdiction-correct severity, e.g. non-compete is HIGH in NY).
    """

    categories = ("clause",)


class ExtractCitations(_RuleScan):
    """Atomic op: extract legal citations valid for a jurisdiction.

    Emits ``cite.*`` detections (USC/CFR in the US, AIR in India, etc.).
    """

    categories = ("cite",)


class IdentifyStatutes(_RuleScan):
    """Atomic op: identify statutes/acts applicable in a jurisdiction.

    Emits ``statute.*`` detections. This is where facet-selected rules surface —
    e.g. in ``in`` with ``domain=family`` + ``personal_law``, the applicable
    marriage act depends on the community (Hindu Marriage Act vs Special
    Marriage Act, etc.).
    """

    categories = ("statute",)


class ScreenPrivilege(ExpertPipe):
    """Atomic op: decide whether a document appears privileged.

    Resolves ``privileged`` markers for the jurisdiction, scans, and records a
    single boolean verdict in ``document.meta[key]`` plus the matched markers as
    detections. One act: the privilege screen — no redaction, no annotation.
    """

    def __init__(
        self,
        jurisdiction: str | Jurisdiction = ANY,
        *,
        key: str = "privileged",
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.jurisdiction = (
            jurisdiction if isinstance(jurisdiction, Jurisdiction)
            else Jurisdiction.parse(jurisdiction)
        )
        self.key = key
        self._rules = [
            r.compile()
            for r in RULES.resolve_by(self.jurisdiction, key=lambda r: r.kind)
            if r.kind == "privileged"
        ]

    def forward(self, data: "str | Prediction") -> Prediction:
        pred = Prediction.of(data)
        found = [
            Detection(kind="privileged", label=m.group(0), span=Span(m.start(), m.end()), severity=cr.severity)
            for cr in self._rules
            for m in cr.regex.finditer(pred.text)
        ]
        pred = pred.add_detections(*found)
        from dataclasses import replace

        meta = dict(pred.document.meta)
        meta[self.key] = bool(found)
        return pred.with_document(replace(pred.document, meta=meta))


class Redact(ExpertPipe):
    """Atomic op: mask the spans of already-detected findings in the text.

    A pure transform — it redacts whatever detections the envelope already
    carries (optionally filtered), so it composes after any detector op:
    ``DetectPII("us") >> Redact()``. Which detections to mask is a predicate;
    the default masks every detection that has a span. Redacts right-to-left so
    earlier spans keep their offsets.
    """

    def __init__(
        self,
        *,
        mask: "str | Callable[[Detection], str]" = None,  # type: ignore[assignment]
        select: "Callable[[Detection], bool] | None" = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._mask = mask if mask is not None else (lambda d: f"[{d.kind.upper()}]")
        self._select = select or (lambda d: d.span is not None)

    def _mask_for(self, d: Detection) -> str:
        return self._mask(d) if callable(self._mask) else self._mask

    def forward(self, data: "str | Prediction") -> Prediction:
        pred = Prediction.of(data)
        targets = [d for d in pred.detections if d.span is not None and self._select(d)]
        if not targets:
            return pred
        text = pred.text
        for d in sorted(targets, key=lambda d: d.span.start, reverse=True):  # type: ignore[union-attr]
            s = d.span
            text = text[: s.start] + self._mask_for(d) + text[s.end :]  # type: ignore[union-attr]
        return pred.with_document(pred.document.with_text(text))
