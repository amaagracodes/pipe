"""pipe.lib.core — the interface primitives for atomic ops.

A modular, DSPy-shaped module system split across small files:

  * :mod:`~pipe.lib.core.base`  — ``BasePipe`` (structural) + ``PipeMeta``.
  * :mod:`~pipe.lib.core.pipe`  — ``Pipe``, the atomic callable interface.
  * :mod:`~pipe.lib.core.chain` — ``Chain``, the composite that sequences ops.
  * :mod:`~pipe.lib.core.ops`   — concrete ops (``Echo``, ``EchoStream``) and
    the flat ``echo`` / ``echo_stream`` function API.
"""

from pipe.lib.core.base import BasePipe, PipeMeta
from pipe.lib.core.chain import Chain
from pipe.lib.core.context import current_context, require_context, use_context
from pipe.lib.core.ops import Echo, EchoStream, echo, echo_stream
from pipe.lib.core.pipe import Pipe

__all__ = [
    "BasePipe",
    "PipeMeta",
    "Pipe",
    "Chain",
    "Echo",
    "EchoStream",
    "echo",
    "echo_stream",
    "current_context",
    "use_context",
    "require_context",
]
