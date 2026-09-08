"""pipe.lib.utils.search.relevance.aeo — Answer Engine Optimization analyzer.

``AEOAnalyzer`` scores content for its chance of being the *extracted direct
answer* an answer engine surfaces — Google AI Overviews, featured snippets, and
voice assistants. That favors clear question→answer structure, concise lead
answers, extractable facts, and skimmable list/table/FAQ signals. Pure and
deterministic — no network.

Locale-aware: question detection recognizes interrogatives across several
languages so the heuristic isn't English-only.
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

__all__ = ["AEOAnalyzer"]

# Component weights (sum = 100). Fixed + documented for determinism.
_W_QA = 30.0
_W_CONCISE = 25.0
_W_FACTS = 20.0
_W_STRUCTURE = 25.0

# Concise lead-answer band (words in the first sentence). Snippets/voice favor
# ~40 words or fewer for the direct answer.
_LEAD_IDEAL_MAX = 40
_LEAD_HARD_MAX = 60

# Interrogatives across languages (extend per locale as the platform grows).
_QUESTION_WORDS = {
    "und": ("what", "why", "how", "when", "where", "who", "which", "is", "are", "can", "does", "do"),
    "en": ("what", "why", "how", "when", "where", "who", "which", "is", "are", "can", "does", "do"),
    "es": ("qué", "por qué", "cómo", "cuándo", "dónde", "quién", "cuál"),
    "fr": ("quoi", "pourquoi", "comment", "quand", "où", "qui", "quel", "quelle"),
    "de": ("was", "warum", "wie", "wann", "wo", "wer", "welche", "welcher"),
    "hi": ("क्या", "क्यों", "कैसे", "कब", "कहां", "कहाँ", "कौन", "कौनसा"),
    "pt": ("o que", "por que", "como", "quando", "onde", "quem", "qual"),
}

# Multi-script question marks (Latin '?', Arabic '؟', full-width '？').
_QMARK_RE = re.compile(r"[?؟？]")
_NUMBER_RE = re.compile(r"\b\d[\d,\.]*\b|\b\d+%")


class AEOAnalyzer(Pipe):
    """Score content for Answer Engine Optimization → ``dict`` report.

    Input: ``str | Document | Prediction`` (coerced via ``Prediction.of``).
    Optional ``locale`` (call arg) overrides locale resolution.

    Output ``dict``::

        {
          "score": float,               # 0–100 overall (weighted blend)
          "locale": str,
          "components": {               # each 0–100
            "qa_structure": float, "conciseness": float,
            "facts": float, "structure_signals": float,
          },
          "metrics": {...},
          "suggestions": [str, ...],
        }

    Component weights (fixed, sum 100): qa_structure 30, conciseness 25, facts
    20, structure_signals 25. Deterministic.
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

        qa_score, qa_metrics = self._score_qa(text, sents, loc, suggestions)
        cs_score, cs_metrics = self._score_conciseness(sents, suggestions)
        ft_score, ft_metrics = self._score_facts(text, suggestions)
        st_score, st_metrics = self._score_structure(text, suggestions)

        overall = clamp_score(
            qa_score * _W_QA / 100.0
            + cs_score * _W_CONCISE / 100.0
            + ft_score * _W_FACTS / 100.0
            + st_score * _W_STRUCTURE / 100.0
        )

        return {
            "score": overall,
            "locale": loc.tag,
            "components": {
                "qa_structure": clamp_score(qa_score),
                "conciseness": clamp_score(cs_score),
                "facts": clamp_score(ft_score),
                "structure_signals": clamp_score(st_score),
            },
            "metrics": {
                "sentence_count": len(sents),
                **qa_metrics,
                **cs_metrics,
                **ft_metrics,
                **st_metrics,
            },
            "suggestions": suggestions,
        }

    # --- component scorers -------------------------------------------------

    def _question_words(self, loc: Locale) -> tuple[str, ...]:
        # Walk the locale fallback chain so 'es-MX' → 'es' → 'und'.
        for cand in loc.fallbacks():
            if cand.language in _QUESTION_WORDS:
                return _QUESTION_WORDS[cand.language]
        return _QUESTION_WORDS["und"]

    def _score_qa(
        self, text: str, sents: list[str], loc: Locale, suggestions: list[str]
    ) -> tuple[float, dict]:
        qwords = self._question_words(loc)
        n_qmarks = len(_QMARK_RE.findall(text))
        # A question sentence: ends with '?' or opens with an interrogative.
        q_sents = 0
        for s in sents:
            low = s.lower()
            if _QMARK_RE.search(s) or any(low.startswith(qw) for qw in qwords):
                q_sents += 1
        # Detect an answer immediately following a question. The sentence
        # splitter consumes the '?' terminator, so a "question sentence" here is
        # identified by an interrogative opener (or a residual '?'); an "answer"
        # is the next sentence that is not itself a question.
        def _is_question(s: str) -> bool:
            low = s.lower()
            return bool(_QMARK_RE.search(s)) or any(low.startswith(qw) for qw in qwords)

        has_answer_after_q = False
        for i, s in enumerate(sents[:-1]):
            if _is_question(s):
                nxt = sents[i + 1]
                if not _is_question(nxt) and len(words(nxt)) > 0:
                    has_answer_after_q = True
                    break
        score = 0.0
        if q_sents:
            score += 55.0
        else:
            suggestions.append("Pose the target question explicitly (e.g. 'What is X?').")
        if has_answer_after_q:
            score += 45.0
        elif q_sents:
            suggestions.append("Follow each question immediately with a direct answer sentence.")
        return score, {"question_count": q_sents, "question_marks": n_qmarks}

    def _score_conciseness(self, sents: list[str], suggestions: list[str]) -> tuple[float, dict]:
        if not sents:
            suggestions.append("Add a concise lead answer sentence.")
            return 0.0, {"lead_answer_words": 0}
        lead_words = len(words(sents[0]))
        if lead_words == 0:
            score = 0.0
        elif lead_words <= _LEAD_IDEAL_MAX:
            score = 100.0
        elif lead_words <= _LEAD_HARD_MAX:
            score = 100.0 * (1.0 - (lead_words - _LEAD_IDEAL_MAX) / (_LEAD_HARD_MAX - _LEAD_IDEAL_MAX))
        else:
            score = 20.0
            suggestions.append(
                f"Lead answer is {lead_words} words; tighten to ~{_LEAD_IDEAL_MAX} for snippets/voice."
            )
        return score, {"lead_answer_words": lead_words}

    def _score_facts(self, text: str, suggestions: list[str]) -> tuple[float, dict]:
        n_numbers = len(_NUMBER_RE.findall(text))
        # Extractable facts proxy: presence of concrete numeric/date facts.
        if n_numbers == 0:
            score = 30.0
            suggestions.append("Add concrete, extractable facts (numbers, dates, quantities).")
        elif n_numbers < 3:
            score = 70.0
        else:
            score = 100.0
        return score, {"numeric_fact_count": n_numbers}

    def _score_structure(self, text: str, suggestions: list[str]) -> tuple[float, dict]:
        lines = text.splitlines()
        list_items = sum(
            1 for ln in lines if re.match(r"\s*(?:[-*+]|\d+[.)])\s+", ln)
        )
        has_table = "|" in text and any(ln.count("|") >= 2 for ln in lines)
        has_faq = bool(re.search(r"\bFAQ\b|frequently asked", text, re.IGNORECASE))
        score = 0.0
        if list_items >= 2:
            score += 50.0
        else:
            suggestions.append("Use a bulleted/numbered list for skimmable, extractable points.")
        if has_table:
            score += 25.0
        if has_faq:
            score += 25.0
        if not has_faq and not has_table:
            suggestions.append("Consider an FAQ or comparison table for structured answers.")
        return score, {
            "list_item_count": list_items,
            "has_table": has_table,
            "has_faq": has_faq,
        }
