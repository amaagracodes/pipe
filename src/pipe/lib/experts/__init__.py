"""pipe.lib.experts — domain-expertise pipes and the polymorphism framework.

Built on :mod:`pipe.lib.core`. Two things live here:

  * **The generic expert framework** — a ``java.util.function``-style set of
    typed, overridable functional interfaces layered on
    :class:`~pipe.lib.core.Pipe`:

      - :class:`Expert` ``[I, O]`` — the single-input/single-output root
        (``Function<I, O>``), plus the sibling shapes :class:`Supplier` ``[O]``,
        :class:`Consumer` ``[I]`` and :class:`BiExpert` ``[I, I2, O]``.
      - :class:`AIBasedExpert` ``[I, O]`` — the prompt-driven, provider-backed
        specialization: subclass it with a ``specification`` and you have a
        working expert in one line.

  * **Concrete/generic pipes and the assembler** — the :class:`ExpertPipe`
    interface, generic transforms (:class:`Redactor`, :class:`Annotator`,
    :class:`SeverityGate`), the :class:`Workflow` assembler, and the
    :mod:`~pipe.lib.experts.legal` domain package.
"""

from pipe.lib.experts import legal
from pipe.lib.experts.ai import AIBasedExpert
from pipe.lib.experts.base import BiExpert, Consumer, Expert, Supplier
from pipe.lib.experts.generic import Annotator, Redactor, SeverityGate
from pipe.lib.experts.interface import ExpertPipe
from pipe.lib.experts.workflow import Workflow

__all__ = [
    # functional-interface framework
    "Expert",
    "Supplier",
    "Consumer",
    "BiExpert",
    "AIBasedExpert",
    # interface + generic transforms
    "ExpertPipe",
    "Redactor",
    "Annotator",
    "SeverityGate",
    # assembler + domain
    "Workflow",
    "legal",
]
