# qwen3.7-plus — 关键帧 enrich（第 2 阶段，多模视觉）

模型：**`qwen3.7-plus`**  
API：`dashscope.MultiModalConversation.call`，`response_format: {"type": "json_object"}`  
参考实现形态：[`tutorial_mapper/llm.py`](../../packages/tutorial-mapper/tutorial_mapper/llm.py) → `call_vision_json`。

## 硬约束（原文，勿改写含义）

- **不得改写或删减** 第 1 阶段生成的 **`base_prompt`**。
- 模型 **只输出 `appendix`**（补充描述）；Agent 侧合成：**`final_prompt = base_prompt + appendix`**（**无分隔符**，直接字符串拼接）。
- 若关键帧画面与 `base_prompt` 冲突，**以 base_prompt 为准**；`appendix` 仅写 **不冲突** 的补充；并设 `conflict: true` 与 `notes` 说明。
- 目的：用关键帧 **校对** 并 **尽可能丰富文本**，不是重写 prompt。

## 关键帧选择

解析 `tutorial.steps[].keyframe_refs[]`，文件路径：`parse_run_dir/keyframes/{filename}`。

**角色优先级**（与 [`vision_enrich._pick_keyframe_paths`](../../packages/tutorial-mapper/tutorial_mapper/vision_enrich.py) 一致）：

1. `makeup_detail`
2. `step_end_face`
3. `step_start_face`

按优先级排序后取 **最多 3 张** 且文件存在的 JPG；去重路径。

**无可用帧时**：跳过本阶段；`final_prompt = base_prompt`；`enrich.json` 写 `"skipped": true`，manifest 警告 **`no_keyframes_for_enrich`**。

## System（固定）

```text
你是美妆步骤视觉校对助手。你会看到教程步骤的关键帧，以及已经写好的 base_prompt（不可修改）。

只输出合法 JSON：
{
  "step_id": "与输入相同",
  "appendix": "仅补充中文，可为空字符串",
  "conflict": false,
  "notes": "简短说明校对结论；无冲突可空字符串",
  "keyframe_roles_used": ["makeup_detail", ...]
}

规则：
1. 禁止输出新的 base_prompt 或 paraphrase base_prompt；禁止在 appendix 中重复 base_prompt 全文。
2. appendix 只补充：边界细节、晕染方向、工具痕迹、可见色感强弱、与 sub_step label 一致的区域名等。
3. 若画面与 base_prompt 部位/动作明显矛盾，conflict=true，appendix 留空或只写不矛盾的细节，notes 说明矛盾点。
4. appendix 直接接在 base_prompt 后阅读应通顺；不要以句号开头重复句末「请在原始图片上…」（该句已在 base_prompt 末尾）。
5. 总长度 appendix 建议 0–80 字。
```

## User 文本（与图片一起发送）

```text
step_id: {step_id}
part: {part}
instruction: {instruction}
base_prompt（禁止修改，仅用于校对）:
{base_prompt}

请根据附带的关键帧，输出 appendix 等 JSON 字段。
```

消息结构：先 1–3 张 `{"image": "file:///absolute/path/to/frame.jpg"}`，再 `{"text": "<User 文本>"}`。

## 输出 JSON Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| `step_id` | string | 与输入一致 |
| `appendix` | string | 追加片段；可为 `""` |
| `conflict` | boolean | 是否与 base 明显矛盾 |
| `notes` | string | 校对说明 |
| `keyframe_roles_used` | string[] | 实际使用的 role |

## 合成 final_prompt

```python
base = base_prompt.strip()
app = (appendix or "").strip()
final_prompt = base + app  # 无分隔符
assert final_prompt.startswith(base)
```

写入 `final_prompt.txt`；完整 enrich 写入 `enrich.json`（含 `base_prompt`、`appendix`、`final_prompt`、`keyframe_files`）。

## Python 调用骨架

```python
import os
from pathlib import Path
import dashscope
from dashscope import MultiModalConversation
from http import HTTPStatus

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

content = []
for p in image_paths:  # 最多 3 张
    content.append({"image": f"file://{Path(p).resolve().as_posix()}"})
content.append({"text": user_text})

response = MultiModalConversation.call(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="qwen3.7-plus",
    messages=[
        {"role": "system", "content": [{"text": "<上文 System>"}]},
        {"role": "user", "content": content},
    ],
    response_format={"type": "json_object"},
)
```

## 示例

**base_prompt**

```text
在两颊两侧颧骨下端的位置横向扫低饱和粉色腮红，请在原始图片上用色块标注着色范围
```

**appendix**

```text
，色块略呈柔和椭圆形并向太阳穴方向轻扫
```

**final_prompt**

```text
在两颊两侧颧骨下端的位置横向扫低饱和粉色腮红，请在原始图片上用色块标注着色范围，色块略呈柔和椭圆形并向太阳穴方向轻扫
```
