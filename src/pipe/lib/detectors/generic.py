"""pipe.lib.detectors.generic — reusable, domain-neutral detectors.

These pipes find things in text and append :class:`Detection`s to the running
:class:`Prediction`. They are entirely generic — a detector is defined by the
*patterns you give it*, not by any built-in notion of law, PII, or otherwise.
Legal presets (see :mod:`pipe.lib.workflows`) are just these detectors wired up
with legal patterns.

stdlib only (``re``) — Pyodide-safe.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Pattern

from pipe.lib.detectors.interface import DetectorPipe
from pipe.lib.shared.types import Detection, Prediction, Severity, Span

__all__ = ["Rule", "RegexDetector", "KeywordDetector"]


@dataclass(frozen=True, slots=True)
class Rule:
    """A single named detection rule.

    ``kind`` labels what a match means (e.g. ``"pii.email"``); ``pattern`` is a
    regex string; ``severity`` ranks a match. Case-insensitive by default.
    """

    kind: str
    pattern: str
    severity: Severity = Severity.MEDIUM
    flags: int = re.IGNORECASE

    def compile(self) -> "CompiledRule":
        return CompiledRule(self.kind, re.compile(self.pattern, self.flags), self.severity)


@dataclass(frozen=True, slots=True)
class CompiledRule:
    kind: str
    regex: Pattern[str]
    severity: Severity


class RegexDetector(DetectorPipe):
    """Scan text with a set of :class:`Rule`s and emit a Detection per match.

    Accepts a :class:`~pipe.lib.shared.Prediction`, ``Document``, or ``str`` and
    returns a ``Prediction`` with detections appended — so it drops into a chain
    before or after any transform.
    """

    def __init__(self, rules: Iterable[Rule], *, name: str | None = None) -> None:
        super().__init__(name=name)
        self.rules: list[CompiledRule] = [r.compile() for r in rules]

    def forward(self, data: "str | Prediction" ) -> Prediction:
        pred = Prediction.of(data)
        text = pred.text
        found: list[Detection] = []
        for rule in self.rules:
            for m in rule.regex.finditer(text):
                found.append(
                    Detection(
                        kind=rule.kind,
                        label=m.group(0),
                        span=Span(m.start(), m.end()),
                        severity=rule.severity,
                    )
                )
        return pred.add_detections(*found)


class KeywordDetector(DetectorPipe):
    """Emit a Detection wherever any configured keyword/phrase appears.

    A convenience over :class:`RegexDetector` for plain word lists: pass a
    ``kind`` and the phrases that signal it (e.g. privileged-communication
    markers). Matches on word boundaries, case-insensitive.
    """

    def __init__(
        self,
        kind: str,
        keywords: Iterable[str],
        *,
        severity: Severity = Severity.MEDIUM,
        whole_word: bool = True,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        self.kind = kind
        self.severity = severity
        terms = [re.escape(k) for k in keywords if k]
        if not terms:
            self._regex: Pattern[str] | None = None
        else:
            body = "|".join(terms)
            pat = rf"\b(?:{body})\b" if whole_word else rf"(?:{body})"
            self._regex = re.compile(pat, re.IGNORECASE)

    def forward(self, data: "str | Prediction") -> Prediction:
        pred = Prediction.of(data)
        if self._regex is None:
            return pred
        found = [
            Detection(
                kind=self.kind,
                label=m.group(0),
                span=Span(m.start(), m.end()),
                severity=self.severity,
            )
            for m in self._regex.finditer(pred.text)
        ]
        return pred.add_detections(*found)
