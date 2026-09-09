# REST API — serve the library on your own cloud

TODO: the selling point. Every pipe op you can `import` can also be **served as
an HTTP API on your own infrastructure** — no rewrite. The same pure core runs
as a thin, stateless FastAPI adapter you deploy under your own cloud account.
Your data and keys never leave your environment.

!!! tip "Why serve it yourself"
    TODO: turn any pipe op into an endpoint your services can call, on the go.
    You own the deployment, the keys, the data boundary, and the bill — we don't
    proxy your traffic. Run it at the edge (Cloudflare Python Worker) or as a
    container (Cloud Run, ECS, or any box that runs Python).

## The idea

TODO: the library *is* the API. `pipe.api` is a thin adapter over `pipe.lib` —
each handler parses input, calls one atomic op, and returns the output. Because
the core is pure and stateless, the same code serves a laptop, a container, or
an edge worker. "Same core, no rewrite."

## Serve it

TODO: one command locally; a container image for production.

```bash
# local
python -m pipe.api.dev            # 0.0.0.0:8787

# production ASGI entrypoint (binds $PORT, default 8080)
python -m pipe.api.server
```

TODO: note the config knobs — `PIPE_ROOT_PATH` (reverse-proxy prefix),
`PIPE_PUBLIC_DIR` (static site), `PORT`, `PIPE_HOST`/`PIPE_PORT`, and the
provider keys (`OPENROUTER_API_KEY`, `AVIATIONSTACK_API_KEY`) — all read from
*your* environment.

## Routes

TODO: the endpoints exposed by the adapter. Interactive OpenAPI at `/docs`, raw
spec at `/openapi.json`.

### Ops

| Method | Path | Style | Params | Returns |
| --- | --- | --- | --- | --- |
| `GET` | `/echo` | buffered | `data` | `{ data }` |
| `GET` | `/echo/stream` | streaming | `data`, `chunk_size` | `text/plain` stream |

### LLM & speech

| Method | Path | Style | Params | Returns |
| --- | --- | --- | --- | --- |
| `POST` | `/llm` | buffered | `prompt`, `model`, `max_tokens` | `{ model, prompt, completion }` |
| `POST` | `/stt` | buffered | `file` (multipart), `model`, `language` | `{ model, format, text }` |

### Legal expert

| Method | Path | Style | Params | Returns |
| --- | --- | --- | --- | --- |
| `GET` | `/legal/ops` | buffered | — | `{ operations, categories, rule_count }` |
| `POST` | `/legal/detect` | buffered | `text`, `jurisdiction`, `op` | `{ op, jurisdiction, detections, meta }` |

!!! info
    TODO: `/llm` and `/stt` return shaped 501/503/502 errors when the stack or a
    key is unavailable, so they are safe to probe.

## Deploy targets

TODO: describe the supported deploy targets.

- **Edge** — Cloudflare Python Worker (Pyodide); pure-Python ops run at the edge.
- **Container** — the shipped `Dockerfile` runs on Cloud Run, ECS, Fly, or any
  container host; real CPython, so any dependency works.
- **Anywhere Python runs** — it's just an ASGI app.
