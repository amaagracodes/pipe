"""pipe.lib.shared.registry — a generic, scope-aware resolver.

A :class:`ScopedRegistry` holds :class:`~pipe.lib.shared.scope.Scoped` items and,
given a target :class:`~pipe.lib.shared.jurisdiction.Jurisdiction`, returns the
items that apply — ordered by the defeasible-priority rule from the legal-rules
literature: highest authority first, then most territorially specific, then most
facet-qualified.

It is fully generic over the payload type: register rules, keyword lists,
workflow factories, anything. Nothing here knows about law, PII, or any country
— it only understands scopes and containment.

stdlib only, no global state (each registry is its own instance).
"""

from __future__ import annotations

from typing import Callable, Generic, Iterable, TypeVar

from pipe.lib.shared.jurisdiction import Jurisdiction
from pipe.lib.shared.scope import Scope, Scoped

__all__ = ["ScopedRegistry"]

T = TypeVar("T")


class ScopedRegistry(Generic[T]):
    """A container of scoped payloads with priority-ordered resolution."""

    def __init__(self, items: Iterable[Scoped[T]] = ()) -> None:
        self._items: list[Scoped[T]] = list(items)

    # --- registration -----------------------------------------------------

    def add(self, scope: Scope, payload: T, *, authority: int = 0) -> "ScopedRegistry[T]":
        """Register a payload under a scope; returns self for chaining."""
        self._items.append(Scoped(scope=scope, payload=payload, authority=authority))
        return self

    def extend(self, scoped: Iterable[Scoped[T]]) -> "ScopedRegistry[T]":
        """Register pre-built :class:`Scoped` items."""
        self._items.extend(scoped)
        return self

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    # --- resolution -------------------------------------------------------

    def resolve(self, query: str | Jurisdiction) -> list[Scoped[T]]:
        """Return applicable :class:`Scoped` items, highest priority first.

        Priority = descending ``(authority, territorial depth, facet count)``.
        Ties keep registration order (stable sort), so equally-ranked items are
        all retained rather than one silently shadowing another.
        """
        q = query if isinstance(query, Jurisdiction) else Jurisdiction.parse(query)
        applicable = [it for it in self._items if it.applies_to(q)]
        return sorted(applicable, key=lambda it: it.rank, reverse=True)

    def payloads(self, query: str | Jurisdiction) -> list[T]:
        """Applicable payloads (unwrapped), highest priority first."""
        return [it.payload for it in self.resolve(query)]

    def resolve_by(
        self,
        query: str | Jurisdiction,
        key: Callable[[T], object],
    ) -> list[T]:
        """Applicable payloads with lower-priority duplicates removed.

        For each distinct ``key(payload)`` only the highest-priority payload is
        kept — this is how a specific/local or higher-authority rule *overrides*
        a broader one addressing the same thing (lex specialis). Payloads whose
        key is already claimed by a higher-priority item are dropped.
        """
        seen: set[object] = set()
        out: list[T] = []
        for item in self.resolve(query):
            k = key(item.payload)
            if k in seen:
                continue
            seen.add(k)
            out.append(item.payload)
        return out
