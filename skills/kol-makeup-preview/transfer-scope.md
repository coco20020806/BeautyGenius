# Transfer 教程范围（动态 Prompt）

版本：**v1**  
适用：从 parse run 关联的 makeup preview **transfer 调用之前**，解析「允许改妆区域」并决定 `prompt_mode`（`full` | `scoped`）。

## 目标

- 教程仅覆盖局部主类（如仅 **唇妆**）时，wan 文案 **scoped**：只允许在对应面部区域迁移妆效；**图3 其余区域须与原图一致**。
- 全脸或多主类教程、或无 scope 数据时，使用既有 **full** 长 prompt（[`transfer-prompt.md`](transfer-prompt.md) 的 `prompt-v2` / `prompt-v1`）。
- **不改** API 图拓扑（仍 v2 三图 / v1 二图）；**不改** `target_display.jpg` / `preview_display.jpg` 全脸对齐展示逻辑。

## 输入与优先级

| 优先级 | 来源 | 字段 |
|--------|------|------|
| 1 | `{parse_run_dir}/taxonomy-coverage.json` | `present_primaries` |
| 2 | `{parse_run_dir}/tutorial.json`（coverage 缺失或 `present_primaries` 为空时） | `steps[].taxonomy_primary` 去重、保序 |
| 3 | 无 parse run（仅 `--reference-image` 等） | 无 scope → **`prompt_mode: full`**，`warnings` 含 `transfer_scope_fallback_full` |

`skipped_primaries` **Never** 当作可改区域。

## `application_primaries`

从 `present_primaries`（或 tutorial fallback）得到，再应用：

| 规则 | 说明 |
|------|------|
| 排除 `妆前` | 妆前为流程/打底说明，**不单独**打开底妆 §1；若仅有 `妆前`+`唇妆`，application 为 **`["唇妆"]`** |
| 保留其余主类 | 与 [taxonomy-enums.json](../beauty-video-parse/taxonomy-enums.json) 一致的 12 主类 |

## `prompt_mode` 判定

实现常量（变更须同步本文）：

| 常量 | 值 |
|------|-----|
| `FULL_SCOPE_PRIMARY_COUNT` | **6** |

| mode | 条件 |
|------|------|
| **`full`** | `application_primaries` 为空；或 `\|application_primaries\| >= FULL_SCOPE_PRIMARY_COUNT`；或显式 `transfer_scope_override=full`（Phase 2 配置/CLI） |
| **`scoped`** | 其余：`application_primaries` 非空且数量 &lt; 6 |

## 主类 → 允许修改的 prompt 区域

与 [`transfer-prompt.md`](transfer-prompt.md) 长正文编号清单对齐；scoped 时对下列段落取 **并集**：

| taxonomy_primary | 长 prompt 段落 |
|------------------|----------------|
| 底妆、遮瑕、定妆 | §1 底妆 |
| 眉毛 | §2 眉毛 |
| 眼睛、眼线、睫毛 | §3 眼妆 |
| 修容、腮红、高光 | §4 腮红/修容/高光 |
| 唇妆 | §5 唇妆 |
| 妆前 | （不映射；见上节排除） |

§6 点痣/局部细节：仅当 **application_primaries** 含对应区域且参考差分中可见时，在 scoped 附录中允许；默认 scoped 唇妆-only **不** 打开全脸点痣迁移。

`allowed_region_labels`（写入 `preview.json`）：上表并集对应的中文区域标签，如 `["唇妆"]` 或 `["唇妆","修容"]`（与主类列表一致即可，实现可 duplicate 合并）。

## 拼接规则

1. 加载 layout 对应 **base** 块：`prompt-v2` 或 `prompt-v1`（full 基线正文）。
2. 若 `prompt_mode === scoped`：加载 `prompt-v2-scope-appendix`（或 v1 的 `prompt-v1-scope-appendix`），替换占位符：
   - `{{PRIMARY_LIST_ZH}}` → `application_primaries` 顿号连接
   - `{{REGION_LIST_ZH}}` → `allowed_region_labels` 顿号连接（可与主类相同）
3. **最终 text** = `base + "\n\n" + appendix`（单段写入 `transfer_prompt.txt`）。
4. scoped 下 base 中「完整妆容 1–6」清单仍保留，以 **附录约束优先** 收窄语义。

## 差分理解（scoped）

- 仍用图1（妆后）相对图2（妆前）理解 **允许区域内** 的妆前妆后差分。
- **禁止** 将图1 中未覆盖主类区域的妆效迁移到图3。

## 失败策略

- 缺 `taxonomy-coverage.json` 且无法从 `tutorial.json` 得到主类：**不阻断** job；`prompt_mode: full`，`scope.source: default_full`，warning `transfer_scope_fallback_full`。
- 仅用 tutorial fallback：`scope.source: tutorial.json`，可选 warning `transfer_scope_from_tutorial`。

## 输出（契约）

见 [output-contract.md](output-contract.md) → `preview.json.transfer.prompt_mode`、`preview.json.transfer.scope`。

## 验收

- [ ] 嘴部-only parse（`present_primaries: ["唇妆"]`）：`prompt_mode=scoped`，`transfer_prompt.txt` 含「教程范围约束」与「唇妆」。
- [ ] 全脸/多主类（≥6 application 主类）：`prompt_mode=full`，无 scope 附录。
- [ ] 手动 `--reference-image` 无 parse：`full` + `transfer_scope_fallback_full`。
- [ ] UI 仍可读 `target_display` / `preview_display` 全脸对比。

## 示例片段

**full**（末尾无附录，节选）：

```text
…请按目标人物自己的脸部结构贴合以下妆容（细节以图1相对图2为准）：
1. 底妆：…
…
禁止：
- 不得换脸…
```

**scoped**（base 同上 + 附录）：

```text
…禁止：
- 不得换脸…

【教程范围约束】本视频教程仅涉及以下化妆主类：唇妆。
仅允许在图3上修改与上述主类对应的妆效区域（唇妆）。
图3上未列出的区域（肤色、眉形、眼妆、腮红、修容、高光、唇形比例、发型等）须保持与图3原图一致，不得新增或加深任何妆效。
参考图1相对图2的差分，只用于理解上述允许区域内的妆效；不得将图1中其他区域的妆迁移到图3。
```

## v1 边界

- Scoped 依赖模型遵从 prompt，**不保证** 100% 像素级局部；后续可加 mask / 二次 QA。
- 多主类局部（如 唇妆+修容）：scoped 并集，仍非 full。

## 实现

- 规范：本文 + [`transfer-prompt.md`](transfer-prompt.md) 代码块。
- 代码：`packages/makeup-preview/makeup_preview/scope_loader.py`、`prompt_compose.py`（见 [module-structure.md](module-structure.md)）。
