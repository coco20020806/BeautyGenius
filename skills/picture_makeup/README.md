# picture-makeup

按 [`tutorial.json`](../../packages/tutorial-mapper/tutorial_mapper/schemas/tutorial.v1.json) 逐步生成 **模块图示**（色块标注着色范围）。

| 文档 | 说明 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 主流程 |
| [step-prompt-qwen.md](step-prompt-qwen.md) | base_prompt |
| [keyframe-enrich-qwen.md](keyframe-enrich-qwen.md) | 关键帧 enrich |
| [diagram-prompt-wan.md](diagram-prompt-wan.md) | wan 单图生成 |
| [output-contract.md](output-contract.md) | 输出契约 |
| [reference.md](reference.md) | API 与故障 |
| [examples.md](examples.md) | 示例 |
| [module-structure.md](module-structure.md) | Phase 2 包化 |

**底图模板**：[`image_format.png`](image_format.png)（skill 根目录，运行 wan 前须可读）。

上游：[`tutorial-mapper`](../tutorial-mapper/) · [`beauty-video-parse`](../beauty-video-parse/)。
