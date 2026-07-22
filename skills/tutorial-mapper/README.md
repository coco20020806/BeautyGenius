# tutorial-mapper

将 `analysis.json` 映射为跟练用 `tutorial.json` 的 **Cursor Agent Skill** 文档包。

**Canonical 路径**：`<repo-root>/skills/tutorial-mapper/`

实现：`packages/tutorial-mapper/` · CLI：`scripts/map_tutorial_from_parse.py`

## 文件说明

| 文件 | 用途 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 主指令 |
| [display-grouping.md](display-grouping.md) | 展示分组 + `display_title` |
| [step-validation.md](step-validation.md) | tutorial 生成后步骤语义校验 |
| [output-contract.md](output-contract.md) | tutorial + enrichment_meta 契约 |
| 上游 | [beauty-video-parse](../beauty-video-parse/) |

## 安装到 Cursor

复制或 junction 本目录到 `.cursor/skills/tutorial-mapper/` 或 `~/.cursor/skills/tutorial-mapper/`。
