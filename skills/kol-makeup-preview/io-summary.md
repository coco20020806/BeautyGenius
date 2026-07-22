# 输入与输出摘要

Skill 目录：`<repo-root>/skills/kol-makeup-preview/`

## 输入

### 必选（妆面来源，二选一）

| 输入 | 说明 |
|------|------|
| **Parse run** | `beauty-video-parse` 产物目录。妆面图优先 **`makeup_replication_refs.after`**（v2.1）；教程妆前优先 **`makeup_replication_refs.before`**（见 [reference-selection.md](reference-selection.md)）。回退 `step_end_face`。 |
| **手动参考图** | `--reference-image <path>`：单张 KOL/教程完成妆面图（PNG/JPG 等）。无 parse run 时使用（无教程妆前 → 二图降级）。 |

### 目标脸（二选一）

| 输入 | 说明 |
|------|------|
| **用户自拍** | `--user-photo <path>`。须通过 [face-validation.md](face-validation.md)（L0 文件 → L1 MediaPipe 平视正脸 → L2 Qwen JSON）。 |
| **平均脸底图** | `--use-baseline` + 可选 `--baseline female\|male`（默认 `female`）。使用 Skill 内 PNG，见 [baselines.md](baselines.md)：`female_average_face.png` / `male_average_face.png`。 |

### Transfer 图像（默认三图 v2）

| 顺序 | 文件 | 来源 |
|------|------|------|
| 图1 | `reference.jpg` | 教程/KOL **妆后** |
| 图2 | `tutorial_before.jpg` | 教程 **妆前**（有 parse before 时默认进模型） |
| 图3 | `target.jpg` | 用户自拍或平均脸 |

详见 [transfer-prompt.md](transfer-prompt.md)。缺 before 时回退二图 v1，并打 `transfer_without_tutorial_before`。

### 环境与配置

| 输入 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 调用 `wan2.7-image-pro`（生成）与 `qwen3.7-plus`（用户照 L2 质检）。 |
| `skill_dir` | 默认 `<repo-root>/skills/kol-makeup-preview/`（底图 PNG 所在目录）。 |

### 可选参数（CLI / Agent）

| 参数 | 说明 |
|------|------|
| `--reference-step` | 指定从 parse run 的某 `step_name` 选参考帧。 |
| `--validate-only` | 仅质检用户照。 |
| `--strict-replication` | v2.1 复刻参考未验证（含 after 单帧失败）时中止。 |
| `--output-root` | 默认 `outputs/makeup-preview/`。 |

**串联 job**：[`docs/REPLICATE_PIPELINE.md`](../../docs/REPLICATE_PIPELINE.md)（`run_beauty_replicate.py`）。

**互斥**：同一任务不能同时 `--user-photo` 与 `--use-baseline`；必须提供 parse run 或 reference-image 之一。

## 输出

默认 run 目录：`outputs/makeup-preview/runs/<timestamp>/`

| 产物 | 何时有 | 说明 |
|------|--------|------|
| `preview.json` | 总是 | 主契约，`contract_version: v1`；含 reference、target、transfer、outputs。 |
| `meta.json` | 总是 | 耗时、模型、`skill_dir` 等。 |
| `reference.jpg` | 成功选参考 | 妆后参考（transfer 图1）。 |
| `tutorial_before.jpg` | 有教程妆前时 | 妆前对照（transfer 图2，三图路径）。 |
| `target.jpg` | 总是 | 用户照或平均脸（transfer 图3 或二图降级的图2）。 |
| `preview_01.jpg` … | 生成成功 | `wan2.7-image-pro` 妆容迁移预览图。 |
| `user-photo-qa.json` | 仅用户上传 | L1/L2 质检明细；须 `pass: true` 才应继续生成。 |

### `preview.json` 关键字段

- **reference**：参考来源（parse_run / manual）、步骤名、关键帧 role 等。
- **target.type**：`user_photo` | `average_baseline`。
- **transfer.prompt_version**：`v2`（三图）或降级 `v1`（二图）。
- **warnings**：如 `transfer_without_tutorial_before`、`replication_pair_not_validated`。
- **outputs**：生成图文件名列表。

完整字段见 [output-contract.md](output-contract.md)。

## 对用户可见结果

- **上传通过**：个人脸部适配预览图路径 + 可选展示 `preview_01.jpg`。
- **不上传 / 底图**：预览图 + 明确说明 **非本人脸型**；注明使用的是女性或男性平均脸底图。
