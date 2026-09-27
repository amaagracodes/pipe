---
title: REST API Route Reference
description: Complete, automatically generated route reference for the pipe API.
---

# REST API Route Reference

> [!NOTE] Automated Documentation
> This document is automatically generated from the FastAPI route definitions via `pipe.api.openapi`.
> Any route, parameter, or docstring changes in `src/pipe/api/routes.py` are immediately reflected here.

**API Version:** `0.1.0` | **OpenAPI Version:** `3.1.0`  
**Raw Schemas:** [openapi.json](openapi.json) · [openapi.yaml](openapi.yaml) · **Interactive Docs:** [/docs](http://localhost:8787/docs) · [/redoc](http://localhost:8787/redoc)

---

## Endpoints Overview

| Method | Path | Summary | Tags |
| :--- | :--- | :--- | :--- |
| **`GET`** | [`/echo`](#get-echo) | Echo | `ops` |
| **`GET`** | [`/echo/stream`](#get-echo-stream) | Echo Stream | `ops` |
| **`POST`** | [`/legal/detect`](#post-legal-detect) | Legal Detect | `legal` |
| **`GET`** | [`/legal/ops`](#get-legal-ops) | Legal Ops | `legal` |
| **`POST`** | [`/llm`](#post-llm) | Llm | `llm` |
| **`POST`** | [`/stt`](#post-stt) | Stt | `llm` |

---

## Legal Expert Operations (`legal`)

<h3 id="post-legal-detect"><code>POST</code> <code>/legal/detect</code> — Legal Detect</h3>

Run one atomic legal op over text for a given jurisdiction.

``op`` is one of the names from ``GET /legal/ops``; ``jurisdiction`` is a
hierarchical code like ``us``, ``us/ny``, ``in/mh`` (optionally with
facets appended later). Returns the detections found.

#### Parameters

| Name | In | Type | Required | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `text` | `query` | `string` | ✓ | `—` |  |
| `jurisdiction` | `query` | `string` | — | `us` |  |
| `op` | `query` | `string` | — | `detect_pii` |  |

#### Responses

| Status Code | Description | Schema / Returns |
| :--- | :--- | :--- |
| `200` | Successful Response | `object` |
| `422` | Validation Error | `HTTPValidationError` |

#### Example Request

=== "curl"
    ```bash
    curl -X POST "http://localhost:8787/legal/detect" \
      -H "Content-Type: application/json"
    ```

=== "Python (httpx)"
    ```python
    import httpx

    response = httpx.post("http://localhost:8787/legal/detect")
    print(response.json())
    ```

---

<h3 id="get-legal-ops"><code>GET</code> <code>/legal/ops</code> — Legal Ops</h3>

List the available atomic legal operations and rule categories.

#### Responses

| Status Code | Description | Schema / Returns |
| :--- | :--- | :--- |
| `200` | Successful Response | `object` |

#### Example Request

=== "curl"
    ```bash
    curl -X GET "http://localhost:8787/legal/ops"
    ```

=== "Python (httpx)"
    ```python
    import httpx

    response = httpx.get("http://localhost:8787/legal/ops")
    print(response.json())
    ```

---

## LLM & Speech-to-Text (`llm`)

<h3 id="post-llm"><code>POST</code> <code>/llm</code> — Llm</h3>

Test route: send a prompt to OpenRouter and return the completion.

Reads the key from $OPENROUTER_API_KEY (injected in the deployment).
Returns a 4xx-shaped JSON error rather than a 500 when the LLM stack or
key is unavailable, so it's safe to probe.

#### Parameters

| Name | In | Type | Required | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `prompt` | `query` | `string` | ✓ | `—` |  |
| `model` | `query` | `string` | — | `openai/gpt-4o-mini` |  |
| `max_tokens` | `query` | `integer` | — | `256` |  |

#### Responses

| Status Code | Description | Schema / Returns |
| :--- | :--- | :--- |
| `200` | Successful Response | `object` |
| `422` | Validation Error | `HTTPValidationError` |

#### Example Request

=== "curl"
    ```bash
    curl -X POST "http://localhost:8787/llm" \
      -H "Content-Type: application/json"
    ```

=== "Python (httpx)"
    ```python
    import httpx

    response = httpx.post("http://localhost:8787/llm")
    print(response.json())
    ```

---

<h3 id="post-stt"><code>POST</code> <code>/stt</code> — Stt</h3>

Transcribe an uploaded audio file to text (audio bytes in, text out).

Accepts a multipart file upload; the audio format is inferred from the
filename extension (falls back to ``wav``). Reads the key from
$OPENROUTER_API_KEY. Errors map like /llm (503 missing key, 502 upstream).

#### Parameters

| Name | In | Type | Required | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `model` | `query` | `string` | — | `openai/whisper-large-v3` |  |
| `language` | `query` | `string | null` | — | `—` |  |

#### Request Body

- **Content-Type:** `multipart/form-data`
#### Responses

| Status Code | Description | Schema / Returns |
| :--- | :--- | :--- |
| `200` | Successful Response | `object` |
| `422` | Validation Error | `HTTPValidationError` |

#### Example Request

=== "curl"
    ```bash
    curl -X POST "http://localhost:8787/stt" \
      -F "file=@audio.wav"
    ```

=== "Python (httpx)"
    ```python
    import httpx

    with open("audio.wav", "rb") as f:
        response = httpx.post("http://localhost:8787/stt", files={"file": f})
    print(response.json())
    ```

---

## Core Operations (`ops`)

<h3 id="get-echo"><code>GET</code> <code>/echo</code> — Echo</h3>

Echo atomic op: returns the input unchanged (data in, data out).

#### Parameters

| Name | In | Type | Required | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `data` | `query` | `string` | — | `` |  |

#### Responses

| Status Code | Description | Schema / Returns |
| :--- | :--- | :--- |
| `200` | Successful Response | `object` |
| `422` | Validation Error | `HTTPValidationError` |

#### Example Request

=== "curl"
    ```bash
    curl -X GET "http://localhost:8787/echo"
    ```

=== "Python (httpx)"
    ```python
    import httpx

    response = httpx.get("http://localhost:8787/echo")
    print(response.json())
    ```

---

<h3 id="get-echo-stream"><code>GET</code> <code>/echo/stream</code> — Echo Stream</h3>

Streaming echo: sends the input back incrementally as a data stream.

#### Parameters

| Name | In | Type | Required | Default | Description |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `data` | `query` | `string` | — | `` |  |
| `chunk_size` | `query` | `integer` | — | `16` |  |

#### Responses

| Status Code | Description | Schema / Returns |
| :--- | :--- | :--- |
| `200` | Successful Response | `any` |
| `422` | Validation Error | `HTTPValidationError` |

#### Example Request

=== "curl"
    ```bash
    curl -X GET "http://localhost:8787/echo/stream?chunk_size=16"
    ```

=== "Python (httpx)"
    ```python
    import httpx

    response = httpx.get("http://localhost:8787/echo/stream")
    print(response.json())
    ```

---
