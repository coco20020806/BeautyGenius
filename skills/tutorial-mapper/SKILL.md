---
name: tutorial-mapper
description: >-
  Maps beauty-video-parse analysis.json into Tutorial / Step / Part Asset product
  models for follow-along makeup. Use after a parse run exists, when the user
  asks for tutorial.json, step objects, visual_layer, practice checklist, or
  part assets for downstream practice flows.
---

# Tutorial Mapper

将美妆视频解析产物映射为跟练产品模型（**不**改动 `beauty_video_analysis` 契约）。

## 何时使用

- 已有 `outputs/runs/<ts>/analysis.json`，需要 `tutorial.json`。
- 需要 Step 的 `video_clip` / `instruction` / `product` / `visual_layer`。
- 需要按部位聚合的 Part Asset（`eye_001` 等）。

## 快速执行

```powershell
cd "<repo-root>"
.\.venv\Scripts\pip.exe install -e packages\tutorial-mapper
.\.venv\Scripts\python.exe .\scripts\map_tutorial_from_parse.py --parse-run "outputs\runs\<timestamp>"
```

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
5. 刷新 assets + `tutorial.v1` schema 校验
6. 写 `tutorial.json`、`enrichment_meta.json`

## 字段来源原则

| 字段 | 来源 |
|------|------|
| `video_clip` | 仅 `analysis.steps[].time_range`（禁止臆造） |
| `part` / `step_id` | taxonomy 主类映射表 |
| `title` / tags / checklist | 文本 LLM |
| `visual_layer` | 关键帧视觉 LLM |
| 空字段 | 允许 `unknown` / `{}` / `[]` |

## 验收

- [ ] run 目录含 `tutorial.json`、`enrichment_meta.json`
- [ ] `contract_version` 为 `tutorial.v1`
- [ ] 每步 `video_clip.start/end` 与 parse 时间轴一致
- [ ] schema 校验通过

## 实现

- 包：`packages/tutorial-mapper/`
- Schema：`packages/tutorial-mapper/tutorial_mapper/schemas/tutorial.v1.json`
- 上游：[`beauty-video-parse`](../beauty-video-parse/)
