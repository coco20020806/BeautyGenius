"""wan2.7-image-pro single-base diagram generation."""

from __future__ import annotations

import base64
import json
import re
import urllib.request
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message
from PIL import Image

from picture_makeup.config import PictureMakeupConfig, resolve_image_size
from picture_makeup.io_util import to_file_uri
from picture_makeup.prompt_loader import compose_diagram_full_text, load_diagram_prompt


def _serialize_response(response: Any) -> Any:
    try:
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return json.loads(json.dumps(response, default=str))
    except (TypeError, ValueError):
        return {"repr": repr(response)}


def _download_url(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "BeautyGenius/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def _write_b64(data: str, dest: Path) -> None:
    if data.startswith("data:"):
        data = data.split(",", 1)[-1]
    dest.write_bytes(base64.b64decode(data))


def _content_parts(message: Any) -> list[Any]:
    if message is None:
        return []
    content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
    if isinstance(content, list):
        return content
    if isinstance(content, str):
        return [{"text": content}]
    return []


def _extract_images_from_response(response: Any) -> list[str]:
    urls: list[str] = []
    output = getattr(response, "output", None)
    if output is None:
        return urls
    choices = output.get("choices") if isinstance(output, dict) else getattr(output, "choices", None)
    if not choices:
        return urls
    for choice in choices:
        msg = choice.get("message") if isinstance(choice, dict) else getattr(choice, "message", None)
        for part in _content_parts(msg):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "image" and part.get("image"):
                urls.append(str(part["image"]))
            elif part.get("image"):
                urls.append(str(part["image"]))
            if part.get("text"):
                urls.extend(re.findall(r"https?://[^\s\"']+", str(part["text"])))
    return urls


def run_diagram(
    config: PictureMakeupConfig,
    *,
    base_image: Path,
    final_prompt: str,
    step_dir: Path,
) -> Path:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url

    loaded = load_diagram_prompt(config.skill_dir)
    full_text = compose_diagram_full_text(loaded.static_text, final_prompt)
    (step_dir / "diagram_prompt.txt").write_text(full_text, encoding="utf-8")

    with Image.open(base_image) as im:
        bw, bh = im.size
    image_size = resolve_image_size(bw, bh, default=config.image_size)

    message = Message(
        role="user",
        content=[
            {"image": to_file_uri(base_image)},
            {"text": full_text},
        ],
    )
    response = ImageGeneration.call(
        api_key=config.api_key,
        model=config.image_model,
        messages=[message],
        watermark=config.image_watermark,
        n=1,
        size=image_size,
    )
    (step_dir / "wan_raw.json").write_text(
        json.dumps(_serialize_response(response), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if response.status_code != HTTPStatus.OK:
        err = str(getattr(response, "message", response))
        (step_dir / "diagram_error.txt").write_text(err, encoding="utf-8")
        raise RuntimeError(f"步骤图示生成失败: {err}")

    urls = _extract_images_from_response(response)
    if not urls:
        (step_dir / "diagram_error.txt").write_text(
            "未能从响应中解析图片 URL", encoding="utf-8"
        )
        raise RuntimeError("未能从响应中解析图示，请查看 wan_raw.json")

    dest = step_dir / "diagram_01.jpg"
    item = urls[0]
    if item.startswith("http://") or item.startswith("https://"):
        _download_url(item, dest)
    else:
        _write_b64(item, dest)

    with Image.open(dest) as out_im:
        if out_im.size != (bw, bh):
            out_im.convert("RGB").resize((bw, bh), Image.Resampling.LANCZOS).save(
                dest, format="JPEG", quality=92
            )
    return dest
