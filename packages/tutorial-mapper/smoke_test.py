#!/usr/bin/env python3
"""Smoke test for deterministic tutorial mapping."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tutorial_mapper import MapperConfig, run_mapper_job, validate_tutorial


def main() -> None:
    analysis = {
        "contract_version": "v2",
        "taxonomy_version": "v1",
        "video": {"source_path": "C:/fake/video.mp4", "duration_sec": 180.4},
        "generated_at": "2026-07-22T00:00:00Z",
        "model": "test",
        "asr_model": "fun-asr",
        "steps": [
            {
                "step_index": 1,
                "step_name": "腮红",
                "taxonomy": {
                    "primary": "腮红",
                    "sub_steps": ["苹果肌"],
                    "skipped": False,
                },
                "time_range": {
                    "start_sec": 62,
                    "end_sec": 76,
                    "start_label": "1:02",
                    "end_label": "1:16",
                },
                "text": {
                    "voiceover": [
                        {
                            "start_sec": 62,
                            "end_sec": 70,
                            "text": "少量多次叠加低饱和粉色腮红",
                        }
                    ],
                    "subtitles": [],
                    "on_screen": [{"time_sec": 63, "text": "腮红"}],
                },
                "keyframes": [
                    {
                        "index_in_step": 1,
                        "role": "step_start_face",
                        "timestamp_sec": 62,
                        "filename": "a.jpg",
                    },
                    {
                        "index_in_step": 2,
                        "role": "step_end_face",
                        "timestamp_sec": 76,
                        "filename": "b.jpg",
                    },
                ],
            },
            {
                "step_index": 2,
                "step_name": "眼睛",
                "taxonomy": {
                    "primary": "眼睛",
                    "sub_steps": ["外V区"],
                    "skipped": False,
                },
                "time_range": {
                    "start_sec": 80,
                    "end_sec": 100,
                    "start_label": "1:20",
                    "end_label": "1:40",
                },
                "text": {"voiceover": [], "subtitles": [], "on_screen": []},
                "keyframes": [
                    {
                        "index_in_step": 1,
                        "role": "step_start_face",
                        "timestamp_sec": 80,
                        "filename": "c.jpg",
                    },
                    {
                        "index_in_step": 2,
                        "role": "makeup_detail",
                        "timestamp_sec": 90,
                        "filename": "d.jpg",
                        "label": "外V区",
                    },
                ],
            },
        ],
    }

    with tempfile.TemporaryDirectory() as td:
        run = Path(td) / "20260722_120000"
        run.mkdir()
        (run / "analysis.json").write_text(
            json.dumps(analysis, ensure_ascii=False), encoding="utf-8"
        )
        cfg = MapperConfig(
            api_key="", enable_text_enrich=False, enable_vision_enrich=False
        )
        result = run_mapper_job(run, cfg)
        t = result.tutorial
        validate_tutorial(t)
        assert t["contract_version"] == "tutorial.v1"
        assert t["duration"] == 180
        assert t["steps"][0]["step_id"] == "blush_01"
        assert t["steps"][0]["part"] == "cheek"
        assert t["steps"][0]["video_clip"] == {"start": 62.0, "end": 76.0}
        assert "腮红" in t["steps"][0]["instruction"]
        assert t["steps"][1]["part"] == "eye"
        assert any(a["part"] == "cheek" and a["asset_id"] == "cheek_001" for a in t["assets"])
        assert any(a["part"] == "eye" and a["asset_id"] == "eye_001" for a in t["assets"])
        print("OK", t["tutorial_id"], len(t["steps"]), len(t["assets"]))
        print(result.tutorial_path)


if __name__ == "__main__":
    main()
