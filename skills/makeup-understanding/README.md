# makeup-understanding

从 `tutorial.json` 步骤全文提取跟练展示用 **产品（单字段）** 与 **短手法**。

## 在流水线中的位置

```text
beauty-video-parse → tutorial-mapper → makeup-understanding → kol-makeup-preview / 跟练页
```

- **上游**：[`tutorial-mapper`](../tutorial-mapper/) 产出的 `tutorial.json`
- **下游**：前端跟练页读取 `display_product` / `technique`；不再拼接 `无>霜>底妆`

## Cursor

将本目录 junction 或复制到 `.cursor/skills/makeup-understanding/`（或用户全局 skills）。

## 实现

Python 包：`packages/makeup-understanding/`  
CLI：`scripts/run_makeup_understanding.py`
