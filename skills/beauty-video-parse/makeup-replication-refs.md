# 复刻参考对 — before + after（步骤边界）

版本：refs **v1.2** · 契约 **analysis.json `contract_version: v2.1`**

主策略：按化妆步骤时间边界取妆前/妆后全脸；片尾 hints / 片尾扫描仅作**回退**。

## 用途

从美妆教程视频中抽出**一对人脸参考图**，供下游将教程妆容**复刻到用户脸上**：

| 帧 | 语义 | 下游用法 |
|----|------|----------|
| **after** (`replication_after`) | 教程化妆流程结束后的**全脸成品**（通常取末个化妆主类步骤结束处） | 风格 / 颜色 / 全脸妆效参考（preview 三图中的妆后） |
| **before** (`replication_before`) | 流程开始时的素颜或极淡妆基线（默认取**时间序第一步**的 `step_start_face`） | 教程妆前对照；三图 transfer 的图2 |

**不属于** [step-taxonomy.md](step-taxonomy.md) 的 12 主类：不新增 `steps[]` 条目，仅顶层 `makeup_replication_refs`。

**明确不要**：

- 片头预告成妆冒充成品；片尾对比卡的**素颜侧**冒充 after
- 用「视频物理末尾」或「最后一个任意步骤」（可能是闲聊/关注引导）直接当 after，而不校验是否为化妆主类

---

## 步骤集合（排序与过滤）

```text
steps_active = [s in steps if not (s.taxonomy.skipped == true)]
# 按时间排序（不要只用 step_index）
first = min(steps_active, key=time_range.start_sec)
last_makeup = max(
  [s in steps_active if primary in 12主类枚举],
  key=time_range.end_sec
)
```

- 12 主类见 [step-taxonomy.md](step-taxonomy.md) / [taxonomy-enums.json](taxonomy-enums.json)。
- 若无任何化妆主类步骤：after 进入片尾回退路径，并记 `after_no_makeup_step`。

---

## before 主策略（默认）

1. 取 **first** 步骤中 `role == step_start_face` 的关键帧（可复用 `keyframes/` 已有 JPG，或同 `timestamp_sec` 再抽到 `复刻-妆前-*`）。
2. L1 通过后跑单帧 L2 `replication_before`（全脸、五官清晰、`makeup_minimal` / 明显更素）。
3. L2 失败：在原 `timestamp_sec` 的 **±1.5s**（候选：0、+1.5、−1.5）最多 3 次重抽 + 单帧 L2。
4. 仍失败：`validation.pass: false`，`source` 仍为 `first_step_start`。

`before.source` 主值：`first_step_start`（历史别名 `tutorial_baseline` 可读作同义兼容）。

**回退（仅主策略不可用时）**：无 `step_start_face` → `baseline_before_sec` / hints / 片尾 sequence 素颜侧；警告 `before_fallback_hint`。

---

## after 主策略

1. 取 **last_makeup**。
2. **优先**该步 `role == step_end_face`：L1 + 单帧 L2 `replication_after`（须 `makeup_complete: true`，非对比素颜侧）。通过 → `source: last_step_end`。
3. 失败则在步末窗扫描：  
   `W = min(15, max(3, step_duration))` 秒，  
   窗 `[end_sec - W, end_sec]`，步长 **1s**，每帧 L1 + 单帧 L2；取第一个（或最佳）`makeup_complete` → `source: last_step_scan`。
4. 仍失败 → **片尾回退**（见下），警告 `after_fallback_tail`。

---

## 片尾回退（非主路径）

仅当步骤边界 after（或 before）失败时使用。片尾窗：

```text
tutorial_end = max(steps[i].time_range.end_sec)
tail_span    = min(0.25 * duration_sec, 90)
window_start = max(tutorial_end, duration_sec - tail_span)
window_end   = duration_sec
```

回退顺序（与旧版类似，但**不得**盲信 hint）：

1. `split` + crop 成妆侧 → 单帧 L2  
2. `tail_after_sec` 在窗内 → 抽帧 + 单帧 L2；失败作废 hint  
3. 窗内 1s 扫描 + `makeup_complete`  
4. 窗口中点 + `tail_segment_fallback` + `pass: false`

`after.source` 回退值：`tail_split` | `tail_segment` | `tail_segment_fallback`。

Vision `replication_hints` 仍可产出（见 [reference.md](reference.md)），仅服务回退。

---

## 输出契约（analysis.json v2.1）

```json
"makeup_replication_refs": {
  "refs_version": "1",
  "after": {
    "role": "replication_after",
    "timestamp_sec": 0,
    "label": "步骤结束完成妆容",
    "filename": "复刻-妆后-01-HHmmss.jpg",
    "source": "last_step_end",
    "validation": {
      "pass": true,
      "l1_pass": true,
      "makeup_complete": true,
      "reason": ""
    }
  },
  "before": {
    "role": "replication_before",
    "timestamp_sec": 0,
    "label": "复刻基线妆前",
    "filename": "复刻-妆前-01-HHmmss.jpg",
    "source": "first_step_start",
    "validation": {
      "pass": true,
      "l1_pass": true,
      "makeup_minimal": true,
      "reason": ""
    }
  },
  "pair_validation": {
    "same_person": true,
    "before_is_bareer": true,
    "after_is_full_makeup": true,
    "pass": true,
    "reason": ""
  }
}
```

### source 枚举

| 字段 | 值 |
|------|-----|
| `after.source` | `last_step_end` \| `last_step_scan` \| `tail_split` \| `tail_segment` \| `tail_segment_fallback` |
| `before.source` | `first_step_start` \| `tutorial_baseline`（兼容）\| `tail_split` \| `tail_sequence` |

### meta.replication_refs.warnings（可选）

| 码 | 含义 |
|----|------|
| `after_fallback_tail` | after 步骤边界失败，已走片尾回退 |
| `before_fallback_hint` | before 未用首步 start，走了 hints/回退 |
| `after_no_makeup_step` | 无可用化妆主类步骤 |
| `after_hint_rejected_by_l2` | 片尾 hint 被单帧 L2 拒绝 |
| `sequence_before_missing` | sequence 缺 `tail_before_sec`（回退路径） |

---

## QA

见 [keyframe-validation.md](keyframe-validation.md)。

- after / before **各自**单帧 L2 为硬条件；`validation` 不得仅写「L1通过」却 `pass: true`。
- Pair L2 仅在两侧单帧均 pass 后执行；**Pair 通过不能代替** after 的 `makeup_complete`。

---

## 失败与下游

- 单帧或 Pair 失败仍保留 JPG；下游不得在 `pass != true` 时静默当成功参考（`--strict-replication`）。
- `--skip-replication-refs`：不写本字段，`contract_version` 保持 **v2**。

---

## 维护同步

1. [output-contract.md](output-contract.md)  
2. [keyframe-validation.md](keyframe-validation.md)  
3. [SKILL.md](SKILL.md)  
4. `packages/video-parse/video_parse/replication_refs.py`  
5. [kol-makeup-preview](../kol-makeup-preview/)（消费 after/before 文件，不改选帧逻辑）
