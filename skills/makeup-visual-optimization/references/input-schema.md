# Input Schema

Normalize user questionnaire answers into `optimization_input`.

```json
{
  "preferred_styles": [],
  "occasions": [],
  "retained_modules": [],
  "target_areas": [],
  "skin_type": "油性肌肤|干性肌肤|混合性肌肤|中性肌肤|敏感肌|不确定",
  "face_shape": "圆脸|椭圆脸|长脸|方脸|菱形脸|心形脸|不确定",
  "makeup_goals": [],
  "execution_limits": [],
  "free_text": ""
}
```

## Allowed Values

`preferred_styles`: 清透自然, 甜美可爱, 温柔气质, 清冷高级, 氛围感, 元气活力, 性感成熟, 个性酷感.

`occasions`: 日常上学, 通勤工作, 约会, 聚会, 拍照, 面试, 旅行, 特殊活动.

`target_areas`: 眼睛, 眉毛, 鼻子, 面中, 腮红位置, 脸型轮廓, 嘴唇, 整体比例.

`makeup_goals`: 增加立体感, 减少脸部留白, 弱化轮廓感, 放大眼睛, 降低眼位, 缩短中庭.

`execution_limits`: 没有专业刷具, 产品不齐全, 早上时间少, 不会复杂眼妆, 不喜欢厚重底妆.

## Retained Original Modules

`retained_modules` is a multi-select answer to "你希望保留原教程哪些部分？"

Allowed values:

- 腮红
- 唇妆
- 眼妆
- 修容

Retention means:

- Keep the original module's color family, product keywords, source video clip, and recognizable style.
- If a user goal targets a retained module, still adapt its placement/range/intensity enough to satisfy the goal.
- For retained targeted modules, prefer `move_position`, `shrink_area`, `soften_technique`, and small opacity changes over replacing the module.
- For modules not selected, allow stronger rewriting when style, occasion, face-state goal, or execution limits call for it.

## Target Area Mapping

- 眼睛 -> eye, eye_detail, eyeliner, eyeshadow, lash, lower_lid, aegyo_sal
- 眉毛 -> brow
- 鼻子 -> nose_contour, nose_highlight
- 面中 -> cheek, blush, midface_highlight, under_eye
- 腮红位置 -> blush
- 脸型轮廓 -> contour, jaw_contour, cheek_contour, highlight
- 嘴唇 -> lip
- 整体比例 -> blush, contour, highlight, brow, eye, lip
