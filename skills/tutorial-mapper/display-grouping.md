# Tutorial 展示分组与 display_title

版本：v1  
适用：tutorial 映射与 enrichment **完成之后**、schema / 步骤语义校验 **之前**，对内存中的 `tutorial` 对象**确定性**填充。

## 目标

- 同一 `taxonomy_primary` 可对应多条扁平 `steps[]`（下游 clip / 图示 / understanding 不变）。
- 跟练步骤页按 **组** 展示：连续同主类合成一张卡，**编号只记一次**（`步骤 {group.index} · {group.title}`）。
- 卡内子段用去重后的 `display_title` 区分（如「修容 · 鼻头两侧」vs「修容 · 颧骨下方」）。

**分组 ≠ 重复步报错**：连续同主类多 step 且 clip/instruction 不雷同是合法数据；重复解析仍由 [step-validation.md](step-validation.md) 检测。

## 分组算法

按 `steps[]` **数组顺序**（即时间序）扫描：

1. 取当前步 `taxonomy_primary`（空串视为独立键，不与前后合并）。
2. 若与当前组 `title` 相同 → 并入当前组。
3. 否则开启新组。

不相邻的同主类**不**合并（例如 修容 → 眼睛 → 修容 → 两组修容）。

每组写入 `step_groups[]`：

| 字段 | 说明 |
|------|------|
| `group_id` | `group_{序号:02d}`，从 1 起 |
| `title` | 组内 `taxonomy_primary`（空则 `"其他"`） |
| `index` | 展示编号，从 1 起，**全局组序** |
| `step_ids` | 组内 `step_id` 列表（顺序同 `steps[]`） |

每步同步写 `display_group_id` = 所属 `group_id`。

## `display_title` 生成

对每个组内的每一步：

| 场景 | 规则 |
|------|------|
| 组内只有 1 步 | `display_title = taxonomy_primary`（空则 `step_id`） |
| 组内 ≥2 步且有 `taxonomy_sub_steps` | 候选为 `「{primary} · {细分}」`，按细分数组顺序取第一个**组内未用过**的；全部撞名后对首选加 `·2`、`·3`… 后缀直至唯一 |
| 组内 ≥2 步且无细分 | `「{primary} · {组内序号}」`（1-based） |

`primary` 为空时用 `"其他"` 代替拼接前缀。

## 与校验的边界

- 本阶段**不**把「同主类多 step」写成 error。
- [step-validation.md](step-validation.md) 可对写盘后仍撞名的 `display_title` 发 `duplicate_display_title` **warning**（消解逻辑失败时的兜底）。

## 维护

修改规则时同步：

1. 本文件  
2. [output-contract.md](output-contract.md)  
3. [SKILL.md](SKILL.md)  
4. `packages/tutorial-mapper/tutorial_mapper/display_grouping.py`
