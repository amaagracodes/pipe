# Pipes and chains in depth

TODO (KT): the mechanics behind the programming model — the level of detail a
new maintainer needs.

## The Pipe lifecycle

TODO (KT): `PipeMeta.__call__` runs `Pipe._base_init` before a subclass
`__init__`, so `name` always exists. Why the metaclass, and what invariants it
guarantees.

## Calling convention

TODO (KT): why you never call `forward` directly.

| Call | Runs | Notes |
| --- | --- | --- |
| `pipe(x)` | `forward` | sync |
| `await pipe.acall(x)` | `aforward` | defaults to running `forward` |
| `pipe.astream(x)` | `stream` | incremental |

## Composition and flattening

TODO (KT): how `>>` / `then` build a `Chain`, and how chaining **flattens** so
`a >> b >> c` is a single three-stage chain (not nested). How `Chain.forward`,
`aforward`, and `stream` execute stages (all-but-last via `acall`, tail
streamed).

```python
pipeline = DetectPII("us") >> Redact()
```

## Nested pipes and discovery

TODO (KT): how `named_pipes()` walks one level of `__dict__` (lists, tuples,
dicts) to discover sub-pipes with dotted/indexed names like `stages[0]`.
