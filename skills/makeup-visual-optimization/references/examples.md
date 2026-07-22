# Examples

## Shorten Midface

Input intent:

```json
{
  "preferred_styles": ["清透自然"],
  "occasions": ["通勤工作"],
  "retained_modules": ["腮红", "唇妆"],
  "target_areas": ["面中", "腮红位置", "整体比例"],
  "skin_type": "混合性肌肤",
  "face_shape": "不确定",
  "makeup_goals": ["缩短中庭"],
  "execution_limits": ["早上时间少"]
}
```

Expected decision:

- Keep original color family and step order.
- Because 腮红 is retained but directly targeted by 缩短中庭, keep its color/product family and clip while changing placement to flatter midface placement.
- Lower cheek contour start relative to a high cheekbone start.
- Simplify instructions to one fast cheek step.

Output excerpt:

```json
{
  "optimization_summary": {
    "primary_goal": "缩短中庭",
    "secondary_goals": ["清透自然", "通勤工作", "早上时间少"],
    "retained_modules": ["腮红", "唇妆"],
    "retention_strategy": "腮红保留原教程色系和切片，但重画范围；唇妆保持原教程做法",
    "confidence": "high"
  },
  "step_adjustments": [
    {
      "step_id": "blush_01",
      "part": "cheek",
      "original": "原教程腮红从苹果肌斜向颧骨外侧。",
      "adapted": "改为面中偏上的横向轻铺，颜色更淡，最低点控制在鼻翼线附近或以上。",
      "actions": ["move_position", "soften_technique", "lower_saturation"],
      "visual_layer_patch": {
        "layer_id": "layer_blush_01",
        "type": "blush",
        "shape": "soft_horizontal_oval",
        "color": "#EFA3A8",
        "opacity": 0.34,
        "position_description": "黑眼珠下方到苹果肌上缘横向平铺，外侧轻微晕向颧骨，最低点不低于鼻翼",
        "blend_edge": "soft"
      },
      "adaptation_note": "这个目标下，把腮红重心留在面中偏上，会比斜向下延伸更利于压缩中庭视觉距离。"
    },
    {
      "step_id": "contour_01",
      "part": "contour",
      "original": "原教程从颧骨高点向嘴角方向扫修容。",
      "adapted": "修容起点略降低，从耳前中段向嘴角上方轻扫，范围更窄。",
      "actions": ["move_position", "shrink_area", "soften_technique"],
      "visual_layer_patch": {
        "layer_id": "layer_contour_01",
        "type": "contour",
        "shape": "narrow_soft_diagonal",
        "color": "#9B7C6F",
        "opacity": 0.26,
        "position_description": "耳前中段到嘴角上方的短斜线，起点低于颧骨高点，边缘向外晕开",
        "blend_edge": "soft"
      },
      "adaptation_note": "修容起点略低，能保留脸部立体感，同时减少高颧骨阴影对面中长度的强调。"
    }
  ]
}
```

## Simplify Eye Makeup

Input intent: `不会复杂眼妆`, `通勤工作`, `放大眼睛`.

Expected decision:

- Keep one base eyeshadow layer.
- Keep outer-third depth and lash-line detail.
- Remove complex multi-color gradient.
- Do not thicken the whole eyeliner.
