# qwen3.7-plus — 步骤 base_prompt（第 1 阶段，纯文本）

模型：**`qwen3.7-plus`**  
API：`dashscope.MultiModalConversation.call`（**纯文本也走多模态端点**；`content` 为 `[{"text": "..."}]`），`response_format: {"type": "json_object"}`  
**勿用** `Generation.call`：对 `qwen3.7-plus` 会返回 `url error, please check url!`。  
参考实现形态：[`picture_makeup/llm.py`](../../packages/picture-makeup/picture_makeup/llm.py) → `call_text_json`。

**禁止**在本阶段传入关键帧或引用「画面中可见」的细节。

## System（固定）

```text
你是美妆跟练图示文案助手。根据教程步骤的结构化字段，生成一句中文 base_prompt，用于后续在固定人脸底图上用色块标注化妆范围。

只输出合法 JSON：
{
  "step_id": "与输入相同",
  "base_prompt": "一句完整中文"
}

base_prompt 写作规则：
1. 先描述本步手法与部位（扫、点、晕染、填色等），再描述颜色/质感（若有 visual_layer.color 或 product 信息）。
2. 必须包含 visual_layer.position 或从 instruction 推断出的等价位置描述（中文地标：颧骨、苹果肌、眼睑、唇线等）。
3. 句末必须以「请在原始图片上用色块标注着色范围」结尾（或「请在原始图片上用色块标注作用区域」——仅 prep/base/护肤类步骤可用「作用区域」替代「着色范围」）。
4. 长度建议 30–120 字；不要编号列表；不要 markdown。
5. visual_layer 缺 color 或 position 时，从 instruction、part、product 推断，仍须满足规则 3。
6. part 为 prep/base/set 等无典型彩妆色块时：描述涂抹/打底区域，句末仍用「作用区域」+ 色块标注要求，或说明用浅色半透明块标注全脸/分区。
7. 不要编造教程未出现的色号名称；opacity/shape 可融入描述（如「柔和椭圆」「低透明度」）。
```

## User 模板（Agent 填充）

将单步 JSON 序列化填入：

```text
请为以下教程步骤生成 base_prompt：

step_id: {step_id}
part: {part}
taxonomy_primary: {taxonomy_primary}
taxonomy_sub_steps: {json array}
instruction: {instruction}
adaptation_note: {adaptation_note}
product.name: {product.name}
product.keywords: {json array}
visual_layer: {json object — shape, color, opacity, position}
```

## 输出 JSON Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| `step_id` | string | 与输入一致 |
| `base_prompt` | string | 单句中文，句末符合 system 规则 3 |

## 示例

**输入（节选）**

```json
{
  "step_id": "blush_01",
  "part": "cheek",
  "instruction": "少量多次，低饱和粉色腮红",
  "visual_layer": {
    "color": "#E8A0A0",
    "opacity": 0.45,
    "position": "两颊颧骨下端",
    "shape": "soft_oval"
  }
}
```

**输出**

```json
{
  "step_id": "blush_01",
  "base_prompt": "在两颊两侧颧骨下端的位置横向扫低饱和粉色腮红，请在原始图片上用色块标注着色范围"
}
```

## Python 调用骨架

```python
import os
import dashscope
from dashscope import MultiModalConversation
from http import HTTPStatus

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

response = MultiModalConversation.call(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen3.7-plus",
    messages=[
        {"role": "system", "content": [{"text": "<上文 System>"}]},
        {"role": "user", "content": [{"text": "<User 模板填充>"}]},
    ],
    response_format={"type": "json_object"},
)
if response.status_code != HTTPStatus.OK:
    raise RuntimeError(response.message)
raw = response.output.choices[0].message.content
text = raw[0]["text"] if isinstance(raw, list) else raw
# 解析 JSON → base_prompt，写入 steps/<step_id>/base_prompt.txt
```

## 落盘

- `outputs/picture-makeup/runs/<ts>/steps/<step_id>/base_prompt.txt`（仅文本，无换行或单行）
