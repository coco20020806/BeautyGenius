# makeup-understanding 示例

## 底妆（口播含品牌 + 手法）

**输入摘要**（instruction 节选）：

> 珂岸面部素颜霜没有防晒 没有美白 全脸推开就行 专门打造伪素颜的

**期望输出**：

```json
{
  "step_id": "base_01",
  "display_product": "珂岸面部素颜霜",
  "display_product_tier": "specific",
  "technique": "全脸推开",
  "product_name": "珂岸面部素颜霜"
}
```

跟练页应显示：产品=`珂岸面部素颜霜`，手法=`全脸推开`。  
**错误示例**：`无>霜>底妆`（三段拼接 + 弱 keyword）。

## 腮红（有色号）

**输入摘要**：橘朵腮红 01 号 膨胀色 轻拍在颧骨

**期望**：

```json
{
  "step_id": "blush_01",
  "display_product": "橘朵腮红01",
  "display_product_tier": "specific",
  "technique": "轻拍颧骨",
  "product_name": "橘朵腮红01"
}
```

## 仅有特征称呼

**输入摘要**：用膨胀色腮红带一点血色

**期望**：

```json
{
  "display_product": "膨胀色腮红",
  "display_product_tier": "characteristic",
  "technique": "轻扫带出血色",
  "product_name": "unknown"
}
```

## 仅有品类

**输入摘要**：这一步画眉毛

**期望**：

```json
{
  "display_product": "眉毛",
  "display_product_tier": "category",
  "technique": "",
  "product_name": "unknown"
}
```
