# Library

TODO: the importable surface. `import pipe` for the flat entry points; the
richer capabilities live under `pipe.lib.*`. This is where the capability
detail lives.

## Core

TODO: `Pipe`, `Chain`, and the flat helpers (`echo`, `echo_stream`).

```python
import pipe

pipe.echo("hi")
```

## Experts

TODO: `pipe.lib.experts` — the domain-expertise ops. Legal today (`DetectPII`,
`SpotClauses`, `ExtractCitations`, `IdentifyStatutes`, `ScreenPrivilege`,
`Redact`); more domains to come.

## Providers

TODO: `pipe.lib.providers` — external-service-wrapping pipes (`OpenRouterProvider`,
`STT`, `FxRates`, `Weather`, `Geocode`, `Flights`, `SatelliteEmbedding`).

## Utilities

TODO: `pipe.lib.utils` — pure pipes for finance, geo, search relevance, and flow
combinators.

## Shared types

TODO: `pipe.lib.shared` — the `Prediction` envelope, `Jurisdiction`, `Scope`,
`Locale`, and request-context types.
