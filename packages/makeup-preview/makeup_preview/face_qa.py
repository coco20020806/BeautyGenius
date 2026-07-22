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

_SOFT_PASS: dict[str, Any] = {
    "is_frontal": True,
    "is_eye_level": True,
    "occlusion_ok": True,
    "lighting_ok": True,
    "suitable_as_makeup_target": True,
    "pass": True,
    "l2_soft_pass": True,
}

FACE_QA_PROMPT = (
    "你是用户自拍质检员。判断该照片是否适合作为「抄 KOL 整妆」的上妆底图。\n"
    "要求：大致单人、接近正脸平视即可；允许淡妆或美颜；光线大致可用即可。\n"
    "仅在以下情况判不合格：口罩/墨镜严重遮挡五官、脸部大面积被头发或手遮挡、"
    "明显非人脸主体、或完全无法辨认面部。\n"
    "不要因为已化妆、滤镜、轻微侧脸/歪头、或光线一般而拒绝。\n"
    "只输出 JSON："
    '{"is_frontal":true,"is_eye_level":true,"occlusion_ok":true,'
    '"lighting_ok":true,"suitable_as_makeup_target":true,"pass":true,"reason":""}'
)


def run_face_qa(path: Path, config: PreviewConfig, run_dir: Path) -> dict[str, Any]:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    content = [{"image": to_file_uri(path)}, {"text": FACE_QA_PROMPT}]
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
            **_SOFT_PASS,
            "reason": "视觉质检不可用，已放行",
        }
    text = response.output.choices[0].message.content
    if isinstance(text, list):
        text = next((p.get("text", "") for p in text if isinstance(p, dict)), "{}")
    (run_dir / "face_qa_raw.json").write_text(str(text), encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {
            **_SOFT_PASS,
            "reason": "质检 JSON 解析失败，已放行",
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
