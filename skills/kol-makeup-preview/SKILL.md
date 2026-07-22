---
name: kol-makeup-preview
description: >-
  Applies KOL/tutorial full-face makeup from a beauty-video-parse reference frame
  onto the user's frontal selfie or a Chinese average-face baseline using
  wan2.7-image-pro. Validates user photos with MediaPipe pose gates and Qwen
  QA. Use when the user wants makeup transfer, KOL look preview, 抄整妆, or
  personal face adaptation after video parse.
disable-model-invocation: true
---

# KOL Makeup Preview（抄整妆个人预览）

Skill 源码目录：`<repo-root>/skills/kol-makeup-preview/`（Beauty Genius 仓库内 [`skills/kol-makeup-preview/`](README.md)）。

从美妆解析 run 或手动参考图取 **KOL 完成妆面**，生成 **个人脸部适配预览**（或中国平均脸底图预览）。

## 何时使用

- 用户已有或即将有 [`beauty-video-parse`](../beauty-video-parse/) 的 `outputs/runs/...`。
- 用户要 **抄 KOL 整妆**、看妆效在自己脸上或底图上的效果。
- 需要 **校验用户上传的正脸自拍** 再调用生成。

**不在本 skill**：教程视频解析、Face++ 试妆 SKU、逐帧视频换妆（v1 仅静态预览）。

## 对用户话术（原文，勿改写）

进入本能力后，先对用户说：

> 你可以上传一张**本人正脸照片**，我们会把教程/KOL 的整妆效果适配到你的脸上并生成预览。  
> - **若上传**：生成**个人脸部适配预览**。  
> - **若不上传**：将使用**中国平均脸底图**作为目标脸，仅展示妆效参考（非你的脸型）。

未收到用户照片前，走 **不上传** 分支或等待上传；不得默认用户已授权使用其生物特征。

## 快速执行（Beauty Genius 仓库）

依赖：`DASHSCOPE_API_KEY`、Python 3.10+、（L1）MediaPipe；上游可选 parse run。

```powershell
cd "<repo-root>"
python scripts/run_makeup_preview.py --parse-run "outputs/runs/<timestamp>" --user-photo "D:\path\selfie.jpg"
# 不上传，使用平均脸底图（默认女性；男性加 --baseline male）：
python scripts/run_makeup_preview.py --parse-run "outputs/runs/<timestamp>" --use-baseline
python scripts/run_makeup_preview.py --parse-run "outputs/runs/<timestamp>" --use-baseline --baseline male
```

成功时输出 `outputs/makeup-preview/runs/<timestamp>/`；主交付物见 [output-contract.md](output-contract.md)。

## 流水线（Agent 顺序）

1. **Prompt** — 使用上文「对用户话术」。
2. **Resolve reference** — [reference-selection.md](reference-selection.md)：优先 parse run 的 **`makeup_replication_refs.after`** + **`before`**（v2.1）；无则建议重跑 parse（勿 `--skip-replication-refs`）。
3. **Resolve target** — 用户图 **或** 平均脸底图（[baselines.md](baselines.md)：`female_average_face.png` / `male_average_face.png`）。
4. **Validate user photo**（仅上传）— [face-validation.md](face-validation.md)：L0 → L1 MediaPipe → L2 Qwen；失败则 [user-flow.md](user-flow.md) 指引重拍。
5. **Transfer** — [transfer-prompt.md](transfer-prompt.md) **v2 三图**（妆后 + 教程妆前 + 目标脸）；缺妆前则降级 v1 二图并 warning。
6. **Write run** — `preview.json`、`preview_*.jpg`、`user-photo-qa.json`（若有）。
7. **Report** — 底图分支须说明「非本人脸型」；上传分支展示预览图路径。

## Agent 约束

- 密钥不得写入 Git；仅环境变量或 gitignore 本地文件。
- 改质检阈值须同步 `face-validation.md` 与 `packages/makeup-preview/` 内常量。
- 参考帧优先用 parse 中 `validation.pass=true` 的关键帧；after 须为真正成妆（见上游 [makeup-replication-refs.md](../beauty-video-parse/makeup-replication-refs.md)）。

## 验收清单

- [ ] 已提示用户可上传本人照片（原文三 bullet）
- [ ] 上传：`user-photo-qa.json` 且 `pass=true`
- [ ] 未上传：`target.type=average_baseline`，`target.baseline` 为 female/male，且已说明非本人脸型
- [ ] `reference.jpg` 与至少一张 `preview_*.jpg`
- [x] 有 parse before 时：`tutorial_before.jpg` 存在且 `transfer.prompt_version` 为 **v2**
- [x] 无 before 时：`warnings` 含 `transfer_without_tutorial_before`，`prompt_version` 为 v1
- [ ] `preview.json` 含 `contract_version`

## 延伸阅读

| 文档 | 内容 |
|------|------|
| [user-flow.md](user-flow.md) | 状态机与重试 |
| [face-validation.md](face-validation.md) | 平视正脸规则 |
| [reference-selection.md](reference-selection.md) | KOL 参考帧 |
| [transfer-prompt.md](transfer-prompt.md) | 多图 prompt |
| [output-contract.md](output-contract.md) | 输出契约 |
| [reference.md](reference.md) | API 与依赖 |
| [examples.md](examples.md) | 样例 |
| [baselines.md](baselines.md) | 女性/男性平均脸 PNG 路径 |
| [module-structure.md](module-structure.md) | 包与 Phase 2 |

上游契约：[beauty-video-parse/output-contract.md](../beauty-video-parse/output-contract.md)。  
端到端串联：[docs/REPLICATE_PIPELINE.md](../../docs/REPLICATE_PIPELINE.md)。

## 输入与输出（摘要）

见 [io-summary.md](io-summary.md)。
