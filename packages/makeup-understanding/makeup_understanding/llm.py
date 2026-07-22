"""DashScope text JSON helpers."""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope import Generation

from makeup_understanding.config import UnderstandingConfig


def _configure(config: UnderstandingConfig) -> None:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url


def extract_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty model output")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("no JSON object in model output")
    return json.loads(m.group(0))


def repair_json(
    config: UnderstandingConfig,
    raw: str,
    run_dir: Path,
    *,
    dump_name: str,
) -> dict[str, Any]:
    _configure(config)
    response = Generation.call(
        api_key=config.api_key,
        model=config.repair_model,
        messages=[
            {
                "role": "system",
                "content": "Fix the following into a single valid JSON object. Return JSON only.",
            },
            {"role": "user", "content": raw[:12000]},
        ],
        response_format={"type": "json_object"},
        result_format="message",
    )
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"JSON repair API 失败: {getattr(response, 'message', response)}")
    text = response.output.choices[0].message.content
    (run_dir / dump_name).write_text(text if isinstance(text, str) else str(text), encoding="utf-8")
    return extract_json_object(text if isinstance(text, str) else str(text))


def call_text_json(
    config: UnderstandingConfig,
    *,
    system: str,
    user: str,
    run_dir: Path,
    dump_name: str,
) -> dict[str, Any]:
    _configure(config)
    response = Generation.call(
        api_key=config.api_key,
        model=config.text_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        result_format="message",
    )
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"makeup-understanding API 失败: {getattr(response, 'message', response)}")
    text = response.output.choices[0].message.content
    (run_dir / dump_name).write_text(text if isinstance(text, str) else str(text), encoding="utf-8")
    try:
        return extract_json_object(text if isinstance(text, str) else str(text))
    except (json.JSONDecodeError, ValueError):
        return repair_json(config, str(text), run_dir, dump_name=f"repaired_{dump_name}")
