"""pipe.lib.experts — domain-expertise pipes and the workflow assembler.

Built on :mod:`pipe.lib.core`. Exposes the :class:`ExpertPipe` interface,
generic transform pipes (:class:`Redactor`, :class:`Annotator`,
:class:`SeverityGate`), the generic :class:`Workflow` assembler, and the
:mod:`~pipe.lib.experts.legal` domain package (atomic legal operations).
"""

from pipe.lib.experts import legal
from pipe.lib.experts.generic import Annotator, Redactor, SeverityGate
from pipe.lib.experts.interface import ExpertPipe
from pipe.lib.experts.workflow import Workflow

__all__ = ["ExpertPipe", "Redactor", "Annotator", "SeverityGate", "Workflow", "legal"]
