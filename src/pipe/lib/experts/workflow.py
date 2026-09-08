"""pipe.lib.experts.workflow — the generic workflow assembler.

A :class:`Workflow` is a *named* :class:`~pipe.lib.core.Chain`: an ordered
assembly of pipes given an identity and, optionally, a description. It stays a
plain ``Pipe`` — so a workflow can itself be a stage in a larger workflow, be
streamed, and be introspected.

This is the generic building block the domain presets use: a legal workflow is
nothing more than a ``Workflow`` constructed from generic detectors and
transforms configured with legal patterns.
"""

from __future__ import annotations

from pipe.lib.core import Chain, Pipe

__all__ = ["Workflow"]


class Workflow(Chain):
    """An ordered, named assembly of pipes (data in at the top, out the bottom).

    ``Workflow("contract_review", detect, redact, annotate)`` behaves like any
    pipe: call it, stream it, or nest it. Presets return one of these so callers
    get a self-describing, chainable object rather than a bare function.
    """

    def __init__(self, name: str, *stages: Pipe, description: str = "") -> None:
        super().__init__(*stages, name=name)
        self.description = description

    def describe(self) -> dict:
        """A small, serializable summary of the workflow's shape."""
        return {
            "name": self.name,
            "description": self.description,
            "stages": [type(s).__name__ for s in self.stages],
        }

    def __repr__(self) -> str:
        stages = " >> ".join(type(s).__name__ for s in self.stages)
        return f"Workflow(name={self.name!r}, stages=[{stages}])"
