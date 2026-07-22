# wan2.7-image-pro — 抄整妆多图 Prompt

Attribution：长 prompt 约束结构参考 [JoyelleZ/makeup — wan-makeup-transfer](https://github.com/JoyelleZ/makeup/tree/main/wan-makeup-transfer)（静态化，无逐 KOL 填槽）。

图拓扑版本：`prompt_version` 为 **v2**（三图）或 **v1**（二图降级）。  
正文版本：`prompt_text_version: wan-long-1`（与图拓扑分离；改长正文时递增）。  
实现：`packages/makeup-preview/makeup_preview/prompt_loader.py` 读取本文 `prompt-v1` / `prompt-v2` 代码块 → `transfer.py`。

## 图像顺序（v2，固定，勿调换）

| 顺序 | 文件 | 语义 |
|------|------|------|
| 图1 | `reference.jpg` | 教程/KOL **妆后**（`replication_after`） |
| 图2 | `tutorial_before.jpg` | 教程 **妆前**（`replication_before`） |
| 图3 | `target.jpg` | 用户自拍或中国平均脸底图 |

## 机器可读正文（v2 三图）

```prompt-v2
任务：将参考博主的妆容准确复刻到目标人物脸上。图3的身份、五官比例、脸型、发型、表情、姿态、年龄感、皮肤真实纹理、光线和拍摄角度必须保持不变；只迁移妆容。

图像说明：
- 图1：美妆教程/KOL 的完成妆面参考（妆后）。
- 图2：同一教程的妆前/素颜对照，用于区分妆面变化；勿把图2当作上妆目标。
- 图3：需要上妆的目标人脸（用户自拍或平均脸底图）；图3是身份与几何的唯一来源。

参考妆容：以图1为妆后、图2为妆前，按图1相对图2的可见差分理解完整妆容（底妆、眉、眼、唇、腮红、修容、点痣等）。具体色号、形状、边界以参考图可见效果为准，在图3上按目标人物自己的脸部结构地标相对贴合。

妆感强度校准：妆感应等于或弱于图1相对图2的可见差分；不得提高饱和度、对比度、修容深度、腮红范围、眼线粗细、睫毛密度、高光亮度或唇色浓度。默认真实人类上妆、日常可见，非舞台妆、非滤镜加重、非广告级浓妆。若参考图为偏暗或压缩的社交截图，保持中低妆感，除非差分明显更浓。

请按目标人物自己的脸部结构贴合以下妆容（细节以图1相对图2为准）：
1. 底妆：质地、遮瑕、明度、色调、修容与高光位置。
2. 眉毛：粗细、形状、弧度、眉尾、颜色与柔和度。
3. 眼妆：眼影色系与晕染范围、眼线内外形态、睫毛卷翘与密度、下眼睑/卧蚕处理。
4. 腮红/修容/高光：位置与强度。
5. 唇妆：颜色、边缘、质地（哑光/润泽）、不得改变图3固有嘴型比例。
6. 点痣/局部细节：若图1或差分中可见小黑点、点痣、刻意添加的雀斑或局部妆点，用相对 landmarks 描述并在图3对应侧复刻；贴纸、脸钻、亮片、水钻等装饰仅当参考中 unmistakably 可见时才添加，否则明确不要添加。

成片要求：
- 真实人像、自然妆感、保留皮肤毛孔，避免塑料皮。
- 妆容自然可见且忠实于参考的实际显色，但不得强于博主妆前妆后差分；像真实化妆贴在图3脸上。
- 保持图3原有脸廓、眼大小、鼻形、嘴形、下颌线。
- 保留图3原有天然痣与皮肤标记，除非用户要求去除；仅添加参考妆面中明确属于妆容的细节点。
- 勿遗漏参考中明显的小黑点/妆点；勿仅凭类别名臆造贴纸或脸钻。
- 保持图3原有光线方向、拍摄角度、背景简洁度与发型，除非另有要求。

禁止：
- 不得换脸，不得让图3看起来像图1博主。
- 不得改变骨相、五官比例、眼大小、鼻梁、唇形、下颌、年龄感、发型或表情。
- 不得过度美白、过度磨皮、过度饱和、加深修容、提亮高光、加粗眼线、夸大睫毛、扩大腮红、加滤镜、臆造无关配饰，也不得变成烟熏/舞台/欧美浓妆，除非参考中明确存在。
```

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
        {"text": "<从 prompt-v2 代码块加载>"},
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

## 机器可读正文（v1 二图）

```prompt-v1
任务：将参考妆面的妆容准确复刻到目标人物脸上。图2的身份、五官比例、脸型、发型、表情、姿态、年龄感、皮肤真实纹理、光线和拍摄角度必须保持不变；只迁移妆容。

图像说明：
- 图1：完成妆面参考（无妆前对照时，直接根据图1可见妆效描述；不确定的细节按 subtle/estimated 处理，勿臆造浓妆）。
- 图2：需要上妆的目标人脸；图2是身份与几何的唯一来源。

参考妆容：将图1的完整妆容风格（底妆、眉、眼、唇、腮红、修容、可见妆点等）自然迁移到图2，具体以图1可见效果为准，按图2自身脸部结构地标相对贴合。

妆感强度：默认真实人类上妆、日常至中低强度；勿舞台妆、勿滤镜加重。无妆前差分时勿夸大 pigment，宁可 subtle 但可感知。

请按目标人物自己的脸部结构贴合：底妆、眉毛、眼妆、腮红/修容/高光、唇妆、以及图1中可见的点痣/妆点（贴纸/脸钻/亮片仅当图1中 clearly 可见才添加）。

成片要求：真实人像、自然妆感、保留皮肤纹理；保持图2脸廓与五官尺寸；保留图2天然痣；保持图2光线、角度、发型。

禁止：不得换脸或像博主；不得改骨相、比例、眼鼻嘴下颌、年龄、发型、表情；不得过度美白磨皮饱和、加重修容眼线睫毛腮红、臆造配饰或烟熏浓妆，除非图1中明确存在。
```

## 参数约定

| 参数 | 预览默认 |
|------|----------|
| `n` | 1（可选 2 供用户挑选） |
| `size` | `2K`（图像编辑最高 2K） |
| `watermark` | false（`PreviewConfig.image_watermark` 可调） |
| 本地图 | `file://` URI，与 `video_parse` 一致 |

## 响应落盘

从 `response.output.choices[].message.content` 中 `type: image` 的 URL 下载，写入 `preview_01.jpg` 等；本次请求的 text 写入 run 目录 `transfer_prompt.txt`。细节见 [reference.md](reference.md)。

## Agent 可选（CLI 不读）

调试时可按 [wan-makeup-transfer](https://github.com/JoyelleZ/makeup/tree/main/wan-makeup-transfer) 格式手写 `makeup-analysis.txt`，再对照本文长 prompt 微调；正式流水线仅使用上文代码块。

## 维护

- 改 **图数量/顺序**：更新 `prompt_version`（v1/v2）与 `preview.json.transfer.prompt_version`。
- 改 **长正文**：递增 `prompt_text_version`（如 `wan-long-2`）并更新 `preview.json.transfer.prompt_text_version`。
- 若 md 缺失或代码块损坏，实现回退 `config.py` 短 prompt，并写 `warnings: transfer_prompt_fallback_static`。
