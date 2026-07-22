"""DashScope text JSON helpers.

qwen3.7-plus must use MultiModalConversation (multimodal-generation).
Generation (text-generation) returns ``url error, please check url!``.
"""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope import MultiModalConversation

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


def _message_text(raw_content: Any) -> str:
    if isinstance(raw_content, list) and raw_content:
        first = raw_content[0]
        if isinstance(first, dict):
            return str(first.get("text", "") or "")
        return str(first)
    if isinstance(raw_content, str):
        return raw_content
    return ""


def call_text_json(
    config: UnderstandingConfig,
    *,
    system: str,
    user: str,
    run_dir: Path,
    dump_name: str,
) -> dict[str, Any]:
    _configure(config)
    messages = [
        {"role": "system", "content": [{"text": system}]},
        {"role": "user", "content": [{"text": user}]},
    ]
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.text_model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"makeup-understanding API 失败: {getattr(response, 'message', response)}")
    text = _message_text(response.output.choices[0].message.content)
    (run_dir / dump_name).write_text(text, encoding="utf-8")
    try:
        return extract_json_object(text)
    except (json.JSONDecodeError, ValueError):
        return repair_json(config, text, run_dir, dump_name=f"repaired_{dump_name}")


def repair_json(
    config: UnderstandingConfig,
    raw: str,
    run_dir: Path,
    *,
    dump_name: str,
) -> dict[str, Any]:
    _configure(config)
    messages = [
        {
            "role": "system",
            "content": [{"text": "Fix the following into a single valid JSON object. Return JSON only."}],
        },
        {"role": "user", "content": [{"text": raw[:12000]}]},
    ]
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.repair_model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"JSON repair API 失败: {getattr(response, 'message', response)}")
    text = _message_text(response.output.choices[0].message.content)
    (run_dir / dump_name).write_text(text, encoding="utf-8")
    return extract_json_object(text)
