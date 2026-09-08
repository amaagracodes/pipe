"""pipe.lib.utils.search.relevance — content-relevance analyzer pipes.

Pure (no network), deterministic content-analysis :class:`~pipe.lib.core.Pipe`
subclasses scoring text against the three modern search-discovery targets:

  * :class:`SEOAnalyzer` — classic **Search Engine Optimization** (ranking in
    traditional results).
  * :class:`AEOAnalyzer` — **Answer Engine Optimization** (being the extracted
    direct answer in AI Overviews / featured snippets / voice).
  * :class:`GEOAnalyzer` — **Generative Engine Optimization** (being *cited*
    inside LLM answers like ChatGPT / Perplexity / Gemini). GEO here means
    *generative-engine*, NOT geography.

Each analyzer is a single atomic concern: it takes ``str | Document |
Prediction`` (coerced via :meth:`Prediction.of`) and returns a ``dict`` report
with a 0–100 ``"score"``, per-component sub-scores, raw ``"metrics"``, and an
ordered ``"suggestions"`` list. All are locale-aware (explicit arg → Document
locale → ambient RequestContext locale → ``Locale('und')``) so scoring
heuristics can internationalize.
"""

from pipe.lib.utils.search.relevance.aeo import AEOAnalyzer
from pipe.lib.utils.search.relevance.geo import GEOAnalyzer
from pipe.lib.utils.search.relevance.seo import SEOAnalyzer

__all__ = [
    "SEOAnalyzer",
    "AEOAnalyzer",
    "GEOAnalyzer",
]
