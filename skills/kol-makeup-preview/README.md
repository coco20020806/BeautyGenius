# kol-makeup-preview

KOL **抄整妆**个人预览的 Cursor Agent Skill。源码路径：

```text
<repo-root>/skills/kol-makeup-preview/
```

Windows 本机示例：`C:\Users\fei.kong\Desktop\Beauty Genius\skills\kol-makeup-preview\`

## 安装到 Cursor

```text
# 从本目录复制或 junction 到：
.cursor/skills/kol-makeup-preview/

# 或用户全局：
~/.cursor/skills/kol-makeup-preview/
```

上游依赖：通常先跑 [beauty-video-parse](../beauty-video-parse/) 得到 `outputs/runs/<id>/`。

实现包（计划/演进）：`packages/makeup-preview/`；CLI：`scripts/run_makeup_preview.py`。

## 文件说明

| 文件 | 用途 |
|------|------|
| [SKILL.md](SKILL.md) | Agent 主指令 |
| [user-flow.md](user-flow.md) | 上传 / 不上传 / 校验失败 |
| [face-validation.md](face-validation.md) | 平视正脸 L1 + L2 |
| [reference-selection.md](reference-selection.md) | 从 parse run 选参考帧 |
| [transfer-prompt.md](transfer-prompt.md) | wan2.7-image-pro 多图 prompt |
| [output-contract.md](output-contract.md) | preview run 契约 |
| [reference.md](reference.md) | DashScope / MediaPipe |
| [examples.md](examples.md) | 命令与样例 |
| [module-structure.md](module-structure.md) | 包边界与演进 |
| [io-summary.md](io-summary.md) | 输入/输出摘要 |
| [baselines.md](baselines.md) | 女性/男性平均脸 PNG 路径 |
| `female_average_face.png` / `male_average_face.png` | Skill 根目录底图资源 |
