---
name: tutorial-mapper
description: >-
  Maps beauty-video-parse analysis.json into Tutorial / Step / Part Asset product
  models for follow-along makeup, with post-map step semantic validation (duplicate
  step detection). Use after a parse run exists, when the user asks for tutorial.json,
  step objects, visual_layer, practice checklist, or part assets for downstream practice flows.
---

# Tutorial Mapper

将美妆视频解析产物映射为跟练产品模型（**不**改动 `beauty_video_analysis` 契约）。

## 何时使用

- 已有 `outputs/runs/<ts>/analysis.json`，需要 `tutorial.json`。
- 需要 Step 的 `video_clip` / `instruction` / `product` / `visual_layer`。
- 需要按部位聚合的 Part Asset（`eye_001` 等）。
- 需要检查 tutorial **重复步骤**（非「主类只能出现一次」）。

## 快速执行

```powershell
cd "<repo-root>"
.\.venv\Scripts\pip.exe install -e packages\tutorial-mapper
.\.venv\Scripts\python.exe .\scripts\map_tutorial_from_parse.py --parse-run "outputs\runs\<timestamp>"
```

映射完成后 stderr 会打印 `tutorial_step_validation` 摘要；详情在 run 目录 `enrichment_meta.json`。

也可由串联脚本自动触发（parse 之后、preview 之前）：

```powershell
.\scripts\run-beauty-replicate.ps1 -ParseRun "outputs\runs\<timestamp>" -UseBaseline -SkipTransfer
# 跳过映射：-SkipTutorialMap；fast 仅确定性：-Mode fast
```

仅确定性映射（不调 LLM）：

```powershell
.\.venv\Scripts\python.exe .\scripts\map_tutorial_from_parse.py --parse-run "outputs\runs\<timestamp>" --skip-text-enrich --skip-vision-enrich
```

## 流水线

1. 读 `analysis.json`
2. **确定性映射**：`time_range` → `video_clip`，`taxonomy.primary` → `part`，拼口播为弱 `instruction`
3. **文本 enrichment**（可选）：ASR/字幕 → title、tags、difficulty、product、adaptation_note、checklist
4. **视觉 enrichment**（可选）：关键帧或缺帧时 clip 中点截图 → `visual_layer`
5. 刷新 assets
6. **5a** **展示分组 + `display_title`**（`apply_display_grouping`）→ `step_groups[]` / 每步 `display_title`、`display_group_id`；见 [display-grouping.md](display-grouping.md)
7. **5b** `tutorial.v1` schema 校验（`validate_tutorial`）
8. **5c** **步骤语义校验**（`validate_tutorial_steps`）→ 写入 `enrichment_meta.tutorial_step_validation`；见 [step-validation.md](step-validation.md)
9. 写 `tutorial.json`、`enrichment_meta.json`（**warn_write**：有 error  issue 仍写 tutorial）

## Agent 工作约束

- 改校验规则前阅读 [step-validation.md](step-validation.md) 与 [output-contract.md](output-contract.md)。
- 改展示分组规则前阅读 [display-grouping.md](display-grouping.md)。
- **禁止**用「`taxonomy_primary` 全局唯一」验收 tutorial。
- 同一主类下**允许多个** step；只拦**重复解析**（重叠 clip / 雷同 instruction）。
- 跟练页卡片编号读 `step_groups`，**禁止**仅用扁平下标拼「步骤 N · taxonomy_primary」导致同名双卡。
- 改阈值或 issue 码须同步 Skill 与 `packages/tutorial-mapper/tutorial_mapper/step_validation.py`。
- 改分组/标题算法须同步 `packages/tutorial-mapper/tutorial_mapper/display_grouping.py`。

## 字段来源原则

| 字段 | 来源 |
|------|------|
| `video_clip` | 仅 `analysis.steps[].time_range`（禁止臆造） |
| `part` / `step_id` | taxonomy 主类映射表 |
| `step_groups` / `display_title` / `display_group_id` | 确定性（连续同主类分组） |
| `title` / tags / checklist | 文本 LLM |
| `visual_layer` | 关键帧视觉 LLM |
| 空字段 | 允许 `unknown` / `{}` / `[]` |

## 验收

- [ ] run 目录含 `tutorial.json`、`enrichment_meta.json`
- [ ] `contract_version` 为 `tutorial.v1`
- [ ] 每步 `video_clip.start/end` 与 parse 时间轴一致
- [ ] schema 校验通过
- [ ] 含 `step_groups[]`；每步有 `display_title`、`display_group_id`
- [ ] 连续同 `taxonomy_primary` 多 step → **一组**；组内 `display_title` 互异
- [ ] `enrichment_meta.tutorial_step_validation` 存在
- [ ] 同 primary 多 step、clip 不重叠时 `pass: true`（如两段唇妆 0–36 / 36–80）
- [ ] 重叠 clip 或重复 instruction 时产生对应 `issue.code`

## 延伸阅读

| 文档 | 内容 |
|------|------|
| [display-grouping.md](display-grouping.md) | 展示分组与 display_title |
| [step-validation.md](step-validation.md) | 重复步规则与 issue 码 |
| [output-contract.md](output-contract.md) | enrichment_meta 校验块 |
| [beauty-video-parse](../beauty-video-parse/SKILL.md) | 上游 parse |

## 实现

- 包：`packages/tutorial-mapper/`
- Schema：`packages/tutorial-mapper/tutorial_mapper/schemas/tutorial.v1.json`
- 展示分组：`tutorial_mapper/display_grouping.py`
- 步骤校验：`tutorial_mapper/step_validation.py`
