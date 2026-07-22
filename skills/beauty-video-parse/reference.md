# 视频解析 — 技术参考

面向 Agent 与维护者。实现入口：`packages/video-parse`（CLI：`scripts/parse_beauty_video.py`）。

## 外部服务

| 用途 | 模型/服务 | 说明 |
|------|-----------|------|
| 步骤切分、字幕/OCR、关键帧时间建议 | `qwen3.7-plus` | DashScope `MultiModalConversation`，`response_format: json_object`，非 thinking |
| 口播转写 | `fun-asr` | `Transcription.async_call`；音频先 `OssUtils.upload` 再 `file_urls` |
| JSON 修复（可选） | `qwen3.5-flash` | 视觉返回非合法 JSON 时 |

**Base URL（大陆）**：`https://dashscope.aliyuncs.com/api/v1`  
**OpenAI 兼容修复**：`https://dashscope.aliyuncs.com/compatible-mode/v1`

## 本地视频输入

- Windows：`file://D:/path/to.mp4`（正斜杠）
- 视觉 API 本地 file 上限约 **100MB**；超出则在 run 目录生成 `upload_proxy.mp4`（H.264 迭代压缩）

## 视觉请求要点

- 消息含 `{"video": "<file_uri>", "fps": 1.5}`（教程可 1.5～2.0）
- System prompt 要求唯一 JSON：`steps[]` + 可选 **`replication_hints`**（见 [makeup-replication-refs.md](makeup-replication-refs.md)）
- **步骤主类与细分**须符合 [step-taxonomy.md](step-taxonomy.md)
- Prompt 中须含 **JSON** 字样以满足 structured output
- `replication_hints.tail_after_sec` **不得**指向片头预告或对比素颜侧；hints **仅作复刻回退**（主策略为步骤边界，见 [makeup-replication-refs.md](makeup-replication-refs.md) refs v1.2）
- 实现侧：hint 抽帧后须过单帧 `replication_after` L2，失败则扫描/再回退

## ASR 要点

- 从原视频抽取：`ffmpeg -vn -ac 1 -ar 16000 audio.wav`
- 句段时间：`begin_time` / `end_time` 为**毫秒** → 转为秒写入 `transcript.json`
- 归入 step：计算 ASR 段与 `time_range` 重叠时长，归入重叠最大的一步

## ffmpeg / ffprobe

- 解析顺序：PATH → `~/.local/ffmpeg/bin/ffmpeg.exe`（Windows）
- 子进程：`encoding=utf-8`, `errors=replace`
- 关键帧：`ffmpeg -ss <sec> -i <source> -frames:v 1 -q:v 2 <out.jpg>`（`-ss` 在 `-i` 前）

## Run 目录产物

| 文件 | 说明 |
|------|------|
| `analysis.json` | 主输出（v2 或 v2.1） |
| `meta.json` | probe、API 耗时、`replication_refs`（v2.1）、`keyframe_qa`（含 `l2_retried_frames` / `l2_rescued`，v2.2） |
| `transcript.json` | ASR segments + raw |
| `keyframes/*.jpg` | 步级 + `复刻-妆前/妆后-*` |
| `keyframe-qa.json` | 步级 L1/L2 + 可选 `l2_retry`（v2.2）+ `replication_pair` |
| `replication_hints.json` | vision hints 快照（可选） |
| `upload_proxy.mp4` | 可选 |
| `audio.wav` | ASR 输入 |
| `raw_vision_response.txt` | 调试 |

## CLI 模式（`--mode`）

入口参数（`scripts/parse_beauty_video.py` / `parse-beauty-video.ps1`）：

| 值 | 行为 |
|----|------|
| `full`（默认） | `enable_keyframe_qa=True`：L1 抽帧 + 逐步 L2 Vision |
| `fast` | `enable_keyframe_qa=False`：仅 L1 抽帧，跳过 L2（省墙钟） |

`--skip-keyframe-qa` 与 `fast` 任一为真即关 L2。`meta.json` 写入 `mode` 与 `enable_keyframe_qa`。串联脚本 `run_beauty_replicate.py` / `run-beauty-replicate.ps1` 同样支持 `--mode` / `-Mode`（仅在 `--video` 触发 parse 时生效）。

`fast` **不**默认关闭复刻参考；需要时另加 `--skip-replication-refs`。正式关键帧验收用 `full`。

## CLI 进度

默认向 **stderr** 打印固定 10 阶段进度，格式：`[<n>/10] <说明>… (Ns)`。不要求真实百分比（Vision/ASR 时长不可预知）。跳过的步骤仍占序号（例如跳过复刻时打印 `[8/10] 跳过复刻参考`）。

实现：`ParseConfig.on_progress`；CLI 默认注入 stderr 打印；宿主可自备回调。

| 序号 | 阶段 |
|------|------|
| 1 | Probe |
| 2 | Prepare / 压缩（未触发则注明跳过） |
| 3 | 抽音频 |
| 4 | Vision API |
| 5 | ASR（可与 4 并行，文案可标「并行中」） |
| 6 | Merge + taxonomy |
| 7 | 步级关键帧 + QA（含子进度：步骤 i/N；L2 重抽文案待重抽实现） |
| 8 | 复刻参考（可跳过） |
| 9 | Schema 校验 |
| 10 | 写盘完成 |

关闭方式：CLI `--quiet`，或环境变量 `BEAUTY_PARSE_QUIET=1`。

## 常见失败

| 现象 | 方向 |
|------|------|
| 未找到 ffmpeg | 安装至 PATH 或 `~/.local/ffmpeg/bin` |
| GBK / UnicodeDecodeError | subprocess UTF-8（已修） |
| 视觉 API 失败 | 查 `raw_vision_error.txt`、文件大小、密钥区域 |
| ASR 失败 | OSS 上传、音频过长、配额 |
| schema 失败 | 补全 step/keyframe；或走 JSON 修复 |
| 压缩后仍 &gt;100MB | 提高 CRF/降分辨率或缩短源视频 |
| 步级关键帧 L2 仍 failed | 查 `keyframe-qa.json` 的 `l2_retry` / `reason`；确认实现已按 v2.2 窗内重抽 |

## 与下游产品模型映射（Phase 2）

解析输出是**中性**的「视频理解结果」。本 skill **不**生成 `visual_layers` 或跟练清单。

Phase 2 由独立包 [`tutorial-mapper`](../../packages/tutorial-mapper/) / Skill [`tutorial-mapper`](../tutorial-mapper/) 消费 `analysis.json`：

| analysis 字段 | 产品模型 |
|---------------|----------|
| `steps[]` | Tutorial.steps（Step） |
| `time_range` | `video_clip.{start,end}` |
| `taxonomy.primary` | `part`（腮红→cheek 等） |
| `text.*` / ASR | 弱 `instruction`；文本 LLM 补 title/tags/product |
| `keyframes/` | 缩略图锚点；视觉 LLM 补 `visual_layer` |

```powershell
.\.venv\Scripts\python.exe .\scripts\map_tutorial_from_parse.py --parse-run outputs\runs\<timestamp>
```

产物：`tutorial.json`（`contract_version: tutorial.v1`）、`enrichment_meta.json`。
