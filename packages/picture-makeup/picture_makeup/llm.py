"""DashScope JSON helpers."""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope import MultiModalConversation

from picture_makeup.config import PictureMakeupConfig


def _configure(config: PictureMakeupConfig) -> None:
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
    config: PictureMakeupConfig,
    *,
    system: str,
    user: str,
    run_dir: Path,
    dump_name: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Call qwen3.7-plus via multimodal endpoint (text-only).

    DashScope: qwen3.7-plus must use MultiModalConversation / multimodal-generation;
    Generation (text-generation) returns ``url error, please check url!``.
    """
    _configure(config)
    messages = [
        {"role": "system", "content": [{"text": system}]},
        {"role": "user", "content": [{"text": user}]},
    ]
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=model or config.text_model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"文本 API 失败: {getattr(response, 'message', response)}")
    text = _message_text(response.output.choices[0].message.content)
    (run_dir / dump_name).write_text(text, encoding="utf-8")
    return extract_json_object(text)


def call_vision_json(
    config: PictureMakeupConfig,
    *,
    system: str,
    user_text: str,
    image_paths: list[Path],
    run_dir: Path,
    dump_name: str,
) -> dict[str, Any]:
    _configure(config)
    content: list[dict[str, Any]] = []
    for p in image_paths:
        content.append({"image": f"file://{p.resolve().as_posix()}"})
    content.append({"text": user_text})
    messages = [
        {"role": "system", "content": [{"text": system}]},
        {"role": "user", "content": content},
    ]
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.vision_model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"视觉 API 失败: {getattr(response, 'message', response)}")
    text = _message_text(response.output.choices[0].message.content)
    (run_dir / dump_name).write_text(text, encoding="utf-8")
    return extract_json_object(text)
