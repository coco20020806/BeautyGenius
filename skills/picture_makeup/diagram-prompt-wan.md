# wan2.7-image-pro — 步骤模块图示（单底图编辑）

模型：**`wan2.7-image-pro`**（与 [`kol-makeup-preview/transfer-prompt.md`](../kol-makeup-preview/transfer-prompt.md) 相同）  
实现参考：[`makeup_preview/transfer.py`](../../packages/makeup-preview/makeup_preview/transfer.py) 中 `ImageGeneration.call` 与响应解析。

`prompt_text_version: diagram-1`（改静态正文时递增）。

## 图像顺序（固定）

| 顺序 | 文件 | 语义 |
|------|------|------|
| 图1 | `skills/picture_makeup/image_format.png` | 原始示意底图（平均脸/模板）；**保持身份、五官、构图、光线** |

仅 **单图** + text，无妆后/用户多图拓扑。

## 完整送入模型的 text

```text
<从下方 prompt-diagram 代码块加载的静态正文>

本步骤具体标注要求：
{final_prompt}
```

Agent 从 **`skill_dir/diagram-prompt-wan.md`** 读取 ```prompt-diagram``` 块，再拼接 `final_prompt`（来自 [keyframe-enrich-qwen.md](keyframe-enrich-qwen.md)）。

## 机器可读正文（静态）

```prompt-diagram
任务：在图1固定人脸底图上，为本美妆教程步骤生成跟练示意图。图1的人物身份、五官比例、脸型、发型、表情、姿态、皮肤纹理、光线和拍摄角度必须保持不变；只允许添加用于教学的可视化标注。

图像说明：
- 图1：原始示意底图/模板脸，是唯一的几何与身份来源。

标注要求：
- 根据下文「本步骤具体标注要求」在对应面部区域叠加半透明色块或柔和色区，清晰标示着色或作用范围。
- 色块边缘可略柔和，避免硬边贴纸感；需与描述的位置一致（如颧骨、眼睑、唇峰等）。
- 不要整脸换色，不要完成真实上妆渲染；目标是「范围示意」，不是成妆效果图。
- 可保留极淡的箭头或短文字仅当有助于理解范围（非必须）；优先色块。

成片要求：
- 真实人像底图风格，勿卡通化、勿换脸。
- 保持图1原有脸廓、眼鼻嘴比例、发型与背景。
- 标注颜色应与描述中的色系一致或近似；不确定时用中性半透明粉/棕/肤色调示意。

禁止：
- 不得改变骨相、五官大小、年龄感或表情。
- 不得迁移 KOL/博主身份或变成另一个人。
- 不得添加教程未要求的完整眼妆/唇妆成妆效果；仅范围标注。
- 不得过度磨皮、滤镜或添加无关装饰。
```

## Python 调用骨架

```python
import os
import re
from pathlib import Path
import dashscope
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message
from http import HTTPStatus

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

skill_dir = Path("<repo-root>/skills/picture_makeup")
base_image = skill_dir / "image_format.png"
md = (skill_dir / "diagram-prompt-wan.md").read_text(encoding="utf-8")
m = re.search(r"```prompt-diagram\s*\n(.*?)```", md, re.DOTALL)
static = m.group(1).strip() if m else ""
final_prompt = Path("final_prompt.txt").read_text(encoding="utf-8").strip()
full_text = f"{static}\n\n本步骤具体标注要求：\n{final_prompt}"

message = Message(
    role="user",
    content=[
        {"image": f"file://{base_image.resolve().as_posix()}"},
        {"text": full_text},
    ],
)

response = ImageGeneration.call(
    api_key=os.environ["DASHSCOPE_API_KEY"],
    model="wan2.7-image-pro",
    messages=[message],
    watermark=False,
    n=1,
    size="2K",
)
```

## 参数约定

| 参数 | 默认 |
|------|------|
| `n` | 1 |
| `size` | `2K`（图像编辑上限；可与底图宽高比接近时改用 `1280*1280` / `1280*720` / `720*1280` / `1024*1024`，逻辑同 `makeup_preview.config.resolve_image_size`） |
| `watermark` | false |

## 响应落盘

- 从 `response.output.choices[].message.content` 取 `type: image` 的 URL 或 base64，下载为 `diagram_01.jpg`。
- 完整 `full_text` 写入 `diagram_prompt.txt`；原始响应可选 `wan_raw.json`。
- HTTP 非 OK 时写 `diagram_error.txt`（对齐 transfer 的 `transfer_error.txt` 习惯）。

## 维护

- 改 **静态长正文**：递增 `prompt_text_version`（如 `diagram-2`），并更新 `manifest.json` 中 `diagram.prompt_text_version`。
- md 缺失或代码块损坏：Agent 应中止并提示修复 `diagram-prompt-wan.md`，勿静默省略静态约束。
