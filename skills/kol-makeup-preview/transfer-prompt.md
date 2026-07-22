# wan2.7-image-pro — 抄整妆多图 Prompt

版本：`prompt_version: v2`（三图：妆后 + 教程妆前 + 目标脸）  
兼容回退：`v1`（二图：妆后 + 目标脸）见文末。  
实现：`packages/makeup-preview/makeup_preview/transfer.py`（有 `tutorial_before` 走 v2，否则 v1）。

## 图像顺序（v2，固定，勿调换）

| 顺序 | 文件 | 语义 |
|------|------|------|
| 图1 | `reference.jpg` | 教程/KOL **妆后**（`replication_after`） |
| 图2 | `tutorial_before.jpg` | 教程 **妆前**（`replication_before`） |
| 图3 | `target.jpg` | 用户自拍或中国平均脸底图 |

## 默认 text（v2）

图1为美妆教程中的**完成妆面**参考。图2为同一教程中的**妆前/素颜对照**（用于区分妆面变化，勿把图2当作上妆目标）。图3为需要上妆的人脸。请将图1相对图2所体现的**完整妆容风格**（唇色、眼妆、腮红、修容等）自然迁移到图3上，**保持图3的身份特征、脸型与发型不变**，光照与肤色协调，真实美妆照片效果，不要换脸，不要改变图3的五官结构。

## Python 调用骨架（v2）

```python
import os
import dashscope
from dashscope.aigc.image_generation import ImageGeneration
from dashscope.api_entities.dashscope_response import Message

dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

message = Message(
    role="user",
    content=[
        {"image": "file:///absolute/path/reference.jpg"},
        {"image": "file:///absolute/path/tutorial_before.jpg"},
        {"image": "file:///absolute/path/target.jpg"},
        {"text": "<上表 v2 正文>"},
    ],
)

response = ImageGeneration.call(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="wan2.7-image-pro",
    messages=[message],
    watermark=False,
    n=1,
    size="2K",
)
```

## 缺教程妆前时的降级

| 条件 | 行为 |
|------|------|
| 有 `makeup_replication_refs.before` 且文件存在 | **三图 v2** |
| 无 before，仅有 after + target | **回退二图 v1**；`warnings` 含 `transfer_without_tutorial_before` |
| `--reference-image` 手动单图（无 parse before） | **回退二图 v1**；同上 warning |

### v1 二图顺序（仅降级）

| 顺序 | 文件 | 语义 |
|------|------|------|
| 图1 | `reference.jpg` | 妆后参考 |
| 图2 | `target.jpg` | 用户/平均脸 |

v1 text：图1为完成妆面参考。图2为需要上妆的人脸。请将图1的完整妆容风格自然迁移到图2上，保持图2身份特征、脸型与发型不变……

## 参数约定

| 参数 | 预览默认 |
|------|----------|
| `n` | 1（可选 2 供用户挑选） |
| `size` | `2K`（图像编辑最高 2K） |
| `watermark` | false（`PreviewConfig.image_watermark` 可调） |
| 本地图 | `file://` URI，与 `video_parse` 一致 |

## 响应落盘

从 `response.output.choices[].message.content` 中 `type: image` 的 URL 下载，写入 `preview_01.jpg` 等；细节见 [reference.md](reference.md)。

## 维护

改 prompt 正文时递增 `prompt_version`，并在 `preview.json.transfer.prompt_version` 记录（`v2` 或降级 `v1`）。
