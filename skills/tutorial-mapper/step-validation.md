# Tutorial 步骤语义校验

版本：v1  
适用：tutorial 映射与 enrichment **完成之后**、写盘 **之前**，对内存中的 `tutorial` 对象执行。

## 目标

- **允许**同一 `taxonomy_primary` 下**多条** step（如 `lip_01` / `lip_02` 均为「唇妆」，时间首尾相接、instruction 不同）。
- **检测**「同一步被解析两次」：高度重叠的 `video_clip`、高度雷同的 `instruction`。
- **禁止**将「`taxonomy_primary` 在 `steps[]` 中全局唯一」作为验收标准。

失败策略默认 **`warn_write`**：写入 `issues`，**仍输出** `tutorial.json`；结果见 [output-contract.md](output-contract.md) 中 `enrichment_meta.tutorial_step_validation`。

## 输入

- `tutorial`：`contract_version: tutorial.v1` 对象（含 `duration`、`steps[]`）。
- 每步至少使用：`step_id`、`taxonomy_primary`、`instruction`、`video_clip.start` / `video_clip.end`。

## 分组统计

按 `taxonomy_primary` 分组，写入 `by_primary`：

```json
"唇妆": { "step_count": 2, "step_ids": ["lip_01", "lip_02"] }
```

`step_count > 1` **不是**问题本身。

## 必检（cheap）

| code | 条件 | severity |
|------|------|----------|
| `duplicate_step_id` | `step_id` 重复 | error |
| `invalid_video_clip` | `start >= end`，或 clip 超出 `[0, duration]` | error |
| `unknown_taxonomy_primary` | `taxonomy_primary` 为空或不在 [taxonomy-enums.json](../beauty-video-parse/taxonomy-enums.json) 主类列表 | warning |
| `duplicate_display_title` | 非空 `display_title` 在 `steps[]` 中出现两次及以上（展示分组消解失败的兜底） | warning |

`duplicate_display_title` **不是**「同主类多 step」本身；连续同主类合法分组见 [display-grouping.md](display-grouping.md)。

## 重复步检测

仅在**相同 `taxonomy_primary`** 的 step 之间两两比较（实现可先相邻对再全对，结果一致即可）。

常量默认值（实现为模块常量，变更须同步本文）：

| 常量 | 值 |
|------|-----|
| `SAME_CLIP_DELTA_SEC` | 2.0 |
| `OVERLAP_RATIO_THRESHOLD` | 0.30 |
| `INSTRUCTION_JACCARD_THRESHOLD` | 0.85 |

| code | 条件 | severity |
|------|------|----------|
| `duplicate_step_same_clip` | `\|start_a - start_b\| ≤ 2s` 且 `\|end_a - end_b\| ≤ 2s` | error |
| `duplicate_step_overlap` | `overlap_sec / min(len_a, len_b) > 0.30` | warning |
| `duplicate_step_same_instruction` | 归一化 instruction 相同，或字符 bigram Jaccard ≥ 0.85 | warning |
| `duplicate_step_overlap_and_instruction` | 同时满足 overlap 条件与高 instruction 相似 | error |

**overlap_sec**：`max(0, min(end_a,end_b) - max(start_a,start_b))`。  
**len**：`end - start`。

### instruction 归一化（仅用于比较）

1. 转小写（可选，中文可跳过）
2. 去除空白
3. 去除常见中英文标点
4. 不截断（v1）；若未来截断须在本文注明

## `pass` 语义

- `pass: true` 当且仅当 **不存在** `severity: error` 的 issue。
- 仅有 `warning` 时 `pass` 仍为 `true`。
- **`warn_write`**：无论 `pass` 真假，均写 `tutorial.json`；下游根据 `issues` 与 `pass` 决定是否阻断跟练。

## 输出

并入 `enrichment_meta.json` → `tutorial_step_validation`（不写独立文件）。形状见 [output-contract.md](output-contract.md)。

## 示例

### Pass（合法：同 primary 多 step）

嘴部教程类 run：两步 `taxonomy_primary: "唇妆"`，`video_clip` 约 0–36s 与 36–80s，instruction 不同 → `by_primary.唇妆.step_count === 2`，`issues` 无 error。

### Fail（重复解析）

- 两步「唇妆」clip 均为 0–40s → `duplicate_step_same_clip`（error），`pass: false`。
- 两步 clip 重叠超过 30% 且 instruction 高度相似 → `duplicate_step_overlap_and_instruction`（error）。

## 维护

修改规则时同步：

1. 本文件  
2. [output-contract.md](output-contract.md)  
3. [SKILL.md](SKILL.md) 流水线步骤语义校验  
4. `packages/tutorial-mapper/tutorial_mapper/step_validation.py`  
5. 展示字段相关见 [display-grouping.md](display-grouping.md)
