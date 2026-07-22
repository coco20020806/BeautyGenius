# 输出契约 — picture-makeup run

Schema 演进：`contract_version: "v1"`（将来 v2 另文）。

## Run 目录

根路径默认：`outputs/picture-makeup/runs/<timestamp>/`

| 文件 | 说明 |
|------|------|
| `manifest.json` | 主索引：tutorial、parse run、模型、逐步 status |
| `meta.json` | 可选；耗时、逐步 API 计数 |
| `steps/<step_id>/base_prompt.txt` | 第 1 阶段 qwen 输出 |
| `steps/<step_id>/enrich.json` | 第 2 阶段：appendix、conflict、notes、keyframe_files、skipped |
| `steps/<step_id>/final_prompt.txt` | base + appendix（须以 base 为前缀） |
| `steps/<step_id>/diagram_prompt.txt` | 送入 wan 的完整 text |
| `steps/<step_id>/diagram_01.jpg` | 成功时的图示 |
| `steps/<step_id>/wan_raw.json` | 可选调试 |
| `steps/<step_id>/diagram_error.txt` | wan 失败时 |

底图 **不拷贝** 到 run（始终引用 `skill_dir/image_format.png`）；manifest 记录 `base_image` 绝对或 repo 相对路径。

## manifest.json

| 字段 | 含义 |
|------|------|
| `contract_version` | `"v1"` |
| `generated_at` | ISO8601 |
| `skill_dir` | 使用的 skill 路径 |
| `base_image` | 通常 `skills/picture_makeup/image_format.png` |
| `parse_run_dir` | 上游 parse / tutorial 目录 |
| `tutorial_id` | 来自 `tutorial.json` |
| `tutorial_path` | run 内相对或绝对路径 |
| `text_model` | `qwen3.7-plus`（base prompt） |
| `vision_model` | `qwen3.7-plus`（enrich） |
| `image_model` | `wan2.7-image-pro` |
| `diagram.prompt_text_version` | 如 `diagram-1`（来自 diagram-prompt-wan.md） |
| `steps` | 数组，见下表 |
| `warnings` | run 级，如 `missing_base_image` |

### manifest.steps[]

| 字段 | 含义 |
|------|------|
| `step_id` | tutorial step |
| `part` | tutorial `part` |
| `index` | 在 `tutorial.steps` 中的从 0 起序号 |
| `status` | `ok` \| `failed` \| `skipped` |
| `base_prompt_path` | 相对 run，如 `steps/blush_01/base_prompt.txt` |
| `final_prompt_path` | 相对 run |
| `diagram_path` | 成功时 `steps/.../diagram_01.jpg` |
| `warnings` | 如 `no_keyframes_for_enrich`、`enrich_conflict` |

## enrich.json

| 字段 | 含义 |
|------|------|
| `base_prompt` | 冗余存档，须与 base_prompt.txt 一致 |
| `appendix` | 模型输出 |
| `final_prompt` | 合成结果 |
| `conflict` | boolean |
| `notes` | string |
| `keyframe_files` | 使用的 filename 列表 |
| `skipped` | 无关键帧时为 true |

## 自检规则

1. `final_prompt.startswith(base_prompt)` 必须为真。
2. `skipped` 为 true 时 `appendix` 应为空且 `final_prompt == base_prompt`。
3. `status === ok` 时须存在 `diagram_01.jpg`。

## 下游

UI / 跟练页可按 `step_id` 挂载 `diagram_01.jpg` 与 `final_prompt`；只读 JSON/图片，不依赖 Skill markdown。

## Phase 2

可执行包化后，CLI 应写入相同契约；见 [module-structure.md](module-structure.md)。
