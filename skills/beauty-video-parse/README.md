# beauty-video-parse

美妆教程视频解析的 **Cursor Agent Skill** 文档包。

**Canonical 源码路径**（Beauty Genius 仓库）：

```text
<repo-root>/skills/beauty-video-parse/
```

Windows 示例：`C:\Users\fei.kong\Desktop\Beauty Genius\skills\beauty-video-parse\`

实现代码：`packages/video-parse/`、`scripts/parse_beauty_video.py`；目标结构见 [module-structure.md](module-structure.md)。  
同目录索引：[skills/README.md](../README.md)。

## 安装到 Cursor

```text
# 从上述 skills/beauty-video-parse 复制或 junction 到：
.cursor/skills/beauty-video-parse/

# 或用户全局
~/.cursor/skills/beauty-video-parse/
```

## 文件说明

| 文件 | 用途 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 主指令 |
| [makeup-replication-refs.md](makeup-replication-refs.md) | 片尾 before/after 复刻参考 |
| [reference.md](reference.md) | DashScope / ffmpeg / 故障 |
| [output-contract.md](output-contract.md) | analysis.json 契约（v2 / v2.1） |
| [step-taxonomy.md](step-taxonomy.md) | 步骤 taxonomy |
| [taxonomy-enums.json](taxonomy-enums.json) | 主类/sub_steps 枚举 |
| [keyframe-validation.md](keyframe-validation.md) | 关键帧与 Pair QA |
| [examples.md](examples.md) | 命令与样例 |
| [module-structure.md](module-structure.md) | 可复用包与演进 |

Schema：`packages/video-parse/video_parse/schemas/beauty_video_analysis.v2.json` · `beauty_video_analysis.v2.1.json`
