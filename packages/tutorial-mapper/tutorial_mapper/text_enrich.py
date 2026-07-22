"""Text LLM enrichment from ASR / step text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tutorial_mapper.config import MapperConfig
from tutorial_mapper.llm import call_text_json
from tutorial_mapper.parts import DIFFICULTIES, PARTS

TEXT_SYSTEM = """你是美妆跟练教程结构化助手。根据口播/字幕/画面文字，补全教程与步骤字段。
只输出一个合法 JSON 对象，不要 Markdown。字段结构：
{
  "title": "短标题",
  "difficulty": "easy|medium|hard|unknown",
  "style_tags": ["清透", "..."],
  "occasion_tags": ["通勤", "..."],
  "practice_checklist": ["检查项1", "..."],
  "eye_detail": {},
  "steps": [
    {
      "step_id": "必须与输入相同",
      "instruction": "可跟练的短指令",
      "adaptation_note": "脸型/眼型等适配提示，可空字符串",
      "product": {"name": "产品名或unknown", "keywords": ["关键词"]},
      "suitable_features": [],
      "avoid_features": [],
      "difficulty": "easy|medium|hard|unknown"
    }
  ],
  "assets": [
    {
      "part": "eye|cheek|...",
      "style_tags": [],
      "occasion_tags": [],
      "suitable_features": [],
      "avoid_features": [],
      "difficulty": "easy|medium|hard|unknown",
      "practice_notes": []
    }
  ]
}
约束：
- 不要改 step_id，不要编造 video_clip / 时间轴。
- 不确定的产品名用 "unknown"；keywords 可从口播推断质地/色调。
- eye_detail 仅当有眼妆步骤时填写简要对象（可含 layers/notes），否则 {}。
- difficulty 只能是 easy/medium/hard/unknown。
"""


def _load_transcript(parse_run_dir: Path) -> str:
    path = parse_run_dir / "transcript.json"
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    if isinstance(data, dict):
        if isinstance(data.get("text"), str):
            return data["text"]
        # fun-asr 常见结构
        segs = data.get("transcripts") or data.get("sentences") or data.get("segments")
        if isinstance(segs, list):
            parts = []
            for s in segs:
                if isinstance(s, dict):
                    t = (s.get("text") or s.get("sentence") or "").strip()
                    if t:
                        parts.append(t)
                elif isinstance(s, str):
                    parts.append(s)
            return " ".join(parts)
        # 嵌套 raw
        for key in ("result", "output", "data"):
            nested = data.get(key)
            if isinstance(nested, dict) and isinstance(nested.get("text"), str):
                return nested["text"]
    return ""


def _build_user_payload(tutorial: dict[str, Any], transcript: str) -> str:
    slim_steps = []
    for s in tutorial.get("steps") or []:
        slim_steps.append(
            {
                "step_id": s.get("step_id"),
                "part": s.get("part"),
                "taxonomy_primary": s.get("taxonomy_primary"),
                "taxonomy_sub_steps": s.get("taxonomy_sub_steps"),
                "instruction_seed": (s.get("instruction") or "")[:800],
                "video_clip": s.get("video_clip"),
                "product": s.get("product"),
            }
        )
    payload = {
        "duration": tutorial.get("duration"),
        "transcript_excerpt": (transcript or "")[:6000],
        "steps": slim_steps,
        "parts_present": sorted({s.get("part") for s in slim_steps if s.get("part")}),
    }
    return (
        "请根据以下美妆教程解析摘要补全字段，返回 JSON：\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def enrich_from_text(
    config: MapperConfig,
    tutorial: dict[str, Any],
    *,
    parse_run_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return enrichment patch + meta. Does not mutate tutorial."""
    if not config.api_key:
        raise RuntimeError("文本 enrichment 需要 DASHSCOPE_API_KEY")

    transcript = _load_transcript(parse_run_dir)
    dump_dir = parse_run_dir
    raw = call_text_json(
        config,
        system=TEXT_SYSTEM,
        user=_build_user_payload(tutorial, transcript),
        run_dir=dump_dir,
        dump_name="raw_text_enrichment.json",
    )

    meta: dict[str, Any] = {
        "source": "text_llm",
        "model": config.text_model,
        "fields_touched": [],
    }
    patch: dict[str, Any] = {"steps": {}, "assets_by_part": {}}

    title = (raw.get("title") or "").strip()
    if title:
        patch["title"] = title
        meta["fields_touched"].append("title")

    diff = (raw.get("difficulty") or "").strip()
    if diff in DIFFICULTIES:
        patch["difficulty"] = diff
        meta["fields_touched"].append("difficulty")

    for key in ("style_tags", "occasion_tags", "practice_checklist"):
        val = raw.get(key)
        if isinstance(val, list) and val:
            patch[key] = [str(x).strip() for x in val if str(x).strip()]
            meta["fields_touched"].append(key)

    eye = raw.get("eye_detail")
    if isinstance(eye, dict) and eye:
        patch["eye_detail"] = eye
        meta["fields_touched"].append("eye_detail")

    known_ids = {s["step_id"] for s in tutorial.get("steps") or []}
    for item in raw.get("steps") or []:
        if not isinstance(item, dict):
            continue
        sid = item.get("step_id")
        if sid not in known_ids:
            continue
        step_patch: dict[str, Any] = {}
        if isinstance(item.get("instruction"), str) and item["instruction"].strip():
            step_patch["instruction"] = item["instruction"].strip()
        if isinstance(item.get("adaptation_note"), str):
            step_patch["adaptation_note"] = item["adaptation_note"].strip()
        prod = item.get("product")
        if isinstance(prod, dict):
            name = (prod.get("name") or "unknown").strip() or "unknown"
            kws = prod.get("keywords") or []
            if isinstance(kws, list):
                step_patch["product"] = {
                    "name": name,
                    "keywords": [str(k).strip() for k in kws if str(k).strip()],
                }
        if step_patch:
            patch["steps"][sid] = step_patch
            meta["fields_touched"].append(f"step:{sid}")

    for item in raw.get("assets") or []:
        if not isinstance(item, dict):
            continue
        part = item.get("part")
        if part not in PARTS:
            continue
        asset_patch: dict[str, Any] = {}
        for key in (
            "style_tags",
            "occasion_tags",
            "suitable_features",
            "avoid_features",
            "practice_notes",
        ):
            val = item.get(key)
            if isinstance(val, list) and val:
                asset_patch[key] = [str(x).strip() for x in val if str(x).strip()]
        adiff = (item.get("difficulty") or "").strip()
        if adiff in DIFFICULTIES:
            asset_patch["difficulty"] = adiff
        if asset_patch:
            patch["assets_by_part"][part] = asset_patch
            meta["fields_touched"].append(f"asset:{part}")

    return patch, meta
