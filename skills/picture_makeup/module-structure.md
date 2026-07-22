# picture-makeup 模块结构

Skill 文档 canonical 路径：`<repo-root>/skills/picture_makeup/`（与 [skills/README.md](../README.md) 一致）。

## 设计原则

1. **Skill 管「怎么做」** — 本目录 `.md` 给 Agent；不含密钥。  
2. **v1 无独立包** — Agent 按文档调用 DashScope；契约见 [output-contract.md](output-contract.md)。  
3. **上游** — 只读 `tutorial.v1` 与 parse `keyframes/`。  
4. **wan 形态** — 单图 `image_format.png`，非 [`kol-makeup-preview`](../kol-makeup-preview/) 三图 transfer。

## 当前布局

```text
Beauty Genius/
├── skills/picture_makeup/          # 本 Skill
│   ├── SKILL.md
│   ├── image_format.png            # 用户提供的底图模板（运行必需）
│   ├── step-prompt-qwen.md
│   ├── keyframe-enrich-qwen.md
│   ├── diagram-prompt-wan.md
│   └── output-contract.md
├── skills/tutorial-mapper/         # 上游 tutorial.json
├── skills/beauty-video-parse/      # 上游 keyframes
├── packages/makeup-preview/        # wan 调用参考（transfer 多图）
├── packages/picture-makeup/        # 本 Skill 可执行包
├── scripts/run_picture_makeup.py
└── outputs/picture-makeup/runs/    # CLI / API 落盘
```

## 边界

| 模块（Phase 2 计划） | 职责 | 禁止 |
|----------------------|------|------|
| `prompt_text` | qwen base_prompt | 读关键帧 |
| `prompt_enrich` | qwen appendix | 改 base_prompt |
| `diagram` | wan2.7-image-pro | 解析视频 |
| `pipeline` | run 目录、manifest | UI |

## Phase 2（可选包化）

对齐 [`kol-makeup-preview/module-structure.md`](../kol-makeup-preview/module-structure.md)：

```text
packages/picture-makeup/
└── picture_makeup/
    ├── pipeline.py
    ├── prompt_text.py
    ├── prompt_enrich.py
    └── diagram.py
scripts/run_picture_makeup.py
```

公开 API 草案：

```python
def run_picture_makeup_job(
    *,
    parse_run_dir: Path,
    output_root: Path,
    config: PictureMakeupConfig,
    step_ids: list[str] | None = None,
) -> PictureMakeupJobResult: ...
```

`PictureMakeupConfig.skill_dir` 默认 `skills/picture_makeup`。

## 实现状态

| 项 | 状态 |
|----|------|
| Skill 文档 | 已建立 |
| `image_format.png` | 已存在于 skill 根目录（跟练图示底图模板） |
| `packages/picture-makeup` | 已实现：`run_picture_makeup_job` |
| `scripts/run_picture_makeup.py` | 步骤图示 CLI |
| Web API | `POST/GET …/step-diagrams`（按需，见 api-server） |
