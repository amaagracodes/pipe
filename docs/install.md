# Installation

TODO: one line on install paths.

## Library

TODO: install as a package, import as `pipe`. Requires Python >= 3.11.

```bash
pip install pipe-broker
```

```python
import pipe

pipe.echo("hi")
```

## Serve the API

TODO: how to run the FastAPI adapter locally and in a container.

```bash
# local dev (defaults to 0.0.0.0:8787)
python -m pipe.api.dev
```

!!! info
    TODO: note on `PIPE_ROOT_PATH` for reverse-proxy prefixes, and
    `PIPE_PUBLIC_DIR` for the static frontend location.

## Configuration

| Env var | Purpose | Default |
| --- | --- | --- |
| `PORT` | TODO | `8080` |
| `PIPE_HOST` / `PIPE_PORT` | TODO dev bind | `0.0.0.0` / `8787` |
| `PIPE_ROOT_PATH` | TODO reverse-proxy prefix | *(empty)* |
| `PIPE_PUBLIC_DIR` | TODO static frontend dir | repo `/public` |
| `OPENROUTER_API_KEY` | TODO LLM + STT | *(unset)* |
| `AVIATIONSTACK_API_KEY` | TODO flights provider | *(unset)* |
