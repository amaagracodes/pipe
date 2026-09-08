"""pipe.lib.core.context — ambient RequestContext plumbing for pipes.

A thread-local (and async-task-local, via :mod:`contextvars`) stack of the
current :class:`~pipe.lib.shared.context.RequestContext`. Entered with the
``Pipe.context(...)`` context manager; read by any pipe running inside the block
— including deeply nested pipes in a :class:`Chain` — without being passed
anything. This mirrors DSPy's ``settings.context`` pattern.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, TypeVar

if TYPE_CHECKING:
    from pipe.lib.shared.context import RequestContext

__all__ = ["current_context", "use_context", "require_context"]

_current: contextvars.ContextVar["RequestContext | None"] = contextvars.ContextVar(
    "pipe_request_context", default=None
)

C = TypeVar("C")


def current_context() -> "RequestContext | None":
    """The ambient context for this thread/task, or ``None`` if unset."""
    return _current.get()


@contextmanager
def use_context(ctx: "RequestContext") -> "Iterator[RequestContext]":
    """Set ``ctx`` as ambient for the duration of the ``with`` block."""
    token = _current.set(ctx)
    try:
        yield ctx
    finally:
        _current.reset(token)


def require_context(kind: type[C]) -> C:
    """Return the ambient context, asserting it is (a subclass of) ``kind``.

    Raises a clear error if no context is set, if it is the wrong type, or if
    the context's own ``require()`` validation fails. This is how a domain
    handler demands the context it needs.
    """
    ctx = _current.get()
    if ctx is None:
        raise LookupError(
            f"no RequestContext set; wrap the call in "
            f"`with Pipe.context({kind.__name__}(...)): ...`"
        )
    if not isinstance(ctx, kind):
        raise TypeError(
            f"expected {kind.__name__} in context, got {type(ctx).__name__}"
        )
    return ctx.require()  # type: ignore[return-value,attr-defined]
