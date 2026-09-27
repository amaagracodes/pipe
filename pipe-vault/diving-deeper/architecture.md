# Architecture

TODO (KT): the big picture. How the pieces fit — the pure `pipe.lib` core, the
`pipe.api` serving adapter, and why they are separated (same core as a library
or served at the edge, no rewrite).

## Layers

TODO (KT): describe the layering, borrowed from DSPy.

- **Structural layer** — `BasePipe` / `PipeMeta`: how pipes are discovered,
  named, and deep-copied (`named_pipes`, `pipes`, `deepcopy`).
- **Behavioural layer** — `Pipe`: the calling convention
  (`__call__`/`acall`/`astream`) and composition (`then` / `>>`).
- **Serving layer** — `pipe.api`: thin async handlers over the core.

## Package map

| Package | Responsibility |
| --- | --- |
| `pipe.lib.core` | TODO: BasePipe, Pipe, Chain, context, ops |
| `pipe.lib.shared` | TODO: types, jurisdiction, scope, registry, locale, context |
| `pipe.lib.detectors` | TODO: pattern-driven detection |
| `pipe.lib.experts` | TODO: domain expertise (generic, workflow, legal) |
| `pipe.lib.providers` | TODO: external-service-wrapping pipes |
| `pipe.lib.utils` | TODO: pure finance / geo / search / flow pipes |
| `pipe.api` | TODO: FastAPI app, routes, server, dev |

## Design tenets

1. TODO (KT): atomic over monolithic — one op does one thing.
2. TODO (KT): sequencing lives only in `Chain`.
3. TODO (KT): cross-cutting data travels ambiently, not through signatures.
4. TODO (KT): one uniform envelope (`Prediction`) so ops compose.
