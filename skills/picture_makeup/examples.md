# 示例 — Agent 执行 picture-makeup

假设仓库根为 `Beauty Genius`，parse run 已含 `tutorial.json` 与 `keyframes/`。

## 1. 检查前置

```text
parse_run_dir = outputs/runs/20260722_143000
skill_dir = skills/picture_makeup
assert (skill_dir / "image_format.png").is_file()
assert (parse_run_dir / "tutorial.json").is_file()
assert (parse_run_dir / "keyframes").is_dir()
```

## 2. 创建 run 目录

```text
out = outputs/picture-makeup/runs/20260722_150000
out/steps/  # 按 step_id 分子目录
```

## 3. 单步循环（以 blush_01 为例）

1. 从 `tutorial.json` 读取 `steps[]` 中 `step_id == "blush_01"` 的对象。
2. 调用 [step-prompt-qwen.md](step-prompt-qwen.md) → 写入 `steps/blush_01/base_prompt.txt`。
3. 按 [keyframe-enrich-qwen.md](keyframe-enrich-qwen.md) 选帧，例如：
   - `keyframes/腮红-步骤结束-76.0.jpg`（`step_end_face`）
4. 视觉 enrich → `steps/blush_01/enrich.json` + `final_prompt.txt`。
5. 自检：`final_prompt.startswith(base_prompt)`。
6. 按 [diagram-prompt-wan.md](diagram-prompt-wan.md) 调用 wan → `diagram_01.jpg`。

## 4. 更新 manifest.json（节选）

```json
{
  "contract_version": "v1",
  "generated_at": "2026-07-22T07:00:00Z",
  "skill_dir": "skills/picture_makeup",
  "base_image": "skills/picture_makeup/image_format.png",
  "parse_run_dir": "outputs/runs/20260722_143000",
  "tutorial_id": "tutorial_20260722_143000",
  "text_model": "qwen3.7-plus",
  "vision_model": "qwen3.7-plus",
  "image_model": "wan2.7-image-pro",
  "diagram": { "prompt_text_version": "diagram-2" },
  "steps": [
    {
      "step_id": "blush_01",
      "part": "cheek",
      "index": 2,
      "status": "ok",
      "base_prompt_path": "steps/blush_01/base_prompt.txt",
      "final_prompt_path": "steps/blush_01/final_prompt.txt",
      "diagram_path": "steps/blush_01/diagram_01.jpg",
      "warnings": []
    }
  ],
  "warnings": []
}
```

## 5. 仅调试一步

对其余 `step_id` 在 manifest 中设 `"status": "skipped"`，不调用 API。

## 6. prep 步骤示例（visual_layer 空）

- base_prompt 可能为：「在 T 区与面颊轻铺保湿打底，请在原始图片上用色块标注作用区域」
- enrich 仍 append-only；wan 生成浅色斑块示意分区。

## 7. 无关键帧

若某步 `keyframe_refs` 为空或 JPG 缺失：

```json
{
  "skipped": true,
  "appendix": "",
  "final_prompt": "<同 base_prompt>",
  "conflict": false,
  "notes": "no keyframes",
  "keyframe_files": []
}
```

manifest 该步 `warnings: ["no_keyframes_for_enrich"]`，仍可对 wan 使用 `final_prompt == base_prompt`。
