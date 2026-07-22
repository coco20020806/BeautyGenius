from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from makeup_visual_optimization.config import OptimizationConfig
from makeup_visual_optimization.pipeline import run_optimization_job


def test_run_optimization_job_writes_artifacts(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Skill\nHard constraints.", encoding="utf-8")
    (skill_dir / "references" / "optimization-rules.md").write_text("# Rules", encoding="utf-8")
    (skill_dir / "references" / "output-contract.md").write_text("# Contract", encoding="utf-8")

    tutorial_path = tmp_path / "tutorial.json"
    tutorial_path.write_text(
        json.dumps(
            {
                "contract_version": "tutorial.v1",
                "tutorial_id": "t1",
                "title": "Test",
                "steps": [
                    {
                        "step_id": "blush_01",
                        "part": "cheek",
                        "instruction": "斜扫",
                        "adaptation_note": "",
                        "visual_layer": {"position": "颧骨"},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    fake_opt = {
        "optimization_summary": {"primary_goal": "缩短中庭", "retained_modules": []},
        "step_adjustments": [
            {
                "step_id": "blush_01",
                "adapted": "横向轻铺",
                "adaptation_note": "缩短中庭",
                "visual_layer_patch": {
                    "position_description": "面中横向",
                    "opacity": 0.4,
                },
            }
        ],
    }

    config = OptimizationConfig(api_key="test-key", skill_dir=skill_dir)
    with patch(
        "makeup_visual_optimization.pipeline.call_optimization_json",
        return_value=fake_opt,
    ) as mock_llm:
        result = run_optimization_job(
            tutorial_path=tutorial_path,
            adjustment={"styles": ["清透自然"], "concerns": ["缩短中庭"], "skinType": "混合性肌肤"},
            output_root=tmp_path / "out",
            config=config,
        )

    assert mock_llm.called
    assert result.optimized_tutorial_path.is_file()
    optimized = json.loads(result.optimized_tutorial_path.read_text(encoding="utf-8"))
    assert optimized["steps"][0]["instruction"] == "横向轻铺"
    assert optimized["steps"][0]["visual_layer"]["position"] == "面中横向"
    assert (result.run_dir / "optimization.json").is_file()
    assert (result.run_dir / "optimization_input.json").is_file()
    assert result.manifest_path.is_file()
