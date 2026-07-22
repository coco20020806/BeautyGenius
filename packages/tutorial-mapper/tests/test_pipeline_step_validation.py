"""Integration: run_mapper_job writes tutorial_step_validation."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tutorial_mapper import MapperConfig, run_mapper_job


def test_mapper_job_writes_step_validation_meta():
    analysis = {
        "contract_version": "v2",
        "taxonomy_version": "v1",
        "video": {"source_path": "C:/fake.mp4", "duration_sec": 100.0},
        "generated_at": "2026-01-01T00:00:00",
        "model": "test",
        "asr_model": "fun-asr",
        "steps": [
            {
                "step_index": 1,
                "step_name": "唇妆",
                "taxonomy": {"primary": "唇妆", "sub_steps": ["唇线"], "skipped": False},
                "time_range": {
                    "start_sec": 0,
                    "end_sec": 40,
                    "start_label": "0:00",
                    "end_label": "0:40",
                },
                "text": {"voiceover": [], "subtitles": [], "on_screen": []},
                "keyframes": [
                    {
                        "index_in_step": 1,
                        "role": "step_start_face",
                        "timestamp_sec": 0,
                        "filename": "a.jpg",
                    },
                    {
                        "index_in_step": 2,
                        "role": "step_end_face",
                        "timestamp_sec": 40,
                        "filename": "b.jpg",
                    },
                ],
            },
            {
                "step_index": 2,
                "step_name": "唇妆",
                "taxonomy": {"primary": "唇妆", "sub_steps": ["唇线"], "skipped": False},
                "time_range": {
                    "start_sec": 40,
                    "end_sec": 90,
                    "start_label": "0:40",
                    "end_label": "1:30",
                },
                "text": {"voiceover": [], "subtitles": [], "on_screen": []},
                "keyframes": [
                    {
                        "index_in_step": 1,
                        "role": "step_start_face",
                        "timestamp_sec": 40,
                        "filename": "c.jpg",
                    },
                    {
                        "index_in_step": 2,
                        "role": "step_end_face",
                        "timestamp_sec": 90,
                        "filename": "d.jpg",
                    },
                ],
            },
        ],
    }
    with tempfile.TemporaryDirectory() as td:
        run = Path(td) / "run_test"
        run.mkdir()
        (run / "analysis.json").write_text(
            json.dumps(analysis, ensure_ascii=False), encoding="utf-8"
        )
        result = run_mapper_job(
            run,
            MapperConfig(
                api_key="",
                enable_text_enrich=False,
                enable_vision_enrich=False,
            ),
        )
        meta = result.enrichment_meta
        assert "tutorial_step_validation" in meta
        assert meta["tutorial_step_validation"]["pass"] is True
        stage = meta.get("stages", {}).get("step_validation", {})
        assert stage.get("ok") is True
        assert (run / "enrichment_meta.json").is_file()

        tutorial = result.tutorial
        groups = tutorial.get("step_groups") or []
        assert len(groups) == 1
        assert groups[0]["title"] == "唇妆"
        assert groups[0]["step_ids"] == ["lip_01", "lip_02"]
        titles = [s["display_title"] for s in tutorial["steps"]]
        assert titles[0] != titles[1]
        assert all(s.get("display_group_id") == "group_01" for s in tutorial["steps"])
