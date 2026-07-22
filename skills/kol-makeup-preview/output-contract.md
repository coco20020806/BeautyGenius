# 输出契约 — makeup-preview run

Schema 演进：`contract_version: "v1"`（将来 v2 另文）。

## Run 目录

根路径默认：`outputs/makeup-preview/runs/<timestamp>/`

| 文件 | 说明 |
|------|------|
| `preview.json` | 主结果 |
| `meta.json` | 耗时、模型 id、可选计费字段 |
| `reference.jpg` | 妆后参考（transfer 图1） |
| `tutorial_before.jpg` | 教程妆前（三图 v2 的图2；缺则走二图降级） |
| `target.jpg` | 用户图或底图拷贝（三图的图3） |
| `target_display.jpg` | 可选；人脸对齐裁切后的妆前展示图（API `beforeImage` **优先**） |
| `preview_01.jpg` … | 模型输出；**像素尺寸与 `target.jpg` 一致**（全图对齐对） |
| `preview_display.jpg` | 可选；与 `target_display.jpg` 同裁切的妆后展示图（API `afterImage` **优先**） |
| `transfer_prompt.txt` | 送入 wan 的完整 text（自 transfer-prompt.md 加载） |
| `user-photo-qa.json` | 仅用户上传分支 |

## preview.json

| 字段 | 含义 |
|------|------|
| `contract_version` | `"v1"` |
| `generated_at` | ISO8601 |
| `reference` | 见 [reference-selection.md](reference-selection.md) |
| `target.type` | `user_photo` \| `average_baseline` |
| `target.baseline` | 仅底图：`female` \| `male` |
| `target.skill_asset` | 仅底图：`female_average_face.png` \| `male_average_face.png` |
| `target.path` | run 内相对路径，通常 `target.jpg` |
| `validation` | 用户图：`pass`, `failed_layer`, `codes`, `reason`；底图分支可省略或 `pass: null` |
| `transfer.model` | `wan2.7-image-pro` |
| `transfer.prompt_version` | **`v2`**（三图）或降级 **`v1`**（二图）；仅表示图拓扑 |
| `transfer.prompt_text_version` | 长正文版本，如 **`wan-long-2`**（来自 [transfer-prompt.md](transfer-prompt.md)） |
| `transfer.prompt_mode` | **`full`** 或 **`scoped`**（见 [transfer-scope.md](transfer-scope.md)） |
| `transfer.scope` | scoped/full 元数据：`source`（`taxonomy-coverage` \| `tutorial.json` \| `default_full`）、`present_primaries`、`application_primaries`、`allowed_region_labels`；full 且无 parse 时仍可有 `source: default_full` |
| `transfer.requested_size` | 本次 API `size`（由 `target.jpg` 宽高比解析，如 `720*1280` 或 `2K`） |
| `alignment` | 妆前妆后几何对齐元数据（`method`、`target_size`、`display_size`、`object_position`、`display_fill_scale` 等） |
| `outputs` | `[{ "filename": "preview_01.jpg", "selected": true }]` |
| `warnings` | 如 `partial_reference`、`transfer_without_tutorial_before`、`transfer_prompt_fallback_static`、`transfer_scope_fallback_full`、`transfer_scope_from_tutorial`、`preview_align_fallback_resize_only`、`preview_align_no_face` |

## meta.json

| 字段 | 含义 |
|------|------|
| `skill_dir` | 使用的 skill 路径（repo `skills/kol-makeup-preview`） |
| `time_used_ms` | 端到端 |
| `transfer_time_used_ms` | 模型调用 |

## 下游

UI / API 只读本文件的 run 契约字段，不依赖 Skill markdown 解析。

Preview 摘要区时长标签、妆浓淡色块与对比区正片叠底语义见 [display-contract.md](display-contract.md)（由 API 组装层与前端实现，不写入 `preview.json`）。
