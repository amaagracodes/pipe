"""pipe.lib.utils.search.relevance._common — shared, pure text helpers.

Internal helpers shared by the SEO / AEO / GEO analyzers so each analyzer stays
a single atomic concern while reusing one deterministic tokenizer, sentence
splitter, and locale-resolution rule. Nothing here touches the network; all
functions are pure and stdlib-only (Pyodide-safe).

Locale resolution rule (shared by every analyzer), most→least preferred:

  1. an explicit ``locale`` argument passed to ``forward``,
  2. the incoming :class:`~pipe.lib.shared.types.Document`'s ``locale``,
  3. the ambient :class:`~pipe.lib.shared.context.RequestContext` locale
     (via ``Pipe.ctx()``),
  4. :data:`~pipe.lib.shared.locale.UND` (``Locale('und')``).

Explicit args always win; context is only a fallback — matching the platform
convention.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pipe.lib.shared import Locale, Prediction, UND

if TYPE_CHECKING:
    from pipe.lib.core import Pipe

__all__ = [
    "resolve_locale",
    "words",
    "sentences",
    "clamp_score",
    "readability_note",
]

# Unicode-aware word matcher: runs of letters/digits (handles non-ASCII scripts
# like Devanagari/CJK-adjacent alphabetics via the ``\w`` class under re.UNICODE,
# which is the default for str patterns in Python 3).
_WORD_RE = re.compile(r"\w+", re.UNICODE)

# Sentence terminators across common scripts: Latin (. ! ?), Devanagari danda
# (। ॥), CJK full-stops/marks (。！？), Arabic full stop (۔), Armenian (։).
_SENT_SPLIT_RE = re.compile(r"[.!?…।॥。！？؟۔։]+")

# Languages whose "words" are not space-delimited; average-word-length and
# words-per-sentence heuristics tuned for alphabetic scripts do not transfer, so
# readability notes flag this rather than pretending the numbers are comparable.
_UNSPACED_LANGS = frozenset({"zh", "ja", "th", "lo", "km", "my"})


def resolve_locale(
    pipe: "Pipe",
    explicit: "str | Locale | None",
    prediction: Prediction,
) -> Locale:
    """Resolve the locale for an analysis using the shared precedence rule.

    ``explicit`` (the ``forward`` arg) wins, then the document's own locale, then
    the ambient request-context locale, then :data:`UND`.
    """
    if explicit is not None:
        return explicit if isinstance(explicit, Locale) else Locale.parse(explicit)
    doc_locale = prediction.document.locale
    if doc_locale is not None:
        return doc_locale
    ctx = pipe.ctx()
    if ctx is not None and ctx.locale is not None:
        return ctx.locale
    return UND


def words(text: str) -> list[str]:
    """Tokenize into lowercased word tokens (Unicode-aware, deterministic)."""
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def sentences(text: str) -> list[str]:
    """Split into non-empty, stripped sentences on multi-script terminators."""
    return [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]


def clamp_score(value: float) -> float:
    """Clamp a raw score into the documented ``[0, 100]`` range, rounded to 0.1."""
    return round(max(0.0, min(100.0, value)), 1)


def readability_note(locale: Locale) -> str:
    """A language-aware caveat for length-based readability heuristics.

    Word-length / words-per-sentence thresholds are calibrated for space-
    delimited alphabetic scripts; for unspaced languages (zh/ja/th/…) they are
    not directly comparable, so the note says so instead of over-claiming.
    """
    if locale.language in _UNSPACED_LANGS:
        return (
            f"readability length heuristics are calibrated for space-delimited "
            f"scripts; interpret with care for locale '{locale.tag}'"
        )
    if locale.language == "und":
        return "locale undetermined; readability thresholds assume generic Latin-script prose"
    return f"readability thresholds applied for locale '{locale.tag}'"
