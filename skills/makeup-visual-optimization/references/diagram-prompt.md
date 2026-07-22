# Diagram Prompt

Use this only when the user asks for an image-generation prompt or a fixed-base diagram instruction. This skill's primary output is structured optimization JSON.

`prompt_text_version: optimized-diagram-2`

## Prompt Block

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

## Assembly

Full text:

```text
<prompt-diagram block>

本步骤优化图示要求：
{adapted_step_or_eye_region_prompt}
```

The adapted prompt should include:

- part and step name
- layer type and color
- exact placement and boundary
- opacity/intensity
- blend edge
- why it was optimized, in neutral wording
