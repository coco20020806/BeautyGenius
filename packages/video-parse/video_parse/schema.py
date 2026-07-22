"""JSON Schema load and validate."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from jsonschema import validate

from video_parse.config import CONTRACT_VERSION_V21


def load_analysis_schema(*, contract_version: str | None = None) -> dict[str, Any]:
    ver = contract_version or "v2"
    if ver == CONTRACT_VERSION_V21:
        fname = "beauty_video_analysis.v2.1.json"
    else:
        fname = "beauty_video_analysis.v2.json"
    ref = resources.files("video_parse").joinpath(f"schemas/{fname}")
    return json.loads(ref.read_text(encoding="utf-8"))


def validate_analysis(instance: dict[str, Any]) -> None:
    ver = instance.get("contract_version", "v2")
    validate(instance=instance, schema=load_analysis_schema(contract_version=ver))
