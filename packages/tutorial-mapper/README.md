# tutorial-mapper

将 `beauty-video-parse` 产出的 `analysis.json` 映射为跟练产品模型：

- **Tutorial**（教程对象）
- **Step**（步骤对象）
- **Part Asset**（部位资产对象）

## 用法

```powershell
cd "<repo-root>"
.\.venv\Scripts\pip.exe install -e packages\tutorial-mapper
.\.venv\Scripts\python.exe .\scripts\map_tutorial_from_parse.py --parse-run outputs\runs\<timestamp>
```

确定性映射始终执行；文本 / 视觉 enrichment 默认开启（可用 `--skip-text-enrich` / `--skip-vision-enrich` 关闭）。

产物写在 parse run 目录：`tutorial.json`、`enrichment_meta.json`（含 `tutorial_step_validation` 步骤语义校验与 `stages.step_validation`）。

`scripts/map_tutorial_from_parse.py` 与 `scripts/run_beauty_replicate.py` 在 stderr / job 日志中打印校验摘要；**warn_write**：`pass=false` 时仍写 `tutorial.json`。

## 边界

- 不修改 `beauty_video_analysis` 契约。
- `video_clip` 时间轴只来自 `analysis.steps[].time_range`，不臆造。
- `visual_layer` 等缺字段由二次 LLM / 关键帧补齐，非 parse skill 职责。
