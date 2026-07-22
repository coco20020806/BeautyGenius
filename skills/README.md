# Beauty Genius — Agent Skills（canonical 路径）

本仓库 **Skill 文档的唯一源码目录**：

```text
C:\Users\fei.kong\Desktop\Beauty Genius\skills\
```

（克隆到其他机器时等价于 `<repo-root>/skills/`。）

## 已有 Skill

| 目录 | name | 说明 |
|------|------|------|
| [beauty-video-parse/](beauty-video-parse/) | `beauty-video-parse` | 美妆教程视频解析 → `analysis.json` + 关键帧 |
| [tutorial-mapper/](tutorial-mapper/) | `tutorial-mapper` | `analysis.json` → Tutorial / Step / Part Asset（`tutorial.json`） |
| [kol-makeup-preview/](kol-makeup-preview/) | `kol-makeup-preview` | KOL 整妆 → 用户正脸或中国平均脸底图预览（`wan2.7-image-pro`） |

## 在 Cursor 中使用

开发本仓库时，让 Cursor 加载 Skill 任选其一：

1. **项目级**：将对应子目录复制或 junction 到 `.cursor/skills/<skill-name>/`（内容与本目录子文件夹一致）。
2. **用户全局**：复制到 `~/.cursor/skills/<skill-name>/`。

**不要**把业务 Skill 写到 `~/.cursor/skills-cursor/`（Cursor 内置目录）。

实现代码在 `packages/` 与 `scripts/`，Skill 只描述「怎么做」与契约，不含密钥。

**串联 job**（parse → Tutorial 映射 → preview）：[`docs/REPLICATE_PIPELINE.md`](../docs/REPLICATE_PIPELINE.md) · `scripts/run_beauty_replicate.py`
