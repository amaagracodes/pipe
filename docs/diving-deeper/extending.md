# Extending Pipe

TODO (KT): the most important KT page — how a new maintainer adds capability
without breaking the model. Recipes, not theory.

## Add a new op

TODO (KT): subclass `Pipe`, implement `forward` (and `aforward`/`stream` if
needed), keep it pure. What to return.

```python
class Upper(pipe.Pipe):
    def forward(self, data: str) -> str:
        return data.upper()
```

## Add a detector

TODO (KT): register `Rule`s and use `RegexDetector` / `KeywordDetector`.
Detectors carry no domain knowledge — they are patterns fed in.

## Add a legal rule / jurisdiction

TODO (KT): register a `Rule` under a `Scope` + `Authority` in the legal
`catalog`; how lex-specialis override works (e.g. refining a national rule at
the state level). How to add a new jurisdiction path or facet.

## Add a provider

TODO (KT): subclass `ProviderPipe`; read keys from env (never log them; `repr`
shows `has_key` only); lazy-import the client; provide sync `forward` +
async `aforward`. How to fail honestly when creds/deps are missing (the
`SatelliteEmbedding` scaffold pattern).

## Add an expert / workflow

TODO (KT): compose existing detectors/transforms into a named `Workflow`
(a `Chain` subclass) with `describe()`. "A legal workflow is nothing more than
a Workflow of generic detectors/transforms configured with legal patterns."

## Expose it over HTTP

TODO (KT): add a thin async handler in `pipe.api.routes` that parses input,
calls the op, and returns output. Keep buffered vs. streaming explicit. This is
how a new op joins the [REST API](../api/rest.md).
