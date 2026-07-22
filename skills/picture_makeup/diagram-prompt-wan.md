# wan2.7-image-pro — 步骤模块图示（单底图编辑）

Attribution：静态图示约束对齐 [JoyelleZ/makeup — makeup-visual-optimization/references/diagram-prompt.md](https://github.com/JoyelleZ/makeup/blob/main/makeup-visual-optimization/references/diagram-prompt.md)。

模型：**`wan2.7-image-pro`**（与 [`kol-makeup-preview/transfer-prompt.md`](../kol-makeup-preview/transfer-prompt.md) 相同）  
实现参考：[`makeup_preview/transfer.py`](../../packages/makeup-preview/makeup_preview/transfer.py) 中 `ImageGeneration.call` 与响应解析。

`prompt_text_version: diagram-2`（语义对齐参考的 `optimized-diagram-2`；改静态正文时递增）。

## 图像顺序（固定）

| 顺序 | 文件 | 语义 |
|------|------|------|
| 图1 | `skills/picture_makeup/image_format.png` | 原始示意底图（平均脸/模板）；**保持身份、五官、构图、光线** |

仅 **单图** + text，无妆后/用户多图拓扑。

## 完整送入模型的 text

```text
<从下方 prompt-diagram 代码块加载的静态正文>

本步骤优化图示要求：
{final_prompt}
```

Agent 从 **`skill_dir/diagram-prompt-wan.md`** 读取 ```prompt-diagram``` 块，再拼接 `final_prompt`（来自 [keyframe-enrich-qwen.md](keyframe-enrich-qwen.md)）。

## 机器可读正文（静态）

```prompt-diagram
任务：在固定人脸底图上，为个性化后的美妆教程步骤生成跟练示意图。底图的人物身份、五官比例、脸型、发型、表情、姿态、皮肤纹理、光线和拍摄角度必须保持不变；只允许添加用于教学的半透明范围标注。

图像说明：
- 图1：原始示意底图/模板脸，是唯一的几何与身份来源。

标注要求：
- 根据「本步骤优化图示要求」在对应面部区域叠加半透明色块、柔和色区或必要的极简方向箭头。
- 色块要表达上妆范围，不要生成完整真实妆面。
- 边缘需要柔和，贴近真实晕染范围，但边界仍能让用户看懂。
- 标注颜色默认保持原始产品色系；在接近产品颜色的基础上，可向同色系深浅、冷暖或邻近色相做小幅扩展，让多个标注层之间有清晰对比度。
- 当同一步或同一底图存在多个相近颜色图层时，应通过明度、饱和度、冷暖或透明度区分层级，避免腮红、修容、高光、眼影等标注混成一片。
- 不确定产品颜色时，用低饱和粉、棕、香槟或肤色调作为基础，并为不同部位选择可辨认的邻近变化；不要跨到明显不属于原妆容的色系。
- 若要求缩短中庭，腮红应以横向平铺为主，最低边界不低于鼻翼线附近；修容起点相对原教程降低但保持柔和。
- 若要求眼部精讲，所有眼影、眼线、卧蚕、睫毛、眼头提亮、下至、眉眼距离标注必须集中在同一眼部底图上。

成片要求：
- 真实人像底图风格，勿卡通化，勿换脸。
- 保持底图原有脸廓、眼鼻嘴比例、发型与背景。
- 图示是教学标注，不是医学检测图或热力图。

禁止：
- 不得改变骨相、五官大小、年龄感、表情或肤色。
- 不得添加教程未要求的完整眼妆/唇妆成妆效果。
- 不得过度磨皮、加滤镜或添加无关装饰。
- 不得出现评价用户长相的文字。
```

## 动态段建议字段

`final_prompt`（本步骤优化图示要求）宜包含：

- part 和步骤名
- 图层类型与颜色
- 精确位置与边界
- opacity / 强度
- 晕染边缘（blend edge）
- 中性说明（勿评价长相）

本轮不强制改上游 qwen 模板；由 Agent / 包侧尽量在 `final_prompt` 中带齐上述信息。

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
full_text = f"{static}\n\n本步骤优化图示要求：\n{final_prompt}"

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

- 改 **静态长正文**：递增 `prompt_text_version`（如 `diagram-3`），并更新 `manifest.json` 中 `diagram.prompt_text_version`。
- md 缺失或代码块损坏：Agent 应中止并提示修复 `diagram-prompt-wan.md`，勿静默省略静态约束。
