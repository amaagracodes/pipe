"""pipe.lib.shared.jurisdiction — a generic, hierarchical jurisdiction model.

Law varies at many levels and along several *independent* axes, so a single
flat enum can't express it. Following the jurisdictional-domain / LegalRuleML
literature, a jurisdiction here has two orthogonal parts:

  * a **territorial path** — an ordered containment chain, e.g.
    ``in/mh/mumbai`` or ``us/wa/king/seattle``. Deeper = more specific; a
    shorter path *contains* any path it prefixes.
  * **facets** — non-geographic axes that also select which law applies, e.g.
    ``domain`` (tax, privacy, family), ``personal_law`` (for systems like
    India where community, not geography, picks the rule set), ``court_level``,
    ``language``. Facets are just key→value tags; the engine never hard-codes
    any particular key, so new axes are added as data, not code.

Nothing here is specific to any country. India, the US, the EU, a single city
— all are just different values filling the same generic structure. stdlib
only (Pyodide-safe), immutable values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Mapping

__all__ = ["Jurisdiction", "ANY"]

_SEP = "/"


@dataclass(frozen=True, slots=True)
class Jurisdiction:
    """A point (or region) in the multi-axis jurisdiction space.

    ``path`` is the territorial containment chain from broad to narrow. An empty
    path is the universal jurisdiction (:data:`ANY`) that contains everything.
    ``facets`` carries any additional selecting axes.

    Construct from a string for convenience::

        Jurisdiction.parse("us/wa/king/seattle")
        Jurisdiction.parse("in/mh/mumbai", personal_law="hindu", domain="family")

    Segments are lowercased and separated by ``/`` so codes serialize cleanly
    and compare predictably; interpretation of a segment (country vs state vs
    city) is left to the data — the model only cares about containment order.
    """

    path: tuple[str, ...] = ()
    facets: Mapping[str, str] = field(default_factory=dict)

    # --- construction -----------------------------------------------------

    @classmethod
    def parse(cls, code: str | "Jurisdiction" = "", **facets: str) -> "Jurisdiction":
        """Build from a ``"a/b/c"`` path string plus optional facet kwargs.

        Passing an existing ``Jurisdiction`` returns it with any extra facets
        merged in (kwargs win), so callers can refine a base jurisdiction.
        """
        if isinstance(code, Jurisdiction):
            base = code
            merged = {**base.facets, **_clean_facets(facets)}
            return cls(path=base.path, facets=merged)
        segments = tuple(
            seg for seg in (s.strip().lower() for s in str(code).split(_SEP)) if seg
        )
        return cls(path=segments, facets=_clean_facets(facets))

    def child(self, segment: str) -> "Jurisdiction":
        """Return a more specific jurisdiction one level deeper."""
        return Jurisdiction(path=self.path + (segment.strip().lower(),), facets=dict(self.facets))

    def parent(self) -> "Jurisdiction":
        """Return the enclosing jurisdiction (one level up); ANY at the root."""
        return Jurisdiction(path=self.path[:-1], facets=dict(self.facets))

    def with_facets(self, **facets: str) -> "Jurisdiction":
        """Return a copy with additional/overridden facets."""
        return Jurisdiction(path=self.path, facets={**self.facets, **_clean_facets(facets)})

    # --- territorial containment -----------------------------------------

    @property
    def depth(self) -> int:
        """Number of territorial levels (0 == universal / ANY)."""
        return len(self.path)

    @property
    def code(self) -> str:
        """The territorial path as an ``"a/b/c"`` string (``""`` for ANY)."""
        return _SEP.join(self.path)

    def contains(self, other: "Jurisdiction") -> bool:
        """True if ``self`` territorially encloses ``other``.

        A jurisdiction contains another when its path is a prefix of the other's
        (``us`` contains ``us/wa`` contains ``us/wa/king/seattle``). ANY (empty
        path) contains everything. Facets are handled separately by
        :class:`~pipe.lib.shared.scope.Scope`, not here.
        """
        if self.depth > other.depth:
            return False
        return other.path[: self.depth] == self.path

    def is_within(self, other: "Jurisdiction") -> bool:
        """True if ``self`` is territorially inside (or equal to) ``other``."""
        return other.contains(self)

    def common_prefix_depth(self, other: "Jurisdiction") -> int:
        """How many leading territorial levels ``self`` and ``other`` share."""
        n = 0
        for a, b in zip(self.path, other.path):
            if a != b:
                break
            n += 1
        return n

    # --- niceties ---------------------------------------------------------

    def __iter__(self) -> Iterator[str]:
        return iter(self.path)

    def __str__(self) -> str:
        if not self.facets:
            return self.code or "any"
        facets = ",".join(f"{k}={v}" for k, v in sorted(self.facets.items()))
        return f"{self.code or 'any'}[{facets}]"


def _clean_facets(facets: Mapping[str, str]) -> dict[str, str]:
    """Normalize facet keys/values: drop empties, lowercase, str-coerce."""
    return {
        str(k).strip().lower(): str(v).strip().lower()
        for k, v in facets.items()
        if k and v is not None and str(v).strip() != ""
    }


#: The universal jurisdiction: empty territorial path, no facets. Contains all.
ANY = Jurisdiction()
