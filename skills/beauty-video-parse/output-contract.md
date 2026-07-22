# 输出契约 — analysis.json 与 run 目录



Schema 源文件（按版本）：



- **v2**：`packages/video-parse/video_parse/schemas/beauty_video_analysis.v2.json`

- **v2.1**：`packages/video-parse/video_parse/schemas/beauty_video_analysis.v2.1.json`（v2 + 复刻参考对）



历史路径 `scripts/schemas/beauty_video_analysis.schema.json` 仅作兼容说明，见该目录 [README.md](../../scripts/schemas/README.md)。



## Run 目录产物



| 文件 | 说明 |

|------|------|

| `analysis.json` | 主结果（v2 或 v2.1） |

| `taxonomy-coverage.json` | 本视频覆盖的主类 / sub_steps / 默认跳过项 |

| `keyframe-qa.json` | 步级关键帧 L1/L2 + **`replication_pair`**（v2.1） |

| `meta.json` | 含 `taxonomy_warnings`、`keyframe_qa`、**`replication_refs`**（v2.1） |

| `transcript.json` | ASR |

| `keyframes/` | JPG（含 `复刻-妆前-*` / `复刻-妆后-*`） |

| `replication_hints.json` | 可选；vision 返回的 hints 快照 |



## 顶层（analysis.json）



| 字段 | 含义 |

|------|------|

| `contract_version` | `"v2"` 或 **`"v2.1"`**（启用复刻参考对时为 v2.1） |

| `taxonomy_version` | 如 `"v1"`，对应 [taxonomy-enums.json](taxonomy-enums.json) |

| `skipped_primaries` | 未出现且默认跳过的主类（如眉毛、睫毛） |

| `makeup_replication_refs` | **仅 v2.1**；见 [makeup-replication-refs.md](makeup-replication-refs.md) |

| `video` | 源路径、时长、fps、analysis_path、upload_compressed |

| `generated_at` / `model` / `asr_model` | 元数据 |

| `steps` | 步骤数组 |



## makeup_replication_refs（v2.1）



| 字段 | 含义 |

|------|------|

| `refs_version` | `"1"` |

| `after` | `replication_after` 关键帧对象 |

| `before` | `replication_before` 关键帧对象 |

| `pair_validation` | 同人、素/浓、综合 `pass` |



复刻帧 `role` 枚举（**不在** `steps[].keyframes` 内）：`replication_before`、`replication_after`。



单帧字段：`timestamp_sec`、`label`、`filename`、`source`、`validation`（同步级 keyframe）。



`after.source`：`last_step_end` \| `last_step_scan` \| `tail_split` \| `tail_segment` \| `tail_segment_fallback`  

`before.source`：`first_step_start` \| `tutorial_baseline`（兼容）\| `tail_split` \| `tail_sequence`

选帧主策略见 [makeup-replication-refs.md](makeup-replication-refs.md) **refs v1.2**（步骤边界；片尾为回退）。



## taxonomy-coverage.json



| 字段 | 含义 |

|------|------|

| `present_primaries` | 本教程出现的 12 类主类 |

| `skipped_primaries` | 未出现的主类（含默认「不做」） |

| `sub_steps_by_primary` | 每主类实际出现的细分列表 |

| `all_primaries_enum` | 完整主类枚举 |



## Step 对象



| 字段 | 含义 |

|------|------|

| `step_name` | 必须等于 `taxonomy.primary`，且为 12 主类之一 |

| `taxonomy.primary` | 同 step_name |

| `taxonomy.sub_steps` | 来自 [step-taxonomy.md](step-taxonomy.md) / enums |

| `taxonomy.skipped` | 通常为 false；占位跳过步时为 true |

| `time_range` / `text` | 时间轴与 subtitles / on_screen / voiceover |

| `keyframes` | 步级关键帧（role 仅 step_start_face / step_end_face / makeup_detail） |



## 步级 Keyframe 对象



| 字段 | 含义 |

|------|------|

| `label` | `makeup_detail` **优先**为 taxonomy 细分名（如「外V区」） |

| `validation` | QA 完成后写入（见 [keyframe-validation.md](keyframe-validation.md)） |

| `validation.pass` | L1 + L2 均满足时为 true（含 L2 窗内重抽后的最终结果；skip L2 时见该文档） |

| `timestamp_sec` | 最终采用时刻；L2 重抽成功后可能与视觉初值不同 |

| 其余 | `index_in_step`、`role`、`filename` |



## keyframe-qa.json



| 字段 | 含义 |

|------|------|

| `summary` | 步级帧汇总，见下表 |

| `items[]` | 每步每帧 l1、validation、pass；可选 `l2_retry`（v2.2） |

| `vision_by_step` | 步级 L2 原始结果（首轮批量） |

| `replication_pair` | **v2.1**：`items`（before/after 单帧 QA）、`pair_validation` |



### summary（步级）



| 字段 | 含义 |

|------|------|

| `total` / `passed` / `failed` | 帧计数（`failed` 为最终仍未通过数） |

| `retried_extracts` | **抽帧次数合计**（含 L1 与步级 L2 重抽产生的每一次 extract） |

| `l2_skipped` | 是否跳过步级 L2 |

| `l2_retried_frames` | **v2.2**：进入过 L2 窗内重抽的帧数 |

| `l2_rescued` | **v2.2**：重抽后变为 pass 的帧数 |



### items[].l2_retry（可选，v2.2）



仅当该帧触发过步级 L2 失败重抽时出现。规则见 [keyframe-validation.md](keyframe-validation.md)。



| 字段 | 含义 |

|------|------|

| `attempts` | 重抽阶段实际尝试的候选次数 |

| `candidates_tried` | 尝试过的时间戳（秒）列表 |

| `replaced` | 是否已用通过帧替换原抽帧 |

| `final_timestamp_sec` | 最终采用的时间戳 |



## meta.json 扩展（v2.1）



| 字段 | 含义 |

|------|------|

| `replication_refs` | `{ pass, after_source, before_source, reason, warnings? }` 汇总；`warnings` 可选码见 [makeup-replication-refs.md](makeup-replication-refs.md) |

| `enable_replication_refs` | 是否启用本 run 的复刻参考抽取 |



## 版本



- **v2.1**：v2 + `makeup_replication_refs` + 片尾 before/after（当前默认启用复刻时）。

- **v2**：taxonomy + coverage + 步级 keyframe validation；无 `makeup_replication_refs`。

- **keyframe-qa v2.2 字段**（`l2_retry` / `l2_retried_frames` / `l2_rescued`）：写在 `keyframe-qa.json` / `meta.keyframe_qa`，**不** bump `analysis.json` 的 `contract_version`。

- v1 仅作历史 run 参考。


