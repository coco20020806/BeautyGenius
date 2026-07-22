"""wan2.7-image-pro makeup transfer (multi-image editing)."""

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

from makeup_preview.config import PreviewConfig, resolve_image_size
from makeup_preview.io_util import to_file_uri
from makeup_preview.prompt_loader import load_transfer_prompt


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


def _save_outputs(urls_or_b64: list[str], run_dir: Path, prefix: str) -> list[str]:
    saved: list[str] = []
    for i, item in enumerate(urls_or_b64, start=1):
        name = f"{prefix}_{i:02d}.jpg"
        dest = run_dir / name
        if item.startswith("http://") or item.startswith("https://"):
            _download_url(item, dest)
        else:
            _write_b64(item, dest)
        saved.append(name)
    return saved


def run_transfer(
    reference_path: Path,
    target_path: Path,
    config: PreviewConfig,
    run_dir: Path,
    *,
    tutorial_before_path: Path | None = None,
    n: int = 1,
    image_size: str | None = None,
) -> tuple[list[str], str, str, str, bool]:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url

    use_v2 = tutorial_before_path is not None and tutorial_before_path.is_file()
    layout: str = "v2" if use_v2 else "v1"
    loaded = load_transfer_prompt(config.skill_dir, layout=layout)  # type: ignore[arg-type]
    prompt_text = loaded.text
    (run_dir / "transfer_prompt.txt").write_text(prompt_text, encoding="utf-8")

    if use_v2:
        content: list[dict[str, str]] = [
            {"image": to_file_uri(reference_path)},
            {"image": to_file_uri(tutorial_before_path)},
            {"image": to_file_uri(target_path)},
            {"text": prompt_text},
        ]
        prompt_version = "v2"
    else:
        content = [
            {"image": to_file_uri(reference_path)},
            {"image": to_file_uri(target_path)},
            {"text": prompt_text},
        ]
        prompt_version = "v1"

    if image_size is None:
        with Image.open(target_path) as im:
            tw, th = im.size
        image_size = resolve_image_size(tw, th, default=config.image_size)

    message = Message(role="user", content=content)
    response = ImageGeneration.call(
        api_key=config.api_key,
        model=config.image_model,
        messages=[message],
        watermark=config.image_watermark,
        n=n,
        size=image_size,
    )
    raw_path = run_dir / "transfer_raw.json"
    raw_path.write_text(
        json.dumps(_serialize_response(response), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if response.status_code != HTTPStatus.OK:
        err = str(getattr(response, "message", response))
        (run_dir / "transfer_error.txt").write_text(err, encoding="utf-8")
        raise RuntimeError(f"妆容生成失败: {err}")

    urls = _extract_images_from_response(response)
    if not urls:
        (run_dir / "transfer_error.txt").write_text(
            "未能从响应中解析图片 URL", encoding="utf-8"
        )
        raise RuntimeError("未能从响应中解析预览图，请查看 transfer_raw.json")

    return (
        _save_outputs(urls[:n], run_dir, "preview"),
        prompt_version,
        image_size,
        loaded.prompt_text_version,
        loaded.used_fallback,
    )
