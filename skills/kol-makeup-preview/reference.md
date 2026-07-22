# 技术参考 — DashScope / MediaPipe

## 环境

| 变量 | 用途 |
|------|------|
| `DASHSCOPE_API_KEY` | L2 质检 + `wan2.7-image-pro` 生成 |

可选：`dashscope.base_http_api_url = https://dashscope.aliyuncs.com/api/v1`

## 模型分工

| 阶段 | 模型 |
|------|------|
| 用户正脸 L2 | `qwen3.7-plus`（JSON） |
| 妆容预览 | `wan2.7-image-pro`（多图编辑 / 参考生成） |

## wan2.7-image-pro

- SDK：`dashscope.aigc.image_generation.ImageGeneration.call`（同步 `multimodal-generation`）
- 多图 + text：见 [transfer-prompt.md](transfer-prompt.md)（**v2 三图**；缺教程妆前回退 v1 二图）；范围见 [transfer-scope.md](transfer-scope.md)，落盘 `preview.json.transfer.prompt_mode` / `transfer.scope`
- `size`：默认配置 `2K`；管线按 `target.jpg` 宽高比在 `1280*1280`、`1280*720`、`720*1280`、`1024*1024` 中选最接近比例，否则仍用 `2K`（`makeup_preview.config.resolve_image_size`）
- 生成后：`harmonize_preview_pair` 将 `preview_01.jpg` 对齐到 `target.jpg`（**保持与 target 相同宽高**）；人脸裁切展示写入 `target_display.jpg` / `preview_display.jpg`（见 `preview_align.py`）
- 默认 `n=1`；实现见 `packages/makeup-preview/makeup_preview/transfer.py`
- 错误：检查 HTTP 状态、`response.message`；失败时 run 内写 `transfer_error.txt` / `transfer_raw.json`

## MediaPipe L1

- 包：`mediapipe`（版本在 `packages/makeup-preview/pyproject.toml` 锁定）
- 模型：`face_landmarker.task`（首次运行下载或随包提供路径配置）

## 平均脸底图

见 [baselines.md](baselines.md)：

```text
skills/kol-makeup-preview/female_average_face.png
skills/kol-makeup-preview/male_average_face.png
```

## Skill 路径（canonical）

```text
<repo-root>/skills/kol-makeup-preview/
```

索引：[skills/README.md](../README.md)

## 故障

| 现象 | 处理 |
|------|------|
| 无 `DASHSCOPE_API_KEY` | 提示配置环境变量或 `_qwen_local.py` 模式（与 video-parse 一致） |
| L1 无脸 | 用户重拍；见 user-flow 指引 |
| 生成图无 URL | 查 `transfer_raw.json`，更新 `transfer.py` 解析 |
| 底图缺失 | 确认 Skill 根目录存在 `female_average_face.png` / `male_average_face.png` |
