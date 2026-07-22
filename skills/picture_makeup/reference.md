# 技术参考 — picture-makeup

## 环境

| 变量 | 用途 |
|------|------|
| `DASHSCOPE_API_KEY` | `qwen3.7-plus`（文本 + 视觉 JSON）+ `wan2.7-image-pro`（图示生成） |

可选：`dashscope.base_http_api_url = https://dashscope.aliyuncs.com/api/v1`

## 模型分工

| 阶段 | 模型 | 文档 |
|------|------|------|
| base_prompt | `qwen3.7-plus`（**MultiModalConversation**，纯文本） | [step-prompt-qwen.md](step-prompt-qwen.md) |
| enrich | `qwen3.7-plus`（多图） | [keyframe-enrich-qwen.md](keyframe-enrich-qwen.md) |
| diagram | `wan2.7-image-pro` | [diagram-prompt-wan.md](diagram-prompt-wan.md) |

## 上游输入

| 来源 | 路径 |
|------|------|
| Tutorial | `parse_run_dir/tutorial.json`（[`tutorial.v1`](../../packages/tutorial-mapper/tutorial_mapper/schemas/tutorial.v1.json)） |
| 关键帧 | `parse_run_dir/keyframes/*.jpg` |
| 底图 | `skills/picture_makeup/image_format.png` |

Tutorial 映射：[`tutorial-mapper`](../tutorial-mapper/SKILL.md)  
视频解析：[`beauty-video-parse`](../beauty-video-parse/SKILL.md)

## wan2.7-image-pro

- SDK：`dashscope.aigc.image_generation.ImageGeneration.call`
- **单图** + text（非 kol-makeup-preview 三图 transfer）
- 响应解析与落盘：同 [`makeup_preview/transfer.py`](../../packages/makeup-preview/makeup_preview/transfer.py) 中 `_extract_images_from_response` 思路
- 失败：写 `diagram_error.txt` / `wan_raw.json`

## qwen3.7-plus

- **文本与视觉均用** `MultiModalConversation.call`（`file://` 图片或纯 `[{"text":...}]`）
- **勿用** `Generation.call` 调 `qwen3.7-plus`（会 `url error`）
- JSON 解析失败时可参考 tutorial-mapper 的 `repair_json`（`qwen3.7-plus`），非必须

## Skill 路径（canonical）

```text
<repo-root>/skills/picture_makeup/
```

索引：[skills/README.md](../README.md)

## 与 kol-makeup-preview 的区别

| 项 | kol-makeup-preview | picture-makeup |
|----|--------------------|----------------|
| 目的 | 整妆迁移到用户脸 | 单步范围示意图 |
| wan 输入图 | 2–3 张 | 1 张 `image_format.png` |
| prompt 来源 | 固定 transfer 长 prompt | qwen 两步 + diagram 静态块 |

## 故障

| 现象 | 处理 |
|------|------|
| 无 `DASHSCOPE_API_KEY` | 环境变量或 `scripts/_qwen_local.py`（与仓库其他脚本一致） |
| 缺 `image_format.png` | 中止；提示放入 skill 根目录 |
| 无 `tutorial.json` | 先跑 tutorial-mapper |
| `keyframe_refs` 无文件 | enrich 跳过，`no_keyframes_for_enrich` |
| `final_prompt` 不以 base 开头 | 禁止继续 wan；重跑 enrich 或手工修正 appendix |
| `url error, please check url!` | `qwen3.7-plus` 误用了 `Generation`（文本端点）；应改用 `MultiModalConversation` |

## 成本提示

每步约 2 次 qwen + 1 次 wan。调试时只跑单个 `step_id`。
