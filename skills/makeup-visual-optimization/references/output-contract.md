# Output Contract

Return a short human-readable summary, then JSON matching this shape.

```json
{
  "optimization_summary": {
    "primary_goal": "缩短中庭",
    "secondary_goals": ["通勤工作", "清透自然"],
    "retained_modules": ["腮红", "唇妆"],
    "retention_strategy": "腮红保留原教程色系和视频切片，但调整位置；唇妆保持原教程做法",
    "confidence": "high"
  },
  "global_adjustments": [
    {
      "reason": "通勤工作",
      "actions": ["lower_saturation", "soften_technique"],
      "note": "整体降低对比，让妆面更适合近距离日常场景。"
    }
  ],
  "step_adjustments": [
    {
      "step_id": "blush_01",
      "part": "cheek",
      "original": "原教程腮红从苹果肌向颧骨外侧斜扫。",
      "adapted": "腮红改为面中横向轻铺，范围控制在鼻翼上方。",
      "actions": ["move_position", "expand_area", "soften_technique"],
      "visual_layer_patch": {
        "layer_id": "layer_blush_01",
        "type": "blush",
        "shape": "soft_horizontal_oval",
        "color": "#EFA3A8",
        "opacity": 0.36,
        "position_description": "面中偏上，靠近眼下到苹果肌上缘，横向平铺，最低点不低于鼻翼",
        "blend_edge": "soft"
      },
      "adaptation_note": "想缩短中庭时，横向平铺的腮红能把视觉重点留在面中偏上位置。",
      "video_clip": {
        "reuse_original_clip": true,
        "clip_id": "clip_blush_01"
      }
    }
  ],
  "eye_detail_region_patches": [
    {
      "region_id": "lower_lid_extension",
      "action": "soften_technique",
      "visual_layer_patch": {
        "opacity": 0.32,
        "position_description": "下眼睑后三分之一极窄范围，边界向外晕开"
      },
      "instruction": "用余粉轻扫下眼尾，不画成完整深色下眼线。"
    }
  ],
  "practice_checklist_patches": [
    {
      "step_id": "blush_01",
      "instruction": "用少量腮红从黑眼珠下方向外轻铺，先横向晕开，再补一点点在鼻梁中段。",
      "difficulty": "easy",
      "estimated_time_seconds": 45
    }
  ],
  "visual_quality_checks": [
    "图层范围没有低于鼻翼",
    "修容起点低于原教程但没有形成明显脏感",
    "文案没有评价用户长相"
  ],
  "warnings": []
}
```

## Field Rules

- `optimization_summary.primary_goal`: pick the clearest user goal; if unclear, use occasion/style.
- `optimization_summary.retained_modules`: echo the user-selected modules: 腮红, 唇妆, 眼妆, 修容.
- `retention_strategy`: explain which retained modules remain unchanged and which are patched because they are directly targeted by the user's goals.
- `global_adjustments`: use only for changes affecting multiple steps.
- `step_adjustments`: include only changed or explicitly kept-important steps.
- `visual_layer_patch`: include all drawable fields when known: `layer_id`, `type`, `shape`, `color`, `opacity`, `position_description`, `blend_edge`.
- `video_clip.reuse_original_clip`: true when the original clip still teaches the same gesture; false when the step is substantially replaced.
- `warnings`: include missing tutorial fields, unknown skin/face fields, missing layers, or low-confidence conflicts.

## Opacity Ranges

- Base: 0.18-0.28
- Concealer: 0.25-0.38
- Blush: 0.30-0.48
- Contour: 0.22-0.40
- Highlight: 0.24-0.42
- Eyeshadow: 0.30-0.50
- Lip: 0.35-0.60
