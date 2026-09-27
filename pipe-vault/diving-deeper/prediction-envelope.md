# The Prediction envelope

TODO (KT): the single data structure every domain pipe reads and writes, and
why a uniform envelope is what lets ops compose freely.

## Types

TODO (KT): the frozen dataclasses in `pipe.lib.shared.types` (stdlib only).

| Type | Role |
| --- | --- |
| `Severity` | TODO: INFO … CRITICAL ordering |
| `Span` | TODO: start/end offsets |
| `Detection` | TODO: kind, label, span, severity, meta |
| `Document` | TODO: text + meta + locale (`with_text`, `with_locale`) |
| `Prediction` | TODO: document + detections; the output envelope |

## Reading and writing

TODO (KT): `Prediction.of()` coercion, `with_document`, `add_detections`,
`by_kind`, `max_severity`. How a detector adds detections and a transform
(e.g. `Redactor`, `Annotator`, `SeverityGate`) reads them without mutating text
destructively.

```python
pred = DetectPII("us")("SSN 123-45-6789")
pred.by_kind("pii.ssn")
pred.max_severity()
```
