"""pipe.lib.experts.generic — reusable, domain-neutral transform pipes.

These operate on the :class:`Prediction` envelope: they read detections and/or
rewrite the document, then pass the envelope on. Like the detectors, they carry
no domain knowledge — a legal redaction workflow is just a :class:`Redactor`
placed after a detector configured with legal patterns.

stdlib only — Pyodide-safe.
"""

from __future__ import annotations

from typing import Callable

from pipe.lib.experts.interface import ExpertPipe
from pipe.lib.shared.types import Detection, Prediction, Severity

__all__ = ["Redactor", "Annotator", "SeverityGate"]


class Redactor(ExpertPipe):
    """Mask the text spans of matching detections in place.

    Generic: which detections to redact is a predicate you supply (default: all
    that carry a span). The mask can be a fixed string or a function of the
    detection. Redacts right-to-left so earlier spans keep their offsets.
    """

    def __init__(
        self,
        *,
        mask: "str | Callable[[Detection], str]" = "[REDACTED]",
        select: "Callable[[Detection], bool] | None" = None,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self._mask = mask
        self._select = select or (lambda d: d.span is not None)

    def _mask_for(self, d: Detection) -> str:
        return self._mask(d) if callable(self._mask) else self._mask

    def forward(self, data: "str | Prediction") -> Prediction:
        pred = Prediction.of(data)
        targets = [d for d in pred.detections if d.span is not None and self._select(d)]
        if not targets:
            return pred
        text = pred.text
        # Apply from the end so earlier spans' indices stay valid.
        for d in sorted(targets, key=lambda d: d.span.start, reverse=True):  # type: ignore[union-attr]
            s = d.span  # narrowed above
            text = text[: s.start] + self._mask_for(d) + text[s.end :]  # type: ignore[union-attr]
        return pred.with_document(pred.document.with_text(text))


class Annotator(ExpertPipe):
    """Attach a compact summary of detections to ``document.meta``.

    Non-destructive: leaves text untouched, records counts-by-kind and the
    maximum severity under ``meta[key]`` so a downstream consumer (or the API
    layer) can render a report.
    """

    def __init__(self, *, key: str = "annotations", name: str | None = None) -> None:
        super().__init__(name=name)
        self.key = key

    def forward(self, data: "str | Prediction") -> Prediction:
        pred = Prediction.of(data)
        counts: dict[str, int] = {}
        for d in pred.detections:
            counts[d.kind] = counts.get(d.kind, 0) + 1
        summary = {
            "total": len(pred.detections),
            "by_kind": counts,
            "max_severity": pred.max_severity().name,
        }
        meta = dict(pred.document.meta)
        meta[self.key] = summary
        from dataclasses import replace

        return pred.with_document(replace(pred.document, meta=meta))


class SeverityGate(ExpertPipe):
    """Flag whether the envelope's findings meet a severity threshold.

    Records ``meta[key] = bool`` (does any detection reach ``threshold``?).
    Useful as the final step of a screening workflow — the caller inspects the
    flag to decide routing (e.g. escalate to human review).
    """

    def __init__(
        self,
        *,
        threshold: Severity = Severity.HIGH,
        key: str = "flagged",
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.threshold = threshold
        self.key = key

    def forward(self, data: "str | Prediction") -> Prediction:
        pred = Prediction.of(data)
        flagged = pred.max_severity() >= self.threshold
        meta = dict(pred.document.meta)
        meta[self.key] = flagged
        from dataclasses import replace

        return pred.with_document(replace(pred.document, meta=meta))
