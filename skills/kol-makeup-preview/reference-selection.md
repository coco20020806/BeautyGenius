# KOL 参考帧选择

输入：`beauty-video-parse` 的 run 目录（含 `analysis.json`、`keyframes/`）或用户指定的 `--reference-image`。

实现：`packages/makeup-preview/makeup_preview/reference_pick.py` → `resolve_transfer_reference`。

上游 after/before 选帧纠错见 [beauty-video-parse/makeup-replication-refs.md](../beauty-video-parse/makeup-replication-refs.md)（refs v1.1）。

## 优先级（默认自动）

### P0 — 片尾复刻妆后（v2.1，首选）

当 `analysis.json` 的 `contract_version` 为 **v2.1** 且存在 [`makeup_replication_refs.after`](../beauty-video-parse/makeup-replication-refs.md)：

- 图片：`keyframes/{after.filename}`（通常 `复刻-妆后-*.jpg`）→ 拷贝为 run 内 **`reference.jpg`**（transfer **图1**）
- 教程妆前：`keyframes/{before.filename}` → 拷贝为 **`tutorial_before.jpg`**（transfer **图2**，有 before 时**必须**拷贝并参与生成）
- 标记：`reference_tier: replication_after`，`keyframe_role: replication_after`
- `pair_validation.pass != true` 或 after 单帧未通过时仍可选中，但 `warnings` 含 `replication_pair_not_validated` / 相应码
- CLI **`--strict-replication`**：pair 未通过、或 after 单帧失败则**中止**

三图 transfer 约定见 [transfer-prompt.md](transfer-prompt.md) v2。

### P2 回退 — `step_end_face`（v2 或未产出复刻帧）

- 条件：`role == step_end_face`，优先 `validation.pass == true`
- 排序：靠后步骤 + 较大 `timestamp_sec`（见 `PREFERRED_PRIMARIES`）
- 标记：`reference_tier: step_end_face`
- 通常**无**教程妆前 → transfer **降级二图 v1**，`warnings` 含 `transfer_without_tutorial_before`

### P3 — `makeup_detail`

- 无合格 end_face 时使用；`warning: partial_reference`（及无 before 时的二图降级）

### P4 — `--reference-step`

- **跳过 P0**，仅在指定 `step_name` 下选 `step_end_face`

### 手动 — `--reference-image`

- 覆盖自动选帧；`reference_tier: manual`；无教程妆前 → 二图 v1 降级

## 输出（preview.json.reference）

```json
{
  "source": "parse_run",
  "parse_run_dir": "outputs/runs/...",
  "parse_contract_version": "v2.1",
  "reference_tier": "replication_after",
  "keyframe_role": "replication_after",
  "filename": "复刻-妆后-01-005548.jpg",
  "after_source": "tail_segment",
  "replication_pair_pass": true
}
```

有 before 时另见 `tutorial_replication` / `tutorial_before` 元数据（文件名、source）。

## Agent

- 有 v2.1 parse run 时**不要**默认用中间步骤 end_face 代替片尾妆后。
- after 质量依赖 parse 侧单帧 `makeup_complete`；勿在 after 明显为对比素颜时继续静默生成。
- 全链路见 [docs/REPLICATE_PIPELINE.md](../../docs/REPLICATE_PIPELINE.md)。
