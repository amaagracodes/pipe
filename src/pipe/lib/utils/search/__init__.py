"""pipe.lib.utils.search — search-optimization domain grouping.

Nested under the ``utils`` *purpose* folder (per the structure rule: domain
groupings never become new roots). Holds pure, network-free content-analysis
pipes that score text against modern search-discovery targets.

  * :mod:`~pipe.lib.utils.search.relevance` — analyzer pipes for the three
    modern optimization targets: classic SEO, Answer Engine Optimization (AEO,
    being the extracted answer in AI Overviews / snippets / voice), and
    Generative Engine Optimization (GEO, being *cited* inside LLM answers).

All analyzers are pure (no network), deterministic, and locale-aware so the
platform can internationalize scoring heuristics per language.
"""

from pipe.lib.utils.search.relevance import (
    AEOAnalyzer,
    GEOAnalyzer,
    SEOAnalyzer,
)

__all__ = [
    "SEOAnalyzer",
    "AEOAnalyzer",
    "GEOAnalyzer",
]
