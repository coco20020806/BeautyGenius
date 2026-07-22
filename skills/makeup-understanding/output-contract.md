# makeup-understanding 输出契约

在既有 `tutorial.v1` 的每个 `steps[]` 对象上**追加**（`additionalProperties` 允许）以下字段。不删除原有 `product` / `instruction` / `visual_layer`。

## 步骤字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `display_product` | string | 是 | 跟练页「产品」列唯一展示字符串；无则 `""` |
| `display_product_tier` | string | 是 | `specific` \| `characteristic` \| `category` \| `none` |
| `technique` | string | 是 | 短手法；无则 `""` |
| `display_range` | string | 是 | 跟练页「范围」通顺中文；无则 `""`（前端可回退 `visual_layer.position`） |

可选回填（不改变时间轴）：

| 字段 | 说明 |
|------|------|
| `product.name` | 当 tier=`specific` 且原名为 `unknown` 时可写入具体名 |
| `product.keywords` | 可补充特征词，不覆盖已有非空列表除非更具体 |

## 批处理响应（LLM）

```json
{
  "steps": [
    {
      "step_id": "base_01",
      "display_product": "珂岸面部素颜霜",
      "display_product_tier": "specific",
      "technique": "全脸推开",
      "display_range": "全脸均匀薄涂，边缘自然过渡",
      "product_name": "珂岸面部素颜霜"
    }
  ]
}
```

约束：

- `step_id` 必须与输入一致；禁止编造步骤或时间轴。
- `display_product` 必须与 `display_product_tier` 一致：tier=`none` 时 `display_product` 为空。
- `product_name` 仅当文本中出现可辨认的具体产品名时填写，否则省略或 `unknown`。
- `display_range` 禁止英文枚举、snake_case、裸 `#RRGGBB`；保留机器用 `visual_layer.shape` / `color` 原字段不改写。

## 元数据文件

`understanding_meta.json`：

```json
{
  "generated_at": "ISO8601",
  "parse_run_id": "<run dir name>",
  "model": "qwen-plus 或实际模型 id",
  "steps_touched": ["base_01"],
  "ok": true,
  "error": null
}
```
