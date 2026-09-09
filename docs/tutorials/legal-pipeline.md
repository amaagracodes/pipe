# A legal pipeline

TODO: an end-to-end example — detect and redact PII for a jurisdiction.

!!! warning
    TODO: the legal patterns are pragmatic starting points, not legal advice.

## Detect, then redact

```python
from pipe.lib.experts.legal import DetectPII, Redact

pipeline = DetectPII("us") >> Redact()
pipeline("SSN 123-45-6789")
```

TODO: walk through what each op emits (the `Prediction` envelope), how `Redact`
masks already-detected spans, and how switching the jurisdiction (e.g. `us/ny`)
changes the rules via lex-specialis resolution.

## Over HTTP

TODO: when served as an API, the same op via `POST /legal/detect` with
`op=detect_pii`. See the [REST API](../api/rest.md).
