"""pipe.lib.experts.legal — atomic legal operations, jurisdiction-aware.

The domain layer. Each operation is a single :class:`~pipe.lib.core.Pipe`
performing one act a legal professional does (detect PII, spot clauses, extract
citations, screen for privilege, redact), specialized to a target
:class:`~pipe.lib.shared.Jurisdiction` via the scoped :data:`~.catalog.RULES`
registry. Ops are atomic — compose them with ``>>`` when you want a pipeline.

    from pipe.lib.experts.legal import DetectPII, Redact
    pii = DetectPII("us/ny")
    pii("SSN 123-45-6789")                 # detections only
    (DetectPII("us") >> Redact())("...")   # caller composes when desired
"""

from pipe.lib.experts.legal.authority import Authority
from pipe.lib.experts.legal.catalog import RULES, categories
from pipe.lib.experts.legal.operations import (
    DetectPII,
    ExtractCitations,
    IdentifyStatutes,
    Redact,
    ScreenPrivilege,
    SpotClauses,
)

__all__ = [
    "Authority",
    "RULES",
    "categories",
    "DetectPII",
    "SpotClauses",
    "IdentifyStatutes",
    "ExtractCitations",
    "ScreenPrivilege",
    "Redact",
]
