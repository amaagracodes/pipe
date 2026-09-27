"""Automated OpenAPI schema extraction and documentation generator.

Extracts the OpenAPI schema from the FastAPI app and automatically exports:
1. `openapi.json` — raw OpenAPI 3.1 schema.
2. `openapi.yaml` — YAML-formatted schema.
3. `routes.md` — full, beautifully styled markdown reference for all routes,
   parameters, request bodies, responses, and curl/Python code examples.

Can be run directly via:
    python -m pipe.api.openapi
    uv run dump-openapi
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def get_openapi_schema() -> dict[str, Any]:
    """Instantiate the FastAPI application and generate its OpenAPI schema."""
    from pipe.api.app import create_app

    app = create_app()
    return app.openapi()


def _format_schema_type(schema: dict[str, Any] | None) -> str:
    if not schema:
        return "any"
    if "type" in schema:
        t = schema["type"]
        if isinstance(t, list):
            return " | ".join(t)
        return str(t)
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "anyOf" in schema:
        return " | ".join(_format_schema_type(s) for s in schema["anyOf"])
    return "object"


def generate_markdown_docs(schema: dict[str, Any]) -> str:
    """Generate comprehensive, beautifully formatted Markdown reference for all routes."""
    info = schema.get("info", {})
    version = info.get("version", "0.1.0")

    lines: list[str] = [
        "---",
        "title: REST API Route Reference",
        "description: Complete, automatically generated route reference for the pipe API.",
        "---",
        "",
        "# REST API Route Reference",
        "",
        "> [!NOTE] Automated Documentation",
        "> This document is automatically generated from the FastAPI route definitions via `pipe.api.openapi`.",
        "> Any route, parameter, or docstring changes in `src/pipe/api/routes.py` are immediately reflected here.",
        "",
        f"**API Version:** `{version}` | **OpenAPI Version:** `{schema.get('openapi', '3.1.0')}`  ",
        "**Raw Schemas:** [openapi.json](openapi.json) · [openapi.yaml](openapi.yaml) · **Interactive Docs:** [/docs](http://localhost:8787/docs) · [/redoc](http://localhost:8787/redoc)",
        "",
        "---",
        "",
        "## Endpoints Overview",
        "",
        "| Method | Path | Summary | Tags |",
        "| :--- | :--- | :--- | :--- |",
    ]

    paths = schema.get("paths", {})
    for path, methods in sorted(paths.items()):
        for method, op in sorted(methods.items()):
            method_upper = method.upper()
            summary = op.get("summary", "")
            tags = ", ".join(f"`{t}`" for t in op.get("tags", []))
            anchor = f"#{method.lower()}-{path.strip('/').replace('/', '-').replace('{', '').replace('}', '')}"
            lines.append(f"| **`{method_upper}`** | [`{path}`]({anchor}) | {summary} | {tags} |")

    lines.extend(["", "---", ""])

    # Group routes by tag
    tag_groups: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    for path, methods in sorted(paths.items()):
        for method, op in sorted(methods.items()):
            tags = op.get("tags", ["general"])
            for tag in tags:
                tag_groups.setdefault(tag, []).append((method.upper(), path, op))

    tag_titles = {
        "ops": "Core Operations",
        "llm": "LLM & Speech-to-Text",
        "legal": "Legal Expert Operations",
    }

    for tag, endpoints in sorted(tag_groups.items()):
        group_title = tag_titles.get(tag, tag.capitalize())
        lines.extend([
            f"## {group_title} (`{tag}`)",
            "",
        ])

        for method, path, op in endpoints:
            summary = op.get("summary", path)
            docstring = op.get("description", "")
            params = op.get("parameters", [])
            request_body = op.get("requestBody")
            responses = op.get("responses", {})

            anchor_id = f"{method.lower()}-{path.strip('/').replace('/', '-').replace('{', '').replace('}', '')}"
            lines.extend([
                f'<h3 id="{anchor_id}"><code>{method}</code> <code>{path}</code> — {summary}</h3>',
                "",
            ])

            if docstring:
                lines.extend([docstring.strip(), ""])

            # Parameters Table
            if params:
                lines.extend([
                    "#### Parameters",
                    "",
                    "| Name | In | Type | Required | Default | Description |",
                    "| :--- | :--- | :--- | :---: | :--- | :--- |",
                ])
                for p in params:
                    p_name = p.get("name", "")
                    p_in = p.get("in", "")
                    p_req = "✓" if p.get("required") else "—"
                    p_schema = p.get("schema", {})
                    p_type = _format_schema_type(p_schema)
                    p_default = str(p_schema.get("default", "—")) if "default" in p_schema else "—"
                    p_desc = p.get("description", "")
                    lines.append(f"| `{p_name}` | `{p_in}` | `{p_type}` | {p_req} | `{p_default}` | {p_desc} |")
                lines.append("")

            # Request Body
            if request_body:
                lines.extend(["#### Request Body", ""])
                content = request_body.get("content", {})
                for media_type, media_info in content.items():
                    schema_info = media_info.get("schema", {})
                    lines.append(f"- **Content-Type:** `{media_type}`")
                    schema_props = schema_info.get("properties", {})
                    if schema_props:
                        lines.extend([
                            "",
                            "| Field | Type | Description |",
                            "| :--- | :--- | :--- |",
                        ])
                        for prop_name, prop_val in schema_props.items():
                            pt = _format_schema_type(prop_val)
                            pd = prop_val.get("description", "")
                            lines.append(f"| `{prop_name}` | `{pt}` | {pd} |")
                        lines.append("")

            # Responses Table
            if responses:
                lines.extend([
                    "#### Responses",
                    "",
                    "| Status Code | Description | Schema / Returns |",
                    "| :--- | :--- | :--- |",
                ])
                for code, resp in sorted(responses.items()):
                    desc = resp.get("description", "")
                    resp_content = resp.get("content", {})
                    if "application/json" in resp_content:
                        r_type = _format_schema_type(resp_content["application/json"].get("schema"))
                    elif resp_content:
                        r_type = ", ".join(resp_content.keys())
                    else:
                        r_type = "empty"
                    lines.append(f"| `{code}` | {desc} | `{r_type}` |")
                lines.append("")

            # Code Examples
            lines.extend([
                "#### Example Request",
                "",
                '=== "curl"',
                "    ```bash",
            ])
            if method == "GET":
                query_items = [
                    f"{p['name']}={p.get('schema', {}).get('default', 'example')}"
                    for p in params
                    if p.get("in") == "query" and p.get("schema", {}).get("default")
                ]
                query_str = f"?{'&'.join(query_items)}" if query_items else ""
                lines.append(f'    curl -X GET "http://localhost:8787{path}{query_str}"')
            elif "multipart/form-data" in (request_body or {}).get("content", {}):
                lines.append(f'    curl -X POST "http://localhost:8787{path}" \\')
                lines.append('      -F "file=@audio.wav"')
            else:
                lines.append(f'    curl -X POST "http://localhost:8787{path}" \\')
                lines.append('      -H "Content-Type: application/json"')
            lines.extend([
                "    ```",
                "",
                '=== "Python (httpx)"',
                "    ```python",
                "    import httpx",
                "",
            ])
            if method == "GET":
                lines.append(f'    response = httpx.get("http://localhost:8787{path}")')
            elif "multipart/form-data" in (request_body or {}).get("content", {}):
                lines.append('    with open("audio.wav", "rb") as f:')
                lines.append(f'        response = httpx.post("http://localhost:8787{path}", files={{"file": f}})')
            else:
                lines.append(f'    response = httpx.post("http://localhost:8787{path}")')
            lines.extend([
                "    print(response.json())",
                "    ```",
                "",
                "---",
                "",
            ])

    return "\n".join(lines)


def dump_openapi(
    target_dir: str | Path | None = None,
    json_filename: str = "openapi.json",
    yaml_filename: str = "openapi.yaml",
    markdown_filename: str = "routes.md",
) -> tuple[Path, Path, Path]:
    """Generate and write openapi.json, openapi.yaml, and routes.md to the target directory.

    Defaults to `pipe-vault/api` (or repo root fallback).
    """
    if target_dir is None:
        repo_root = Path(__file__).resolve().parents[3]
        target_dir = repo_root / "pipe-vault" / "api"
    else:
        target_dir = Path(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)
    schema = get_openapi_schema()

    # 1. JSON
    json_path = target_dir / json_filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 2. YAML
    yaml_path = target_dir / yaml_filename
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(schema, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # 3. Markdown Reference
    md_content = generate_markdown_docs(schema)
    markdown_path = target_dir / markdown_filename
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return json_path, yaml_path, markdown_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Dump FastAPI OpenAPI spec to JSON, YAML, and Markdown docs")
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Target directory for generated files (default: pipe-vault/api)",
    )
    args = parser.parse_args()
    json_path, yaml_path, md_path = dump_openapi(args.output_dir)
    print(f"OpenAPI documentation generated successfully:\n  - {json_path}\n  - {yaml_path}\n  - {md_path}")


if __name__ == "__main__":
    main()
