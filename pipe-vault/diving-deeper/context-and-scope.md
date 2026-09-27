# Ambient context, jurisdiction & scope

TODO (KT): the cross-cutting model that makes ops stay atomic — how locale,
jurisdiction, currency, and coordinates reach an op without being passed
through every call.

## RequestContext

TODO (KT): `contextvars`-based stack (thread- and task-local). `use_context`,
`current_context`, `require_context(kind)`. Subtypes: `FinancialRequestContext`
(currency), `LegalRequestContext` (jurisdiction), `GeoRequestContext`
(lat/lon).

```python
with pipe.Pipe.context(LegalRequestContext(jurisdiction="us/ny")):
    result = detect(text)
```

## Jurisdiction

TODO (KT): hierarchical territorial path + orthogonal facets
(`us/wa/king/seattle`, facets like `domain`, `personal_law`). `contains` /
`is_within` prefix containment; `ANY` is universal.

## Scope & the registry

TODO (KT): how `Scope` + `ScopedRegistry` resolve rules by specificity
`(depth, #facets, authority)` with **lex-specialis** dedup — the most specific
applicable rule wins (e.g. NY's non-compete overriding the US default).

## Authority

TODO (KT): `Authority` ordering (LOCAL < SUBNATIONAL < NATIONAL <
SUPRANATIONAL < CONSTITUTIONAL) and where it enters resolution.
