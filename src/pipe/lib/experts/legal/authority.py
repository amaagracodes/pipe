"""pipe.lib.experts.legal.authority — the legal source hierarchy, as ranks.

Authority is a plain integer rank used by the generic
:class:`~pipe.lib.shared.ScopedRegistry` to order/override rules. It encodes the
classic hierarchy of legal sources: a constitution outranks a statute, which
outranks a regulation, which outranks a local ordinance. Higher wins.

This is *data*, not engine logic — a different domain would define its own
ranks (or none). Kept small and explicit so the catalog reads clearly.
"""

from __future__ import annotations

from enum import IntEnum

__all__ = ["Authority"]


class Authority(IntEnum):
    """Rank of a legal source (higher overrides lower on the same subject)."""

    LOCAL = 10          # municipal / city ordinance
    SUBNATIONAL = 20    # state / province / union-territory law
    NATIONAL = 30       # federal / union statute
    SUPRANATIONAL = 40  # e.g. EU regulation over member states
    CONSTITUTIONAL = 50  # constitutional / supreme
