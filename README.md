# Pipe

Atomic, data-in/data-out operations for multilingual translation and domain-expertise knowledge export.

The core library lives in `src/pipe` — installable as `pipe-broker`, imported as `pipe`. A thin, stateless API adapter in `src/api` runs as a Cloudflare Python Worker.

Build uses `poetry-core`; dependencies are managed with `uv`.

## Usage

```python
import pipe

pipe.echo("hi")
```
