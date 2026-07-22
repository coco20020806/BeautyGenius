# 用户自拍质检 — 平视正脸

版本：v1.1（阈值适度放宽）  
结果写入：`outputs/makeup-preview/runs/<id>/user-photo-qa.json`  
实现参考：`packages/makeup-preview/makeup_preview/face_gate.py`、`face_qa.py`

## 目标

确保上传图为 **单人、接近平视正脸**，适合作为 `wan2.7-image-pro` 的上妆底图。允许日常自拍的轻微侧脸/歪头、淡妆与美颜。

## L0 文件基础（必须通过）

| 检查项 | 规则 |
|--------|------|
| 格式 | JPG / PNG / WEBP |
| 体积 | ≥ 4 KB，≤ 8 MB（`PreviewConfig.max_user_photo_bytes`） |
| 分辨率 | 短边 ≥ 480 px，长边 ≤ 4096 px |
| 可读 | 可解码为 RGB，非损坏文件 |

失败 code：`INVALID_FORMAT` / `FILE_TOO_LARGE` / `RESOLUTION_OUT_OF_RANGE` / `UNREADABLE_IMAGE`

## L1 MediaPipe Face Landmarker（必须通过）

- 依赖：`mediapipe` Face Landmarker（本地，无需 Face++）。
- **仅 1 张脸**。

| 检查项 | 规则 | code |
|--------|------|------|
| 人脸数 | `face_count == 1` | `NO_FACE` / `MULTIPLE_FACES` |
| 人脸占比 | 框面积 / 图像面积 ∈ [0.05, 0.75] | `FACE_TOO_SMALL` / `FACE_TOO_LARGE` |
| 偏航 yaw | \|yaw\| ≤ 25° | `YAW_TOO_LARGE` |
| 俯仰 pitch | \|pitch\| ≤ 25° | `PITCH_NOT_EYE_LEVEL` |
| 滚转 roll | \|roll\| ≤ 20° | `ROLL_TOO_LARGE` |
| 裁切 | 鼻尖、双眼角、嘴角 landmark 在图内 | `FACE_CROPPED` |

姿态角由 landmark 估计（实现层统一函数，阈值以本表为准）。

**L1 失败时不调用 L2**（节省 API）。

## L2 Qwen 视觉 JSON

- 模型：`qwen3.7-plus`（与 [beauty-video-parse/keyframe-validation.md](../beauty-video-parse/keyframe-validation.md) L2 同风格）。
- 输入：用户图单张 + 固定说明（要求 **仅输出 JSON**）。
- 判定口径：允许淡妆/美颜；仅硬拦口罩/墨镜严重遮眼、大面积遮挡、非人脸主体等。

| 字段 | 类型 | 通过条件 |
|------|------|----------|
| `is_frontal` | bool | true |
| `is_eye_level` | bool | true |
| `occlusion_ok` | bool | true |
| `lighting_ok` | bool | true |
| `suitable_as_makeup_target` | bool | true |
| `pass` | bool | true |
| `reason` | string | 失败时简短中文，给用户看 |

综合 `pass = L1 pass && L2.pass`（写入 `user-photo-qa.json`）。

**API / JSON 解析失败**：软通过（`pass: true`，`l2_soft_pass: true`，`reason` 说明已放行）。L1 已保证单人脸与可用姿态。

## user-photo-qa.json 结构

```json
{
  "contract_version": "v1",
  "pass": true,
  "failed_layer": null,
  "codes": [],
  "l1": { "yaw_deg": 3.2, "pitch_deg": -1.1, "roll_deg": 0.5, "face_area_ratio": 0.22 },
  "l2": { "is_frontal": true, "pass": true, "reason": "" }
}
```

## 非目标（v1）

- 身份核验、与 KOL 是否为同一人  
- 美颜/妆浓打分（除 `suitable_as_makeup_target` 粗筛严重遮挡）

## 维护

修改阈值时同步：本文件、`config.py` 常量、`face_qa.py` prompt。
