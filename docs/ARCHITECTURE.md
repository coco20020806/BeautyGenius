# 架构草案

## 目标

用户上传美妆视频 → Agent 解析 → 输出结构化知识（教程步骤、产品提及、肤质/场景标签等）→ 支持回顾与检索。

## 建议分层

1. **接入层**：视频上传、URL 提交、任务状态查询
2. **解析层**：下载/读本地文件、抽帧、转写（watch skill / yt-dlp + ffmpeg + Whisper）
3. **理解层**：LLM 将多模态信号转为结构化笔记与摘要
4. **沉淀层**：持久化笔记、标签、用户收藏与搜索（后续迭代）

## 当前状态

- 视频解析 MVP：`scripts/parse_beauty_video.py`（DashScope + ffmpeg）
- **Tutorial 映射（Phase 2）**：`scripts/map_tutorial_from_parse.py` → `tutorial.json`（[`packages/tutorial-mapper/`](../packages/tutorial-mapper/)）
- **可复用 Skill 文档（canonical：`skills/`）**：[`skills/README.md`](../skills/README.md)
  - 视频解析：[`skills/beauty-video-parse/`](../skills/beauty-video-parse/)
  - Tutorial 映射：[`skills/tutorial-mapper/`](../skills/tutorial-mapper/)
  - KOL 整妆预览：[`skills/kol-makeup-preview/`](../skills/kol-makeup-preview/)
- **串联路径**：[`docs/REPLICATE_PIPELINE.md`](REPLICATE_PIPELINE.md)（parse → replication after → preview → `outputs/jobs/` manifest）
- 接入层 / Web / 沉淀层：待建设
