---
name: beauty-video-parse
description: >-
  Parses makeup tutorial videos into step timelines, subtitles, on-screen text,
  voiceover (ASR), per-step keyframes, and tail before/after replication refs
  via DashScope (qwen3.7-plus + fun-asr) and ffmpeg. Use when the user uploads
  or paths a beauty/makeup tutorial video, asks for video parsing, step breakdown,
  keyframe extraction, makeup replication references, or analysis.json output.
---

# Beauty Video Parse

美妆教程**视频解析**：输入本地视频 → 输出带时间轴的结构化 JSON + 关键帧目录 +（默认）片尾复刻参考对。

## 何时使用

- 用户给出**本地视频路径**或要在 Beauty Genius 中跑解析流水线。
- 需要 **步骤时间轴**、口播/字幕/画面文字、**每步关键帧**、**片尾成妆 + 妆前基线（复刻参考）**。
- 扩展解析逻辑、排查 DashScope/ffmpeg 失败、验收 `analysis.json`。

**不在本 skill 范围（Phase 2+）**：抖音链接下载、用户脸上妆 transfer 模型本身、Web API 部署（见 [module-structure.md](module-structure.md)）。

## 快速执行（Beauty Genius 仓库）

依赖：`ffmpeg`、`Python 3.10+`、`DASHSCOPE_API_KEY`（或 `scripts/_qwen_local.py`）。

```powershell
cd "<repo-root>"
.\scripts\parse-beauty-video.ps1 -VideoPath "<absolute-path-to.mp4>"
```

冒烟 / 省时（跳过 L2 关键帧视觉质检，仍 L1 抽帧）：

```powershell
.\scripts\parse-beauty-video.ps1 -VideoPath "<absolute-path-to.mp4>" -Mode fast
```

Linux/macOS 等价：

```bash
python scripts/parse_beauty_video.py --video /path/to/video.mp4
python scripts/parse_beauty_video.py --video /path/to/video.mp4 --mode fast
```

成功时打印 `outputs/runs/<timestamp>/`；主交付物为 `analysis.json`（v2.1 含 `makeup_replication_refs`）与 `keyframes/`。

`--mode full`（默认）开启逐步 L2；`--mode fast` 关闭 L2（`meta.mode` / `enable_keyframe_qa=false`，`keyframe-qa.json` 标 `l2_skipped`）。正式验收用 `full`。也可用 `--skip-keyframe-qa` 与 `fast` 等价叠加。

默认在 **stderr** 输出阶段进度（见下方「CLI 进度」）；可用 `--quiet` 或 `BEAUTY_PARSE_QUIET=1` 关闭。

## 流水线（Agent 应理解的顺序）

1. **Probe** — ffprobe 时长、fps。
2. **Prepare** — 若 &gt;100MB，压缩为 run 内 `upload_proxy.mp4` 再调视觉 API；关键帧与复刻帧仍从**原视频**截取。
3. **Extract audio** — 16k mono `audio.wav`。
4. **Parallel** — `fun-asr` 与 `qwen3.7-plus`（structured JSON，含 `steps` + `replication_hints`）。
5. **Merge** — ASR 归入 `text.voiceover`；normalize taxonomy；步级 keyframe 元数据与文件名。
6. **Taxonomy coverage** — 写入 `taxonomy-coverage.json`。
7. **Step keyframes + QA** — ffmpeg 抽步级帧 → L1 → 步级批量 L2 → **失败帧在步骤时间窗内固定步长重抽** → 写 `keyframe-qa.json`（步级部分）。见 [keyframe-validation.md](keyframe-validation.md)。
8. **Replication refs** — before：时间序第一步 `step_start_face`；after：时间序最后非 skipped 化妆主类步骤结束全脸（失败再片尾回退）。见 [makeup-replication-refs.md](makeup-replication-refs.md)（refs v1.2）。可 `--skip-replication-refs` 跳过，契约保持 v2。
9. **Validate** — **一次** `jsonschema`（v2 或 v2.1 schema）。
10. **Write** — `analysis.json`、`meta.json`（含 `replication_refs` 汇总）。

## CLI 进度

解析耗时长，CLI **默认**向 stderr 打印阶段进度，格式：`[<n>/10] <阶段说明>…`，附已用时 `(Ns)`。不要求不可预知的百分比（Vision/ASR）；以阶段名 + 子步骤为主。

| 序号 | 阶段 | 示例文案 |
|------|------|----------|
| 1 | Probe | `[1/10] Probe…` |
| 2 | Prepare | `[2/10] Prepare（压缩上传代理）…`；未触发压缩可写 `跳过压缩` |
| 3 | 抽音频 | `[3/10] 抽取音频…` |
| 4 | Vision | `[4/10] Vision 分析中…` |
| 5 | ASR | `[5/10] ASR 转写中…`；与 4 并行时双方可标「并行中」 |
| 6 | Merge | `[6/10] Merge + taxonomy…` |
| 7 | 步级关键帧 + QA | `[7/10] 关键帧 QA（步骤 2/7）…`；L2 重抽时 `[7/10] L2 重抽 定妆 step_end_face…` |
| 8 | 复刻参考 | `[8/10] 复刻参考对…`；`--skip-replication-refs` 时打印 `跳过复刻参考` 仍占序号 8 |
| 9 | Schema | `[9/10] Schema 校验…` |
| 10 | 写盘 | `[10/10] 写盘完成` |

关闭进度：`--quiet` 或环境变量 `BEAUTY_PARSE_QUIET=1`。详见 [reference.md](reference.md)、[examples.md](examples.md)。

## Agent 工作约束

- 改解析行为前阅读 [reference.md](reference.md)、[output-contract.md](output-contract.md)、[makeup-replication-refs.md](makeup-replication-refs.md)、[keyframe-validation.md](keyframe-validation.md)。
- **步骤切分与命名**必须对照 [step-taxonomy.md](step-taxonomy.md)；复刻参考**不是**第 13 个主类。
- **密钥**不得写入 Git。
- Windows subprocess 读 ffmpeg 输出须 **UTF-8 + errors=replace**。
- 视觉模型**不读视频音轨**；口播必须走 ASR。
- 完成里程碑后更新 [module-structure.md](module-structure.md)「实现状态」。

## 验收清单

- [ ] run 目录含 `analysis.json`、`meta.json`、`transcript.json`、`keyframes/`、`taxonomy-coverage.json`、`keyframe-qa.json`
- [ ] 启用复刻时 `contract_version` 为 **v2.1** 且含 `makeup_replication_refs`；跳过时为 **v2**
- [ ] 每步含 `taxonomy.primary` / `sub_steps`；步级 `keyframes` ≥ 2
- [ ] `复刻-妆前-*` 对应时间序第一步的 `step_start_face`（`source: first_step_start`）
- [ ] `复刻-妆后-*` 对应时间序最后非 skipped 化妆主类步骤结束处（`last_step_end` / `last_step_scan`）；非对比卡素颜
- [ ] `replication_after` 单帧 L2 含 **`makeup_complete`**；Pair 不能代替单帧判定
- [ ] `pair_validation.pass` 为 false 或 after 单帧失败时下游不得静默用于自动复刻
- [ ] 步级 QA：L2 失败优先**窗内自动重抽**；`summary.l2_rescued` 可解释挽回数；仍 `failed` 的项再人工复核
- [x] CLI 默认有 `[n/10]` 阶段进度；`--quiet` / `BEAUTY_PARSE_QUIET=1` 可关闭

## 延伸阅读

| 文档 | 内容 |
|------|------|
| [reference.md](reference.md) | 模型、端点、限制、错误处理、CLI 进度 |
| [output-contract.md](output-contract.md) | JSON 与 run 目录契约（v2 / v2.1） |
| [makeup-replication-refs.md](makeup-replication-refs.md) | 片尾 before/after 复刻参考 |
| [step-taxonomy.md](step-taxonomy.md) | 化妆步骤 taxonomy |
| [keyframe-validation.md](keyframe-validation.md) | 关键帧 L1/L2 / L2 重抽 / Pair QA |
| [taxonomy-enums.json](taxonomy-enums.json) | 机器可读枚举 |
| [examples.md](examples.md) | 命令与样例 |
| [module-structure.md](module-structure.md) | 可复用包与演进 |
| 下游 | [`tutorial-mapper`](../tutorial-mapper/) 消费 `analysis.json` → `tutorial.json`，并在 mapper 内做**重复步语义校验**（非 parse 阶段合并；同一 `taxonomy_primary` 可多 step）；[`kol-makeup-preview`](../kol-makeup-preview/) 消费 `makeup_replication_refs.after`；串联 [`docs/REPLICATE_PIPELINE.md`](../../docs/REPLICATE_PIPELINE.md) |

Machine-readable schema：`packages/video-parse/video_parse/schemas/beauty_video_analysis.v2.json` / `beauty_video_analysis.v2.1.json`。
