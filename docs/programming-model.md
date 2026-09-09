# Programming model

TODO: one line — Pipe reproduces DSPy's split of a structural layer and a
behavioural layer.

## Pipe

TODO: a `Pipe` is the atomic callable. Subclasses implement `forward` (sync),
and optionally `aforward` (async) and `stream` (incremental). One calling
convention: `__call__` → forward, `acall` → aforward, `astream` → stream.
Never call `forward` directly.

```python
class Upper(pipe.Pipe):
    def forward(self, data: str) -> str:
        return data.upper()

Upper()("hi")  # 'HI'
```

## Chain

TODO: sequencing lives only in `Chain`. Compose with `>>` (or `.then(...)`);
chaining flattens, so `a >> b >> c` is one chain of three. Output of each stage
feeds the next.

```python
pipeline = DetectPII("us") >> Redact()
pipeline("call me at 555-123-4567")
```

## Ambient context

TODO: cross-cutting request data (locale, jurisdiction, currency, lat/lon)
travels ambiently through a `contextvars` stack instead of every signature.
Enter it with a `with` block.

```python
with pipe.Pipe.context(LegalRequestContext(jurisdiction="us/ny")):
    result = detect(text)
```

## Prediction envelope

TODO: every domain pipe speaks one currency — a `Prediction` wrapping a
`Document` and a list of `Detection`s. Uniform in, uniform out, so ops compose
freely.
