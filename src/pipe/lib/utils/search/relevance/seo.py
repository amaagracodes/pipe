"""pipe.lib.utils.search.relevance.seo — Search Engine Optimization analyzer.

``SEOAnalyzer`` scores a piece of content for *classic* search-engine
optimization: does it use its target keywords well, are the title/meta lengths
in the ranges search engines display, does it use headings, is it readable, and
does it link out. Pure and deterministic — no network, no external API.

The score is a documented, fixed-weight blend of component sub-scores so the
same input always yields the same report. Locale-aware: readability thresholds
carry a language note (see :mod:`._common`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pipe.lib.core import Pipe
from pipe.lib.shared import Locale, Prediction

from pipe.lib.utils.search.relevance._common import (
    clamp_score,
    readability_note,
    resolve_locale,
    sentences,
    words,
)

if TYPE_CHECKING:
    pass

__all__ = ["SEOAnalyzer"]

# Component weights (sum = 100). Documented and fixed so scoring is deterministic.
_W_KEYWORDS = 30.0
_W_TITLE_META = 20.0
_W_HEADINGS = 15.0
_W_READABILITY = 20.0
_W_LINKS = 15.0

# Heuristic thresholds (search-display conventions).
_TITLE_MIN, _TITLE_MAX = 30, 60          # characters
_META_MIN, _META_MAX = 70, 160           # characters
_KW_DENSITY_LOW, _KW_DENSITY_HIGH = 0.005, 0.025   # 0.5%–2.5% ideal band
_IDEAL_SENT_LEN = 20.0                     # words/sentence (alphabetic prose)
_IDEAL_WORD_LEN = 5.0                      # characters/word


class SEOAnalyzer(Pipe):
    """Score content for classic Search Engine Optimization → ``dict`` report.

    Input: ``str | Document | Prediction`` (coerced via ``Prediction.of``).
    Optional ``keywords`` (constructor) are the target terms to look for; an
    optional ``locale`` (call arg) overrides locale resolution.

    Output: a ``dict`` report::

        {
          "score": float,                 # 0–100 overall (weighted blend)
          "locale": str,                  # resolved BCP-47 tag
          "components": {                 # each 0–100
            "keywords": float, "title_meta": float, "headings": float,
            "readability": float, "links": float,
          },
          "metrics": {...},               # raw counts used for scoring
          "suggestions": [str, ...],      # actionable, ordered fixes
        }

    Component weights (fixed, sum 100): keywords 30, title/meta 20, headings 15,
    readability 20, links 15. Deterministic: identical input → identical report.
    """

    def __init__(
        self,
        keywords: "list[str] | None" = None,
        *,
        name: str | None = None,
    ) -> None:
        super().__init__(name=name)
        # Normalize target keywords to lowercase once.
        self.keywords: list[str] = [k.strip().lower() for k in (keywords or []) if k.strip()]

    def forward(
        self,
        data: "str | Prediction",
        *,
        locale: "str | Locale | None" = None,
    ) -> dict:
        pred = Prediction.of(data)
        loc = resolve_locale(self, locale, pred)
        text = pred.text
        meta = pred.document.meta or {}

        toks = words(text)
        sents = sentences(text)
        n_words = len(toks)
        suggestions: list[str] = []

        kw_score, kw_metrics = self._score_keywords(toks, n_words, suggestions)
        tm_score, tm_metrics = self._score_title_meta(meta, suggestions)
        hd_score, hd_metrics = self._score_headings(meta, text, suggestions)
        rd_score, rd_metrics = self._score_readability(toks, sents, loc, suggestions)
        ln_score, ln_metrics = self._score_links(meta, text, n_words, suggestions)

        overall = clamp_score(
            kw_score * _W_KEYWORDS / 100.0
            + tm_score * _W_TITLE_META / 100.0
            + hd_score * _W_HEADINGS / 100.0
            + rd_score * _W_READABILITY / 100.0
            + ln_score * _W_LINKS / 100.0
        )

        return {
            "score": overall,
            "locale": loc.tag,
            "components": {
                "keywords": clamp_score(kw_score),
                "title_meta": clamp_score(tm_score),
                "headings": clamp_score(hd_score),
                "readability": clamp_score(rd_score),
                "links": clamp_score(ln_score),
            },
            "metrics": {
                "word_count": n_words,
                "sentence_count": len(sents),
                **kw_metrics,
                **tm_metrics,
                **hd_metrics,
                **rd_metrics,
                **ln_metrics,
            },
            "suggestions": suggestions,
        }

    # --- component scorers (each returns (score_0_100, metrics_dict)) ------

    def _score_keywords(
        self, toks: list[str], n_words: int, suggestions: list[str]
    ) -> tuple[float, dict]:
        if not self.keywords:
            suggestions.append(
                "No target keywords provided; pass keywords=[...] to score keyword usage."
            )
            # Neutral (not penalizing) when no target given.
            return 60.0, {"keyword_density": 0.0, "keywords_present": 0}
        counts = {kw: toks.count(kw) for kw in self.keywords}
        present = sum(1 for c in counts.values() if c > 0)
        total_hits = sum(counts.values())
        density = (total_hits / n_words) if n_words else 0.0

        coverage = present / len(self.keywords)  # fraction of keywords used
        # Density band scoring: ideal in [low, high], degrade outside.
        if density == 0.0:
            density_factor = 0.0
        elif density < _KW_DENSITY_LOW:
            density_factor = density / _KW_DENSITY_LOW
        elif density <= _KW_DENSITY_HIGH:
            density_factor = 1.0
        else:  # keyword stuffing penalty
            density_factor = max(0.0, 1.0 - (density - _KW_DENSITY_HIGH) / _KW_DENSITY_HIGH)

        score = 100.0 * (0.6 * coverage + 0.4 * density_factor)
        if present < len(self.keywords):
            missing = [kw for kw, c in counts.items() if c == 0]
            suggestions.append(f"Add missing target keywords: {', '.join(missing)}.")
        if density > _KW_DENSITY_HIGH:
            suggestions.append("Keyword density is high; reduce repetition to avoid stuffing.")
        elif 0.0 < density < _KW_DENSITY_LOW:
            suggestions.append("Keyword density is low; use target terms a bit more.")
        return score, {
            "keyword_density": round(density, 4),
            "keywords_present": present,
            "keywords_total": len(self.keywords),
        }

    def _score_title_meta(self, meta: dict, suggestions: list[str]) -> tuple[float, dict]:
        title = str(meta.get("title", "") or "")
        description = str(meta.get("description", meta.get("meta_description", "")) or "")
        tl, dl = len(title), len(description)

        title_ok = _TITLE_MIN <= tl <= _TITLE_MAX
        meta_ok = _META_MIN <= dl <= _META_MAX
        score = 0.0
        if title:
            score += 50.0 if title_ok else 25.0
            if not title_ok:
                suggestions.append(
                    f"Title length {tl} chars is outside the {_TITLE_MIN}-{_TITLE_MAX} display range."
                )
        else:
            suggestions.append("Add a <title> (meta['title']) in the 30-60 char range.")
        if description:
            score += 50.0 if meta_ok else 25.0
            if not meta_ok:
                suggestions.append(
                    f"Meta description {dl} chars is outside the {_META_MIN}-{_META_MAX} range."
                )
        else:
            suggestions.append("Add a meta description (meta['description']) in the 70-160 char range.")
        return score, {"title_len": tl, "meta_description_len": dl}

    def _score_headings(self, meta: dict, text: str, suggestions: list[str]) -> tuple[float, dict]:
        # Prefer structured heading metadata; fall back to counting Markdown '#'
        # heading lines in the raw text.
        headings = meta.get("headings")
        if isinstance(headings, (list, tuple)):
            n_headings = len(headings)
        else:
            n_headings = sum(1 for line in text.splitlines() if line.lstrip().startswith("#"))
        if n_headings == 0:
            suggestions.append("Add headings (H1/H2) to structure the content.")
            score = 0.0
        elif n_headings == 1:
            score = 60.0
            suggestions.append("Add sub-headings (H2/H3) to break up sections.")
        else:
            score = 100.0
        return score, {"heading_count": n_headings}

    def _score_readability(
        self, toks: list[str], sents: list[str], loc: Locale, suggestions: list[str]
    ) -> tuple[float, dict]:
        note = readability_note(loc)
        if not toks or not sents:
            suggestions.append("Content too short to assess readability.")
            return 0.0, {"avg_sentence_len": 0.0, "avg_word_len": 0.0, "readability_note": note}
        avg_sent = len(toks) / len(sents)
        avg_word = sum(len(t) for t in toks) / len(toks)
        # Closeness to ideals; deviation degrades linearly.
        sent_factor = max(0.0, 1.0 - abs(avg_sent - _IDEAL_SENT_LEN) / _IDEAL_SENT_LEN)
        word_factor = max(0.0, 1.0 - abs(avg_word - _IDEAL_WORD_LEN) / _IDEAL_WORD_LEN)
        score = 100.0 * (0.6 * sent_factor + 0.4 * word_factor)
        if avg_sent > _IDEAL_SENT_LEN * 1.5:
            suggestions.append("Sentences are long; shorten them for readability.")
        return score, {
            "avg_sentence_len": round(avg_sent, 2),
            "avg_word_len": round(avg_word, 2),
            "readability_note": note,
        }

    def _score_links(
        self, meta: dict, text: str, n_words: int, suggestions: list[str]
    ) -> tuple[float, dict]:
        links = meta.get("links")
        if isinstance(links, (list, tuple)):
            n_links = len(links)
        else:
            # Count Markdown links [..](..) and bare http(s) URLs.
            import re as _re

            n_links = len(_re.findall(r"\]\((?:https?:)?//?[^)]+\)", text)) + len(
                _re.findall(r"(?<!\()\bhttps?://\S+", text)
            )
        # Reward at least one link per ~200 words, cap at full marks.
        target = max(1, n_words // 200)
        score = 100.0 * min(1.0, n_links / target) if target else 0.0
        if n_links == 0:
            suggestions.append("Add relevant links (internal or authoritative external).")
        return score, {"link_count": n_links}
