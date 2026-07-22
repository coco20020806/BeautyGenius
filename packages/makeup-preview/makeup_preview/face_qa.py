"""User photo L2 Qwen JSON QA."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope import MultiModalConversation

from makeup_preview.config import PreviewConfig
from makeup_preview.io_util import to_file_uri


def run_face_qa(path: Path, config: PreviewConfig, run_dir: Path) -> dict[str, Any]:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    prompt = (
        "你是用户自拍质检员。判断该照片是否适合作为「抄 KOL 整妆」的上妆底图。\n"
        "要求：单人、正脸平视、无口罩/墨镜/头发遮眼、光线可接受、适合素颜或极淡妆底图。\n"
        "只输出 JSON："
        '{"is_frontal":true,"is_eye_level":true,"occlusion_ok":true,'
        '"lighting_ok":true,"suitable_as_makeup_target":true,"pass":true,"reason":""}'
    )
    content = [{"image": to_file_uri(path)}, {"text": prompt}]
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.vision_model,
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"},
    )
    if response.status_code != HTTPStatus.OK:
        err = str(getattr(response, "message", response))
        (run_dir / "face_qa_error.txt").write_text(err, encoding="utf-8")
        return {
            "is_frontal": False,
            "is_eye_level": False,
            "occlusion_ok": False,
            "lighting_ok": False,
            "suitable_as_makeup_target": False,
            "pass": False,
            "reason": "视觉质检 API 失败",
        }
    text = response.output.choices[0].message.content
    if isinstance(text, list):
        text = next((p.get("text", "") for p in text if isinstance(p, dict)), "{}")
    (run_dir / "face_qa_raw.json").write_text(str(text), encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {
            "pass": False,
            "reason": "质检 JSON 解析失败",
        }
    required = (
        "is_frontal",
        "is_eye_level",
        "occlusion_ok",
        "lighting_ok",
        "suitable_as_makeup_target",
    )
    ok = all(data.get(k) for k in required) and bool(data.get("pass"))
    data["pass"] = ok
    if ok and not data.get("reason"):
        data["reason"] = ""
    return data
