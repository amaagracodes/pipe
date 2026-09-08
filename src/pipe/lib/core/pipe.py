"""pipe.lib.core.pipe — the atomic, callable interface layer.

``Pipe`` is the behavioural layer that mirrors ``dspy.Module``: it is callable
and routes ``__call__`` to a user-defined ``forward`` (and ``acall`` to
``aforward``), so every subclass is invoked the same way regardless of what it
computes. A ``Pipe`` is the smallest unit of work: data in, data out.

Ops stay atomic (single responsibility); sequencing lives in
:class:`pipe.lib.core.chain.Chain`, reachable via ``>>`` / :meth:`Pipe.then`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator

from pipe.lib.core.base import BasePipe, PipeMeta

if TYPE_CHECKING:
    from pipe.lib.core.chain import Chain
    from pipe.lib.shared.context import RequestContext

__all__ = ["Pipe"]


class Pipe(BasePipe, metaclass=PipeMeta):
    """The atomic op: data in, data out.

    Subclass and implement :meth:`forward` (and optionally :meth:`aforward` /
    :meth:`stream` for async and incremental variants). Never call ``forward``
    directly — invoke the instance, so every ``Pipe`` shares one calling
    convention regardless of what it computes::

        class Upper(Pipe):
            def forward(self, data: str) -> str:
                return data.upper()

        Upper()("hi")            # -> "HI"

    Chain atomic ops so one feeds the next::

        pipeline = Clean() >> Translate() >> Export()
        pipeline("bonjour")      # runs left-to-right

    Compose by holding ``Pipe``s as attributes; :meth:`named_pipes` discovers
    them.
    """

    def _base_init(self) -> None:
        # Set unconditionally by the metaclass, before subclass __init__.
        self.name = type(self).__name__

    def __init__(self, *, name: str | None = None) -> None:
        if name is not None:
            self.name = name
        elif not hasattr(self, "name"):
            self.name = type(self).__name__

    # --- the interface subclasses implement -------------------------------

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        """Synchronous op body. Subclasses must override."""
        raise NotImplementedError(
            f"{type(self).__name__} must implement forward()."
        )

    async def aforward(self, *args: Any, **kwargs: Any) -> Any:
        """Async op body. Defaults to running :meth:`forward`."""
        return self.forward(*args, **kwargs)

    def stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        """Incremental (streaming) op body. Optional; override to support it."""
        raise NotImplementedError(
            f"{type(self).__name__} does not support streaming."
        )

    # --- the single calling convention ------------------------------------

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Invoke the pipe synchronously (routes to :meth:`forward`)."""
        return self.forward(*args, **kwargs)

    async def acall(self, *args: Any, **kwargs: Any) -> Any:
        """Invoke the pipe asynchronously (routes to :meth:`aforward`)."""
        return await self.aforward(*args, **kwargs)

    def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        """Invoke the pipe as a stream (routes to :meth:`stream`)."""
        return self.stream(*args, **kwargs)

    # --- ambient request context ------------------------------------------

    @staticmethod
    def context(ctx: "RequestContext"):
        """Set an ambient :class:`RequestContext` for the ``with`` block.

        Any pipe running inside — including nested pipes in a ``Chain`` — can
        read it via :meth:`ctx` / :meth:`require_context` without being passed
        anything::

            with Pipe.context(FinancialRequestContext(locale="hi-IN", currency="INR")):
                pipeline(data)
        """
        from pipe.lib.core.context import use_context

        return use_context(ctx)

    def ctx(self) -> "RequestContext | None":
        """The ambient context, or ``None`` if none is set."""
        from pipe.lib.core.context import current_context

        return current_context()

    def require_context(self, kind: "type[RequestContext]") -> "RequestContext":
        """Return the ambient context asserting it is ``kind`` (else raise).

        Domain pipes call this to demand the context they need — e.g. a money
        formatter requires a ``FinancialRequestContext`` and errors clearly if
        one wasn't provided.
        """
        from pipe.lib.core.context import require_context

        return require_context(kind)

    # --- chaining: one pipe's output feeds the next -----------------------

    def then(self, other: "Pipe") -> "Chain":
        """Chain ``self`` into ``other``: ``other(self(data))``.

        Returns a composite :class:`Chain` that stays a plain ``Pipe`` — so the
        result can be chained again, invoked, introspected, and copied like any
        atomic op. Each op stays single-purpose; composition lives in ``Chain``.
        """
        from pipe.lib.core.chain import Chain

        if not isinstance(other, Pipe):
            raise TypeError(f"can only chain a Pipe, got {type(other).__name__}")
        # Flatten so ``a >> b >> c`` yields one Chain of three, not nested Chains.
        stages: list[Pipe] = []
        stages += self.stages if isinstance(self, Chain) else [self]
        stages += other.stages if isinstance(other, Chain) else [other]
        return Chain(*stages)

    def __rshift__(self, other: "Pipe") -> "Chain":
        """``pipe_a >> pipe_b`` — sugar for :meth:`then`."""
        return self.then(other)

    # --- introspection helpers --------------------------------------------

    def __repr__(self) -> str:
        nested = self.named_pipes()
        if not nested:
            return f"{type(self).__name__}(name={self.name!r})"
        body = ", ".join(f"{n}={type(p).__name__}" for n, p in nested)
        return f"{type(self).__name__}(name={self.name!r}, {body})"
