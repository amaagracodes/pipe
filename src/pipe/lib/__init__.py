"""pipe.lib — the pure, stateless core: atomic data-in/data-out operations.

Zero runtime dependencies. No I/O, no framework, no global state. Safe to run
anywhere Python does, including Cloudflare's Pyodide runtime.

The interface primitives live in the modular :mod:`pipe.lib.core` subpackage
and are re-exported here for a flat import surface. Two ways to use an op:

  * the interface — subclass :class:`Pipe`, implement ``forward``/``stream``,
    invoke by calling the instance, and chain with ``>>``. This is the
    DSPy-style module pattern: a small, composable, uniformly-called atomic
    layer.
  * the flat helpers — ``echo`` / ``echo_stream`` remain as functions for
    callers that just want data in, data out.
"""

from pipe.lib.core import (
    BasePipe,
    Chain,
    Echo,
    EchoStream,
    Pipe,
    PipeMeta,
    echo,
    echo_stream,
)

__all__ = [
    # interface layer
    "BasePipe",
    "Pipe",
    "PipeMeta",
    "Chain",
    # concrete ops
    "Echo",
    "EchoStream",
    # flat function API
    "echo",
    "echo_stream",
]
