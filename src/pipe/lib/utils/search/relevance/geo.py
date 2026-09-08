"""pipe.lib.utils.search.relevance.geo — Generative Engine Optimization analyzer.

NOTE: **GEO here means Generative Engine Optimization, NOT geography.** This is
distinct from :class:`~pipe.lib.shared.context.GeoRequestContext` (geospatial).

``GEOAnalyzer`` scores content for its chance of being *cited* inside a generative
answer (ChatGPT, Perplexity, Gemini). Generative engines preferentially quote
material that is verifiable and attributable, so this rewards citability signals:
statistics/numbers, quotable authoritative statements, named entities and
sources, clear structured claims. Pure and deterministic — no network.

Locale-aware: attribution cue words ("according to", "study", …) are recognized
across several languages so the heuristic isn't English-only.
"""

from __future__ import annotations

import re

from pipe.lib.core import Pipe
from pipe.lib.shared import Locale, Prediction

from pipe.lib.utils.search.relevance._common import (
    clamp_score,
    resolve_locale,
    sentences,
    words,
)

__all__ = ["GEOAnalyzer"]

# Component weights (sum = 100). Fixed + documented for determinism.
_W_STATS = 25.0
_W_SOURCES = 25.0
_W_ENTITIES = 20.0
_W_QUOTABLE = 15.0
_W_CLARITY = 15.0

# Attribution / evidence cue phrases per language (walk locale fallbacks).
_ATTRIBUTION_CUES = {
    "und": ("according to", "study", "studies", "research", "report", "survey",
            "data", "source", "cited", "published", "found that", "shows that",
            "shows", "reveals", "estimate", "analysis", "%", "percent"),
    "en": ("according to", "study", "studies", "research", "report", "survey",
           "data", "source", "cited", "published", "found that", "shows that",
           "shows", "reveals", "estimate", "analysis", "percent"),
    "es": ("según", "estudio", "investigación", "informe", "encuesta", "datos",
           "fuente", "publicado", "revela", "análisis", "por ciento"),
    "fr": ("selon", "étude", "recherche", "rapport", "enquête", "données",
           "source", "publié", "révèle", "analyse", "pour cent"),
    "de": ("laut", "studie", "forschung", "bericht", "umfrage", "daten",
           "quelle", "veröffentlicht", "zeigt", "analyse", "prozent"),
    "hi": ("के अनुसार", "अध्ययन", "शोध", "रिपोर्ट", "सर्वेक्षण", "डेटा", "स्रोत", "प्रतिशत"),
    "pt": ("de acordo com", "estudo", "pesquisa", "relatório", "pesquisa",
           "dados", "fonte", "publicado", "revela", "análise", "por cento"),
}

_NUMBER_RE = re.compile(r"\b\d[\d,\.]*\b|\b\d+\s?%|\b\d+\s?percent\b", re.IGNORECASE)
_PERCENT_RE = re.compile(r"\d+(?:\.\d+)?\s?%|\d+\s?percent", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
# A capitalized multi-word run is a weak proper-noun / named-entity proxy
# (Latin scripts). Deterministic and dependency-free.
_PROPER_NOUN_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")
_QUOTE_RE = re.compile(r"[\"“”«»].+?[\"“”«»]")


class GEOAnalyzer(Pipe):
    """Score content for Generative Engine Optimization (citability) → ``dict``.

    (GEO = *Generative Engine Optimization*, i.e. being cited by LLM answer
    engines — not geography.)

    Input: ``str | Document | Prediction`` (coerced via ``Prediction.of``).
    Optional ``locale`` (call arg) overrides locale resolution.

    Output ``dict``::

        {
          "score": float,               # 0–100 overall (weighted blend)
          "locale": str,
          "components": {               # each 0–100
            "statistics": float, "sources": float, "named_entities": float,
            "quotable": float, "clarity": float,
          },
          "metrics": {...},
          "suggestions": [str, ...],
        }

    Component weights (fixed, sum 100): statistics 25, sources 25,
    named_entities 20, quotable 15, clarity 15. Deterministic.
    """

    def forward(
        self,
        data: "str | Prediction",
        *,
        locale: "str | Locale | None" = None,
    ) -> dict:
        pred = Prediction.of(data)
        loc = resolve_locale(self, locale, pred)
        text = pred.text
        sents = sentences(text)
        suggestions: list[str] = []

        st_score, st_metrics = self._score_statistics(text, suggestions)
        sr_score, sr_metrics = self._score_sources(text, loc, suggestions)
        en_score, en_metrics = self._score_entities(text, suggestions)
        qt_score, qt_metrics = self._score_quotable(text, suggestions)
        cl_score, cl_metrics = self._score_clarity(sents, suggestions)

        overall = clamp_score(
            st_score * _W_STATS / 100.0
            + sr_score * _W_SOURCES / 100.0
            + en_score * _W_ENTITIES / 100.0
            + qt_score * _W_QUOTABLE / 100.0
            + cl_score * _W_CLARITY / 100.0
        )

        return {
            "score": overall,
            "locale": loc.tag,
            "components": {
                "statistics": clamp_score(st_score),
                "sources": clamp_score(sr_score),
                "named_entities": clamp_score(en_score),
                "quotable": clamp_score(qt_score),
                "clarity": clamp_score(cl_score),
            },
            "metrics": {
                "sentence_count": len(sents),
                **st_metrics,
                **sr_metrics,
                **en_metrics,
                **qt_metrics,
                **cl_metrics,
            },
            "suggestions": suggestions,
        }

    # --- component scorers -------------------------------------------------

    def _score_statistics(self, text: str, suggestions: list[str]) -> tuple[float, dict]:
        numbers = _NUMBER_RE.findall(text)
        percents = _PERCENT_RE.findall(text)
        n_num = len(numbers)
        # Percentages/statistics are especially citable; weight them higher.
        raw = n_num * 20.0 + len(percents) * 15.0
        score = min(100.0, raw)
        if n_num == 0:
            suggestions.append("Add statistics or concrete numbers — generative engines cite figures.")
        elif not percents:
            suggestions.append("Include a percentage or rate; quantified claims are highly citable.")
        return score, {"number_count": n_num, "percent_count": len(percents)}

    def _score_sources(self, text: str, loc: Locale, suggestions: list[str]) -> tuple[float, dict]:
        cues = self._attribution_cues(loc)
        low = text.lower()
        n_cues = sum(low.count(cue) for cue in cues)
        n_years = len(_YEAR_RE.findall(text))
        raw = n_cues * 30.0 + n_years * 10.0
        score = min(100.0, raw)
        if n_cues == 0:
            suggestions.append(
                "Attribute claims to a source ('according to …', 'a 2023 study found …')."
            )
        return score, {"attribution_cue_count": n_cues, "year_mentions": n_years}

    def _score_entities(self, text: str, suggestions: list[str]) -> tuple[float, dict]:
        # Proper-noun proxy; exclude sentence-initial single words to reduce noise
        # by requiring the match to be either multi-word or not the very start.
        candidates = _PROPER_NOUN_RE.findall(text)
        named = [c for c in candidates if " " in c or len(c) > 3]
        n_named = len(set(named))
        score = min(100.0, n_named * 25.0)
        if n_named == 0:
            suggestions.append("Name authoritative entities/sources (organizations, researchers).")
        return score, {"named_entity_count": n_named}

    def _score_quotable(self, text: str, suggestions: list[str]) -> tuple[float, dict]:
        quotes = _QUOTE_RE.findall(text)
        n_quotes = len(quotes)
        score = min(100.0, 50.0 + n_quotes * 50.0) if n_quotes else 40.0
        if n_quotes == 0:
            suggestions.append("Add a crisp, self-contained quotable statement engines can lift.")
        return score, {"quote_count": n_quotes}

    def _score_clarity(self, sents: list[str], suggestions: list[str]) -> tuple[float, dict]:
        if not sents:
            suggestions.append("Add clear, standalone claim sentences.")
            return 0.0, {"avg_sentence_len": 0.0}
        avg_len = sum(len(words(s)) for s in sents) / len(sents)
        # Clear claims are self-contained but not sprawling: ~8–24 words ideal.
        if 8 <= avg_len <= 24:
            score = 100.0
        elif avg_len < 8:
            score = 100.0 * (avg_len / 8.0)
        else:
            score = max(30.0, 100.0 * (24.0 / avg_len))
            suggestions.append("Break long sentences into standalone, quotable claims.")
        return score, {"avg_sentence_len": round(avg_len, 2)}

    # --- helpers -----------------------------------------------------------

    def _attribution_cues(self, loc: Locale) -> tuple[str, ...]:
        for cand in loc.fallbacks():
            if cand.language in _ATTRIBUTION_CUES:
                return _ATTRIBUTION_CUES[cand.language]
        return _ATTRIBUTION_CUES["und"]
