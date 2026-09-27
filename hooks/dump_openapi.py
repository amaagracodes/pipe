"""MkDocs hook to automatically dump OpenAPI specification prior to build."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

from pipe.api.openapi import dump_openapi


def on_pre_build(config, **kwargs):
    """Event handler triggered before documentation is built."""
    target_dir = Path(config["docs_dir"]) / "api"
    dump_openapi(target_dir=target_dir)
