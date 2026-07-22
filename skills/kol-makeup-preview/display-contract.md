# 展示契约 — Makeup Preview UI / API

本文件约束下游 API 组装与 Preview 页摘要区的展示语义。Skill pipeline（`preview.json` 图像管线）**不生成 UI**，但下游必须遵守本契约。

相关实现：`packages/api-server/api_server/preview_assembler.py`、`frontend/src/pages/PreviewPage.tsx`、`frontend/src/components/BeforeAfterSlider.tsx`。

## 摘要标签

| 字段 | 来源 | 规则 |
|------|------|------|
| `duration` | 上传视频真实时长 `tutorial.duration`（秒，来自 parse `video.duration_sec`） | 见下方格式；**禁止**用 `tutorial.estimated_time` 填此标签 |
| `style` | `tutorial.style_tags[0]` | 缺省「自然妆感」（enrichment 前可不随视频变化） |
| `occasion` | `tutorial.occasion_tags` 用 ` · ` 拼接 | 缺省「日常」 |

### `duration` 格式

| 条件 | 展示文案 |
|------|----------|
| `duration < 60`（秒） | `约 N 秒`（N 为整数秒） |
| `duration ≥ 60` | `约 N 分钟`（`N = max(1, round(duration / 60))`） |
| 缺失或 ≤ 0 | `约 15 分钟` |

`estimated_time`（如 `ceil(duration_sec / 10)`）可保留作跟练预估，**不得**驱动时钟标签。

## 妆浓淡色块 `intensityLevels`

摘要区色块是 **妆后浓淡控件**，不是妆容配色摘要。

固定 5 档（浅 → 深 / 低 → 高 opacity）：

| id | color | opacity |
|----|-------|---------|
| `L1` | `#ead6cf` | `0.2` |
| `L2` | `#d8aaa0` | `0.4` |
| `L3` | `#b87870` | `0.6` |
| `L4` | `#8e554f` | `0.8` |
| `L5` | `#5c3a36` | `1.0` |

- 点击越深色块 → 妆后对比图 `opacity` 越高。
- 默认选中 **`L4`**（opacity `0.8`）。
- API 字段：`intensityLevels: Array<{ id, color, opacity }>`。
- 兼容字段 `palette` 可继续返回同序颜色数组；UI 应以 `intensityLevels` 为准。

## 对比区渲染

在保留左右 clip-path 对比滑块的前提下：

1. **妆前图**（底层）：`mix-blend-mode: multiply`（正片叠底）。
2. **妆后图**（上层，受滑块裁切）：`opacity` 由当前 `intensityLevels` 档位控制。
3. 滑块与浓淡控件可并存：滑块控制可见区域，色块控制妆后整体透明度。
