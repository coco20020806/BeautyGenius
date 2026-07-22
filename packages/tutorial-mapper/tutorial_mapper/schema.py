"""JSON Schema load and validate for tutorial.v1."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from jsonschema import validate

CONTRACT_VERSION = "tutorial.v1"


def load_tutorial_schema() -> dict[str, Any]:
    ref = resources.files("tutorial_mapper").joinpath("schemas/tutorial.v1.json")
    return json.loads(ref.read_text(encoding="utf-8"))


def validate_tutorial(instance: dict[str, Any]) -> None:
    validate(instance=instance, schema=load_tutorial_schema())
