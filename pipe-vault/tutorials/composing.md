# Composing a pipeline

TODO: put ops together with `>>`, and supply cross-cutting data via ambient
context.

## Chain ops

```python
pipeline = DetectPII("us") >> Redact()
pipeline("call me at 555-123-4567")
```

TODO: how chaining flattens; output of each stage feeds the next.

## Ambient context

```python
with pipe.Pipe.context(LegalRequestContext(jurisdiction="us/ny")):
    result = pipeline(text)
```

TODO: why context beats threading arguments through every op.
