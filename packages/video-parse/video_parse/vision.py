"""Qwen video understanding."""

from __future__ import annotations

import json
import time
from http import HTTPStatus
from pathlib import Path
from typing import Any

import dashscope
from dashscope import Generation, MultiModalConversation

from video_parse.config import ParseConfig
from video_parse.preprocess import to_file_uri
from video_parse.taxonomy import repair_taxonomy_hint, taxonomy_summary_for_prompt

VISION_USER = (
    "请分析该美妆教程视频，严格按 taxonomy 输出上述 JSON。"
    "口播将由 ASR 单独处理；subtitles 可写画面字幕。on_screen 写画面文字。"
)


def build_vision_system(config: ParseConfig) -> str:
    tax_block = taxonomy_summary_for_prompt(config.skill_dir)
    return f"""你是美妆教程视频分析助手。请观看完整视频，按化妆步骤划分时间轴。
必须只输出一个合法 JSON 对象（不要 Markdown、不要解释），字段结构如下：
{{
  "steps": [
    {{
      "step_index": 1,
      "step_name": "妆前",
      "taxonomy": {{
        "primary": "妆前",
        "sub_steps": ["局部打底", "使用区域"],
        "skipped": false
      }},
      "time_range": {{
        "start_sec": 0,
        "end_sec": 90,
        "start_label": "0:00",
        "end_label": "1:30"
      }},
      "text": {{
        "subtitles": [{{"time_sec": 10, "text": "..."}}],
        "on_screen": [{{"time_sec": 15, "text": "..."}}]
      }},
      "keyframes": [
        {{"role": "step_start_face", "timestamp_sec": 0, "label": "步骤开始脸部"}},
        {{"role": "step_end_face", "timestamp_sec": 90, "label": "步骤结束脸部"}},
        {{"role": "makeup_detail", "timestamp_sec": 45, "label": "局部打底"}}
      ]
    }}
  ]
}}
要求：
- {tax_block}
- subtitles：烧录字幕或口型/字幕条推断（勿假设已听音轨）。
- on_screen：画面内文字、产品名、步骤标题等 OCR。
- 每个 step 的 keyframes 至少包含 step_start_face 与 step_end_face；另加 0–3 个 makeup_detail，label 必须为 taxonomy.sub_steps 中的名称。
- 所有时间为秒（浮点），start_label/end_label 为 M:SS。
- 另含 replication_hints（片尾复刻参考，不要片头预告成妆）：
  "replication_hints": {{
    "tail_layout": "single|split|sequence|none",
    "tail_after_sec": <片尾全妆展示时刻或 null>,
    "tail_before_sec": <片尾对比素颜时刻或 null>,
    "split_frame_sec": <分屏单帧时刻或 null>,
    "baseline_before_sec": <教程妆前基线露脸时刻或 null>
  }}"""


def call_vision(
    config: ParseConfig, video_path: Path, run_dir: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    file_uri = to_file_uri(video_path)
    messages = [
        {"role": "system", "content": [{"text": build_vision_system(config)}]},
        {
            "role": "user",
            "content": [
                {"video": file_uri, "fps": config.video_fps},
                {"text": VISION_USER},
            ],
        },
    ]
    t0 = time.perf_counter()
    response = MultiModalConversation.call(
        api_key=config.api_key,
        model=config.vision_model,
        messages=messages,
        response_format={"type": "json_object"},
    )
    elapsed = time.perf_counter() - t0
    if response.status_code != HTTPStatus.OK:
        raw = getattr(response, "message", str(response))
        (run_dir / "raw_vision_error.txt").write_text(str(raw), encoding="utf-8")
        raise RuntimeError(f"视频理解 API 失败: {raw}")
    content = response.output.choices[0].message.content
    text = ""
    if isinstance(content, list) and content:
        text = content[0].get("text", "")
    elif isinstance(content, str):
        text = content
    (run_dir / "raw_vision_response.txt").write_text(text, encoding="utf-8")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = repair_json(config, text, run_dir)
    return parsed, {"elapsed_sec": elapsed, "usage": getattr(response, "usage", None)}


def repair_json(config: ParseConfig, broken: str, run_dir: Path) -> dict[str, Any]:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    hint = repair_taxonomy_hint(config.skill_dir)
    response = Generation.call(
        api_key=config.api_key,
        model=config.repair_model,
        messages=[
            {
                "role": "system",
                "content": f"Fix to valid JSON with steps array for beauty tutorial. Return JSON only. {hint}",
            },
            {"role": "user", "content": broken},
        ],
        response_format={"type": "json_object"},
        result_format="message",
    )
    if response.status_code != HTTPStatus.OK:
        raise RuntimeError(f"JSON 修复失败: {getattr(response, 'message', response)}")
    text = response.output.choices[0].message.content
    (run_dir / "raw_vision_repaired.txt").write_text(text, encoding="utf-8")
    return json.loads(text)
