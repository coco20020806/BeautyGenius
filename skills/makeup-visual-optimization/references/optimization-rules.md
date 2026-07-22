# Optimization Rules

Use the least invasive combination that satisfies the user goal while respecting user-selected retained modules.

## Action Vocabulary

- `shrink_area`
- `expand_area`
- `lower_saturation`
- `increase_brightness`
- `move_position`
- `soften_technique`
- `keep_original`
- `replace_tool`
- `adjust_order`

## Style Rules

- 清透自然: lower saturation; reduce contour depth; soften edges; use lower-half opacity.
- 甜美可爱: round blush; brighten cheek/lip slightly; avoid sharp full-length eyeliner.
- 温柔气质: use low-contrast transitions; soften brow, eye, cheek, and lip edges.
- 清冷高级: lower warmth and saturation; narrow blush; keep contour precise but blended; avoid large glossy highlights.
- 氛围感: allow slightly expanded eye haze or cheek color while keeping landmarks visible.
- 元气活力: increase cheek/lip brightness; keep blush higher and clearer.
- 性感成熟: retain more contrast; sharpen lip or outer eyeliner only when occasion allows.
- 个性酷感: preserve stronger brow/eye lines; reduce sweet rounded blush expansion.

## Occasion Rules

- 日常上学, 通勤工作, 面试: lower saturation; soften technique; simplify eye detail; reduce shimmer, obvious lower-lid extension, and strong contour.
- 约会: keep softness; add gentle cheek/lip brightness; avoid harsh boundaries.
- 聚会, 拍照, 特殊活动: preserve more contrast and highlight; keep diagram boundaries exact.
- 旅行: simplify tools and steps; prioritize durable base and easy touch-up.

## Face-State Goal Rules

- 增加立体感: clarify contour/highlight layers; keep contour brown-gray and blended; avoid hard shadows.
- 减少脸部留白: expand soft blush, lip color, or eye focus toward the blank area; never phrase as "脸太空" or "脸大".
- 弱化轮廓感: lower contour opacity; widen blend edge; move blush slightly inward and softer.
- 放大眼睛: emphasize outer eyeliner visibility, lower-lid shadow/aegyo-sal, and lash curl; do not simply thicken the entire eyeliner.
- 降低眼位: add soft lower-eye presence and allow cheek focus to sit slightly lower, but avoid heavy under-eye blocks.
- 缩短中庭: make blush as horizontal as the tutorial allows; place blush in the midface/under-eye-to-upper-apple-cheek band; keep lowest blush edge near or above the nose-wing line; optionally add a tiny central nose/cheek color connection when the style allows; lower cheek contour start so it begins closer to the mouth-corner/ear-lobe diagonal rather than high cheekbone.

## Face Shape Rules

- 圆脸: avoid very round low blush; use a slightly lifted outer edge and soft lateral contour.
- 椭圆脸: preserve original placement unless goals say otherwise.
- 长脸: avoid vertical nose highlight and low cheek placement; favor horizontal cheek color.
- 方脸: soften jaw contour edges; avoid blocky shadow.
- 菱形脸: avoid expanding high cheekbone width; keep blush slightly inward and soft.
- 心形脸: avoid over-brightening upper cheek width; balance lower-face/lip color.
- 不确定: do not add face-shape-specific changes.

## Skin Type Operation Advice

- 油性肌肤: suggest lighter base layers, matte or satin finish, oil-control prep, and thinner repeated layers.
- 干性肌肤: avoid powder-heavy wording; suggest moisturizing prep, thin layers, and pressing rather than dragging.
- 混合性肌肤: separate T-zone oil control from cheek glow in operation notes.
- 中性肌肤: preserve original skin technique unless other goals apply.
- 敏感肌: reduce layering and friction; avoid repeated rubbing language; suggest patch-friendly gentle application wording.
- 不确定: do not add skin-type constraints.

Skin type must not change `visual_layer_patch.shape`, `position_description`, or placement. It may change user-facing `instruction`, `practice_checklist_patches`, product texture keywords, and prep/setting advice.

## Execution Rules

- 没有专业刷具: replace complex brush language with finger, puff, cotton swab, or included applicator where plausible.
- 产品不齐全: use broad product keywords for same color family, texture, and finish; do not invent brand names.
- 早上时间少: keep the three highest-impact changes; merge minor steps.
- 不会复杂眼妆: simplify gradients into base color + outer third + lash line.
- 不喜欢厚重底妆: lower base opacity; keep concealer localized; avoid full-face layering.

## Conflict Resolution

- Occasion safety beats intensity: 面试/通勤 should soften 性感成熟 or 个性酷感.
- Face-state placement beats style decoration: 缩短中庭 placement still applies even when style is 清冷高级; only color/intensity changes.
- Retained modules keep original color/product family and source clip where possible, but targeted retained modules can still receive placement/range/intensity patches.
- Non-retained modules may be rewritten more strongly to satisfy occasion, style, or execution constraints.
- When unsure, preserve the original tutorial and output `confidence: "low"` with a short reason.
