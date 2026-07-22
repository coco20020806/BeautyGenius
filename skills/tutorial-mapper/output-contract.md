# 输出契约 — tutorial.json 与 enrichment_meta

Schema：`packages/tutorial-mapper/tutorial_mapper/schemas/tutorial.v1.json`（`contract_version: tutorial.v1`）。

## Run 目录产物（parse run 内）

| 文件 | 说明 |
|------|------|
| `tutorial.json` | 跟练产品模型（steps、assets 等） |
| `enrichment_meta.json` | 映射/enrichment 阶段元数据 + **步骤语义校验** |

不单独写 `tutorial_validation.json`；校验结果仅进入 `enrichment_meta.json`。

## tutorial.json（tutorial.v1）

与 schema 一致。要点：

- `steps[]`：每步含 `step_id`、`part`、`taxonomy_primary`、`video_clip`、`instruction` 等。
- **同一 `taxonomy_primary` 可出现多次**（多 step）；不以全局 unique 为契约要求。
- 跟练页编号读 `step_groups[].index`，**不是**扁平 `steps[]` 下标。

### 展示字段（确定性，mapper 写盘前填充）

详见 [display-grouping.md](display-grouping.md)。

#### 每步追加

| 字段 | 类型 | 说明 |
|------|------|------|
| `display_title` | string | 卡内子段标题；单步组等于主类，多步组为「主类 · 细分」等去重名 |
| `display_group_id` | string | 所属 `step_groups[].group_id` |

#### 顶层 `step_groups[]`

| 字段 | 类型 | 说明 |
|------|------|------|
| `group_id` | string | 如 `group_01` |
| `title` | string | 卡片主标题（通常为 `taxonomy_primary`） |
| `index` | integer | 展示编号，从 1 起 |
| `step_ids` | string[] | 组内步骤，顺序同 `steps[]` |

卡片标题格式：`步骤 {index} · {title}`。

示例（修容拆两步 + 眼睛 + 唇妆）：

```json
{
  "step_groups": [
    {
      "group_id": "group_01",
      "title": "修容",
      "index": 1,
      "step_ids": ["contour_01", "contour_02"]
    },
    {
      "group_id": "group_02",
      "title": "眼睛",
      "index": 2,
      "step_ids": ["eye_01"]
    },
    {
      "group_id": "group_03",
      "title": "唇妆",
      "index": 3,
      "step_ids": ["lip_01"]
    }
  ],
  "steps": [
    {
      "step_id": "contour_01",
      "taxonomy_primary": "修容",
      "display_title": "修容 · 鼻头两侧",
      "display_group_id": "group_01"
    },
    {
      "step_id": "contour_02",
      "taxonomy_primary": "修容",
      "display_title": "修容 · 颧骨下方",
      "display_group_id": "group_01"
    }
  ]
}
```

## enrichment_meta.json 扩展

除现有 `generated_at`、`parse_run_id`、`stages`、`applied` 外，映射流水线在写盘前写入：

### `tutorial_step_validation`

| 字段 | 含义 |
|------|------|
| `version` | 校验规则版本，当前 `"1"` |
| `pass` | 无 `severity: error` 的 issue 时为 `true` |
| `by_primary` | 按主类分组：`step_count`、`step_ids[]` |
| `issues` | 问题列表 |

### `issues[]` 元素

| 字段 | 含义 |
|------|------|
| `code` | 见 [step-validation.md](step-validation.md) |
| `severity` | `error` \| `warning` |
| `taxonomy_primary` | 相关主类（若适用） |
| `step_ids` | 涉及的 step_id，通常 2 个 |
| `message` | 简短中文说明 |

示例：

```json
{
  "tutorial_step_validation": {
    "pass": true,
    "version": "1",
    "by_primary": {
      "唇妆": {
        "step_count": 2,
        "step_ids": ["lip_01", "lip_02"]
      }
    },
    "issues": []
  }
}
```

## 默认写盘策略（warn_write）

- 存在 error 级 issue 时：`pass: false`，**仍写** `tutorial.json`。
- API / 跟练页应读取 `enrichment_meta.tutorial_step_validation`，在 `pass: false` 时提示或阻断自动跟练（产品层决策）。

## 版本

- **tutorial.v1**：Tutorial 主体契约（不变）。
- **tutorial_step_validation v1**：本校验块（与 mapper 包同步）。
