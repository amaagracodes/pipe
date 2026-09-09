# Streaming

TODO: produce output incrementally instead of buffering.

## The streaming op

```python
import pipe

async for chunk in pipe.echo_stream("stream me", chunk_size=2):
    print(chunk, end="")
```

TODO: how `astream` maps to a `Pipe.stream` generator, and how a `Chain`
streams its tail while running earlier stages buffered.

## Over HTTP

TODO: when served as an API, `GET /echo/stream` returns a `text/plain` stream;
show a small client reading it chunk-by-chunk. See the [REST API](../api/rest.md).
