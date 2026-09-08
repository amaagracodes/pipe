"""pipe.lib.legal.catalog — legal knowledge as scoped data.

Every rule is registered into a generic
:class:`~pipe.lib.shared.ScopedRegistry` with (a) the :class:`Scope` it applies
in and (b) an :class:`~.authority.Authority` rank. The engine knows nothing
about any of this — it just resolves, by locality + facets + authority, which
rules apply to a given jurisdiction. Adding a country, a state, a city, or a
personal-law community is purely a matter of appending scoped rows here.

Jurisdiction codes follow ISO 3166 / 3166-2 as a hierarchical materialized
path (``us``, ``us/ny``, ``in/mh``); deeper is more specific and a prefix
territorially contains its descendants (the ``ltree`` model, not geo-spatial).

Scopes shown:
  * ``ANY`` — jurisdiction-neutral rules (e.g. an email looks the same anywhere)
  * ``us`` / ``us/ny`` / ``us/wa/king/seattle`` — territorial hierarchy
  * ``in`` / ``in/mh`` with facets ``domain`` and ``personal_law`` — India's
    subject-matter and personal-law axes, expressed generically as facets.

Patterns are pragmatic starting points, not legal advice; tune per matter.
"""

from __future__ import annotations

from pipe.lib.detectors import Rule
from pipe.lib.legal.authority import Authority
from pipe.lib.shared import Scope, ScopedRegistry, Severity

__all__ = ["RULES", "categories"]


#: The single source of truth: a scope-aware registry of detection rules.
RULES: ScopedRegistry[Rule] = ScopedRegistry()


def _add(scope: Scope, rule: Rule, authority: int) -> None:
    RULES.add(scope, rule, authority=authority)


# --- jurisdiction-neutral (ANY) -------------------------------------------
# These match the same everywhere, so they live at the universal scope.
_add(Scope.of(), Rule("pii.email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", Severity.HIGH), Authority.NATIONAL)
_add(Scope.of(), Rule("pii.credit_card", r"\b(?:\d[ -]?){13,16}\b", Severity.CRITICAL), Authority.NATIONAL)
_add(Scope.of(), Rule("clause.confidentiality", r"\bconfidential(?:ity)?\b", Severity.LOW), Authority.NATIONAL)
_add(Scope.of(), Rule("clause.indemnity", r"\bindemnif(?:y|ication|ies)\b", Severity.MEDIUM), Authority.NATIONAL)
_add(Scope.of(), Rule("clause.arbitration", r"\barbitrat(?:ion|e)\b", Severity.MEDIUM), Authority.NATIONAL)
_add(Scope.of(), Rule("clause.force_majeure", r"\bforce majeure\b", Severity.LOW), Authority.NATIONAL)
_add(Scope.of(), Rule("privileged", r"\bprivileged and confidential\b", Severity.HIGH), Authority.NATIONAL)


# --- United States: federal -----------------------------------------------
_add(Scope.of("us"), Rule("pii.ssn", r"\b\d{3}-\d{2}-\d{4}\b", Severity.CRITICAL), Authority.NATIONAL)
_add(Scope.of("us"), Rule("pii.phone", r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", Severity.MEDIUM), Authority.NATIONAL)
_add(Scope.of("us"), Rule("cite.usc", r"\b\d+\s+U\.?S\.?C\.?\s+§?\s?\d+\b", Severity.INFO), Authority.NATIONAL)
_add(Scope.of("us"), Rule("cite.cfr", r"\b\d+\s+C\.?F\.?R\.?\s+§?\s?\d+\b", Severity.INFO), Authority.NATIONAL)
_add(Scope.of("us"), Rule("privileged", r"\battorney[-\s]client privilege\b", Severity.HIGH), Authority.NATIONAL)
_add(Scope.of("us"), Rule("clause.non_compete", r"\bnon[-\s]?compete\b", Severity.MEDIUM), Authority.NATIONAL)

# United States: New York (state refines federal on the same kind) ----------
_add(Scope.of("us/ny"), Rule("cite.reporter_ny", r"\b\d+\s+N\.?Y\.?\s+\d+\b", Severity.INFO), Authority.SUBNATIONAL)
# NY refines the non-compete posture (stricter enforceability) — overrides the
# federal-scope non_compete rule for the same 'clause.non_compete' kind.
_add(Scope.of("us/ny"), Rule("clause.non_compete", r"\bnon[-\s]?compete\b", Severity.HIGH), Authority.SUBNATIONAL)

# United States: Seattle, WA (city-level ordinance example) -----------------
_add(Scope.of("us/wa/king/seattle"), Rule("clause.fair_chance", r"\bfair chance\b", Severity.MEDIUM), Authority.LOCAL)


# --- India: union level ----------------------------------------------------
_add(Scope.of("in"), Rule("pii.aadhaar", r"\b\d{4}\s?\d{4}\s?\d{4}\b", Severity.CRITICAL), Authority.NATIONAL)
_add(Scope.of("in"), Rule("pii.pan", r"\b[A-Z]{5}\d{4}[A-Z]\b", Severity.HIGH), Authority.NATIONAL)
_add(Scope.of("in"), Rule("cite.air", r"\bAIR\s+\d{4}\s+[A-Z]{2,}\s+\d+\b", Severity.INFO), Authority.NATIONAL)

# India: subject-matter (domain facet) — family-law markers -----------------
_add(Scope.of("in", domain="family"), Rule("clause.maintenance", r"\bmaintenance\b", Severity.MEDIUM), Authority.NATIONAL)

# India: personal law by community (personal_law facet), family domain ------
# Same 'statute.marriage_act' kind, different act per community; the facet
# selects which one applies for a given query.
_add(Scope.of("in", domain="family", personal_law="hindu"), Rule("statute.marriage_act", r"\bHindu Marriage Act\b", Severity.MEDIUM), Authority.NATIONAL)
_add(Scope.of("in", domain="family", personal_law="muslim"), Rule("statute.marriage_act", r"\b(?:Muslim Personal Law|Shariat)\b", Severity.MEDIUM), Authority.NATIONAL)
_add(Scope.of("in", domain="family", personal_law="christian"), Rule("statute.marriage_act", r"\bIndian Christian Marriage Act\b", Severity.MEDIUM), Authority.NATIONAL)
_add(Scope.of("in", domain="family", personal_law="secular"), Rule("statute.marriage_act", r"\bSpecial Marriage Act\b", Severity.MEDIUM), Authority.NATIONAL)

# India: Maharashtra state (subnational) ------------------------------------
_add(Scope.of("in/mh"), Rule("clause.stamp_duty", r"\bstamp duty\b", Severity.LOW), Authority.SUBNATIONAL)


def categories(prefix: str = "") -> set[str]:
    """The distinct rule ``kind`` prefixes present in the catalog.

    With no argument, returns the top-level categories (``{"pii", "clause",
    ...}``); with a prefix, the full kinds under it.
    """
    kinds = {sc.payload.kind for sc in RULES}
    if not prefix:
        return {k.split(".", 1)[0] for k in kinds}
    return {k for k in kinds if k.startswith(prefix)}
