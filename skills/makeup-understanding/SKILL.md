---
name: makeup-understanding
description: >-
  Extracts follow-along display product name and short technique from each
  tutorial.json step using LLM priority rules (specific product > characteristic
  name > category). Use after tutorial-mapper when practice UI needs
  display_product / technique, or when product shows as 无>霜>底妆 style garbage.
---

# Makeup Understanding

从已有 `tutorial.json` 各步骤的**全部文本**中，用大模型按优先级提取跟练页展示用的 **产品名** 与 **短手法**。不改动 `beauty_video_analysis` 契约；在 `tutorial.v1` 步骤上**追加**展示字段。

## 何时使用

- 已有 parse run 下的 `tutorial.json`，跟练页需要干净的产品/手法文案。
- 确定性映射只留下弱 `keywords`（如「霜」）且 `product.name=unknown`。
- `parse_mode=fast` 跳过了 tutorial-mapper 的 text enrich，仍希望产品字段可用。

## 快速执行

```powershell
cd "<repo-root>"
.\.venv\Scripts\pip.exe install -e packages\makeup-understanding
.\.venv\Scripts\python.exe .\scripts\run_makeup_understanding.py --parse-run "outputs\runs\<timestamp>"
```

也可由 API 流水线在 tutorial-mapper 之后自动触发（默认开启，含 fast 模式）。

## 流水线

1. 读 parse run 的 `tutorial.json`
2. 按步组装文本包：`instruction`、`taxonomy_primary`、`taxonomy_sub_steps`、`product`、`adaptation_note`
3. 调用文本 LLM（`qwen3.7-plus` + `MultiModalConversation`，见 [prompt-qwen.md](prompt-qwen.md)）
4. 合并补丁：写入 `display_product`、`display_product_tier`、`technique`；可选回填 `product.name`
5. 写回 `tutorial.json`，并写 `understanding_meta.json`

## 展示优先级（产品）

页面**只显示一条** `display_product`，按下列优先级取最高可得项：

1. **specific**：具体产品名（含品牌/色号），如「橘朵腮红01」「珂岸面部素颜霜」
2. **characteristic**：带特征的产品称呼，如「膨胀色腮红」
3. **category**：品类，如「腮红」「底妆」
4. **none**：文本中无法判断时为空或「无」

## 手法

`technique` 为可跟练的**短动作**（如「全脸推开」），不是整段口播。

## 验收

- [ ] run 目录更新 `tutorial.json`，含每步 `display_product` / `display_product_tier` / `technique`
- [ ] 含 `understanding_meta.json`
- [ ] 前端产品行不再用 `>` 拼接三段
- [ ] 示例底妆：产品「珂岸面部素颜霜」、手法「全脸推开」

## 实现

- 包：[`packages/makeup-understanding/`](../../packages/makeup-understanding/)
- 契约：[output-contract.md](output-contract.md)
- 上游：[`tutorial-mapper`](../tutorial-mapper/)
- 下游：跟练页 `PracticePage` / `formatTutorialStep`
