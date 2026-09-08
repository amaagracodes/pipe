"""pipe.lib.shared.scope — generic applicability scope + scoped payloads.

A :class:`Scope` describes *where and under what conditions* something applies.
It pairs a territorial :class:`~pipe.lib.shared.jurisdiction.Jurisdiction` with
**facet filters** — required key→value(s) that a query's facets must satisfy.
This is what lets one rule say "applies anywhere in India, but only for the
``family`` domain and ``hindu`` personal law" without the engine knowing what
"family" or "hindu" mean.

A :class:`Scoped` wraps any payload (a rule, a keyword list, a whole workflow)
with a scope and an integer ``authority`` rank, so a resolver can decide which
of several applicable items wins (defeasible priority: more specific / higher
authority overrides). Generic over the payload type — reusable for any domain.

stdlib only, immutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Mapping, TypeVar

from pipe.lib.shared.jurisdiction import ANY, Jurisdiction

__all__ = ["Scope", "Scoped"]

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Scope:
    """Applicability condition: a territory plus facet filters.

    ``where`` is the (possibly broad) jurisdiction this applies within.
    ``facet_filters`` maps a facet key to the set of acceptable values; a query
    matches only if, for every filtered key, the query supplies one of the
    accepted values. Keys absent from ``facet_filters`` are unconstrained.

        Scope.of("in", domain={"family"}, personal_law={"hindu", "muslim"})

    A bare ``Scope()`` is universal — matches every query.
    """

    where: Jurisdiction = ANY
    facet_filters: Mapping[str, frozenset[str]] = field(default_factory=dict)

    @classmethod
    def of(cls, where: str | Jurisdiction = "", **filters: "str | set[str] | frozenset[str] | list[str] | tuple[str, ...]") -> "Scope":
        """Convenience builder: ``Scope.of("in/mh", domain="family")``.

        Each filter value may be a single string or any iterable of strings;
        all are normalized to a lowercased ``frozenset``.
        """
        juris = where if isinstance(where, Jurisdiction) else Jurisdiction.parse(where)
        norm: dict[str, frozenset[str]] = {}
        for key, val in filters.items():
            values = [val] if isinstance(val, str) else list(val)
            cleaned = frozenset(str(v).strip().lower() for v in values if str(v).strip())
            if cleaned:
                norm[str(key).strip().lower()] = cleaned
        return cls(where=juris, facet_filters=norm)

    # --- matching ---------------------------------------------------------

    def matches(self, query: Jurisdiction) -> bool:
        """True if this scope applies to ``query``.

        Two conditions, both required:
          1. territorial: ``self.where`` must contain ``query`` (a broad scope
             applies to the narrower place being asked about), and
          2. facets: for every filtered facet key, ``query`` must carry a value
             in the accepted set. A query missing a filtered key does not match.
        """
        if not self.where.contains(query):
            return False
        for key, accepted in self.facet_filters.items():
            qv = query.facets.get(key)
            if qv is None or qv not in accepted:
                return False
        return True

    @property
    def specificity(self) -> tuple[int, int]:
        """Ranking key: (territorial depth, number of facet constraints).

        Deeper territory and more facet constraints = more specific, so a
        city-level or facet-qualified rule outranks a country-wide generic one.
        """
        return (self.where.depth, len(self.facet_filters))


@dataclass(frozen=True, slots=True)
class Scoped(Generic[T]):
    """A payload tagged with the scope in which it applies and its authority.

    ``authority`` is an explicit rank (e.g. constitution > statute > regulation
    > ordinance) used to break ties among items of *equal specificity*. Overall
    resolution is specificity-first (see :attr:`rank`): a more local/facet-
    qualified item wins over a broader one; authority decides only when two
    items are equally specific.
    """

    scope: Scope
    payload: T
    authority: int = 0

    def applies_to(self, query: Jurisdiction) -> bool:
        return self.scope.matches(query)

    @property
    def rank(self) -> tuple[int, int, int]:
        """Sort key for resolution: (territory depth, facet count, authority).

        Sorted descending, this puts the most *specific* item first — a rule
        registered for a narrower territory or with more facet constraints wins
        over a broader one addressing the same subject (lex specialis: a local
        ordinance refines the law within its territory). ``authority`` breaks
        ties only among items at the *same* specificity — there a
        higher-authority source (e.g. constitutional over statutory) prevails.
        """
        depth, facets = self.scope.specificity
        return (depth, facets, self.authority)
