# kol-makeup-preview 模块结构

Skill 文档 canonical 路径：`<repo-root>/skills/kol-makeup-preview/`（与 [skills/README.md](../README.md) 一致）。

## 设计原则

1. **Skill 管「怎么做」** — 本目录 `.md` 给 Agent；不含密钥。  
2. **包管「跑什么」** — `packages/makeup-preview` 提供 `run_preview_job`。  
3. **契约稳定** — [output-contract.md](output-contract.md)。  
4. **上游** — 只读 [beauty-video-parse/output-contract.md](../beauty-video-parse/output-contract.md) v2。

## 目标布局

```text
Beauty Genius/
├── skills/kol-makeup-preview/          # 本 Skill（源码在此）
├── skills/beauty-video-parse/        # 上游解析 Skill
├── packages/makeup-preview/          # 待建 / 演进中
│   └── makeup_preview/
│       ├── pipeline.py
│       ├── reference_pick.py
│       ├── face_gate.py
│       ├── face_qa.py
│       └── transfer.py
├── scripts/run_makeup_preview.py
└── outputs/makeup-preview/runs/
```

## 边界

| 模块 | 职责 | 禁止 |
|------|------|------|
| `reference_pick` | 读 analysis.json 选帧 | 调生成模型 |
| `face_gate` | L0/L1 MediaPipe | 妆容生成 |
| `face_qa` | L2 Qwen JSON | 改参考帧逻辑 |
| `transfer` | wan2.7-image-pro | 视频解析 |
| `pipeline` | run 目录、preview.json | UI |

## 公开 API（计划）

```python
def run_preview_job(
    *,
    parse_run_dir: Path | None,
    reference_image: Path | None,
    user_photo: Path | None,
    use_baseline: bool,
    output_root: Path,
    config: PreviewConfig,
) -> PreviewJobResult: ...
```

`PreviewConfig.skill_dir` 默认指向 repo 内 `skills/kol-makeup-preview`。

## 实现状态

| 项 | 状态 |
|----|------|
| Skill 文档 | 已建立；**transfer 三图 v2** **已实现** [transfer-prompt.md](transfer-prompt.md) |
| `packages/makeup-preview` | 已实现：`run_preview_job`、L0–L2 质检、**三图 transfer**（缺妆前回退二图 v1） |
| `scripts/run_makeup_preview.py` | 预览 CLI |
| `scripts/run_beauty_replicate.py` | 解析 + 预览 + manifest |
| `scripts/run-beauty-replicate.ps1` | PowerShell 串联入口 |
| 底图 PNG | Skill 根目录 `female_average_face.png` / `male_average_face.png` |
| 上游 after 选帧纠错 | 依赖 [makeup-replication-refs.md](../beauty-video-parse/makeup-replication-refs.md) refs v1.1（parse 侧代码待做） |

## Phase 2

Web 上传用户照 → 异步 preview job；与 parse-worker 并列。
