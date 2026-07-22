---
name: picture-makeup
description: >-
  Generates per-step makeup module diagrams from tutorial.json and a fixed base
  face template using qwen3.7-plus for prompts and wan2.7-image-pro for image
  editing. Use when the user wants step illustration, 模块图示, 着色范围标注,
  or picture makeup after video parse and tutorial mapping.
disable-model-invocation: true
---

# Picture Makeup（步骤模块图示）

Skill 源码目录：`<repo-root>/skills/picture_makeup/`（Beauty Genius 仓库内 [`skills/picture_makeup/`](README.md)）。

根据 **文本描述 + 固定底图**，为教程每一步生成 **着色范围示意图示**（与 [`kol-makeup-preview`](../kol-makeup-preview/) 相同使用 **`wan2.7-image-pro`**，但为 **单底图编辑**，非整妆迁移）。

## 何时使用

- 已有 [`beauty-video-parse`](../beauty-video-parse/) parse run，且含 [`tutorial-mapper`](../tutorial-mapper/) 产出的 **`tutorial.json`**。
- 用户要 **按步骤生成模块图示**、在底图上 **色块标注着色范围**、或校对跟练 Step 的视觉说明。
- 需要结合 parse **`keyframes/`** 丰富 prompt 后再生成图。

**不在本 skill**：整妆抄妆预览、视频解析、Tutorial 映射本身、Face++ 试妆。

## 前置条件

| 项 | 要求 |
|----|------|
| `parse_run_dir` | 含 `tutorial.json`（`contract_version: tutorial.v1`） |
| `keyframes_dir` | `parse_run_dir/keyframes/`（与 tutorial 中 `keyframe_refs` 一致） |
| `skill_dir` | `<repo-root>/skills/picture_makeup` |
| 底图 | **`skill_dir/image_format.png`** 必须存在；缺失则 **中止** 并提示用户放置 |
| 密钥 | `DASHSCOPE_API_KEY` |

若无 `tutorial.json`，先执行 [`tutorial-mapper`](../tutorial-mapper/SKILL.md)。

## 流水线（Agent 顺序）

对 **`tutorial.steps[]` 按数组顺序** 逐步处理（含 prep/base；见 [step-prompt-qwen.md](step-prompt-qwen.md) 兜底规则）。

1. **Load inputs** — 读 `tutorial.json`；确认 `image_format.png` 存在。
2. **Base prompt（文本）** — 每步：`visual_layer`（着色/范围）+ `instruction` / `product` / `part` → **`qwen3.7-plus`** → `base_prompt`。详见 [step-prompt-qwen.md](step-prompt-qwen.md)。**此阶段不得使用关键帧。**
3. **Enrich（视觉）** — 从 `keyframe_refs` 选 1–3 帧 → **`qwen3.7-plus`** 多模 JSON → 仅 **`appendix`**；**`final_prompt = base_prompt + appendix`**（无分隔符直接拼接）。**不得改写或删减 `base_prompt`。** 详见 [keyframe-enrich-qwen.md](keyframe-enrich-qwen.md)。
4. **Diagram（图像）** — 从 `skill_dir` 加载 [diagram-prompt-wan.md](diagram-prompt-wan.md) 静态块 + 嵌入 `final_prompt` → **`wan2.7-image-pro`**（图1 = `image_format.png`）。详见 [diagram-prompt-wan.md](diagram-prompt-wan.md)。
5. **Write run** — 落盘结构见 [output-contract.md](output-contract.md)。
6. **Report** — 输出 run 路径、`manifest.json` 逐步 `status` 与 warnings。

调试时可 **仅跑指定 `step_id`**（跳过其余步，仍更新 manifest 中对应条目为 `skipped`）。

## Agent 硬约束

- 密钥不得写入 Git；仅环境变量或 gitignore 本地文件。
- 第 2 阶段：**禁止**修改第 1 阶段 `base_prompt` 的任何字符；冲突时以 base 为准，只写不冲突的 `appendix`。
- 调用 wan 时：`skill_dir` 用于读取 `diagram-prompt-wan.md`；底图路径固定为 `skill_dir/image_format.png`。
- 改 prompt 模板须同步对应 `.md` 与 `manifest` 中的 `prompt_text_version`（若文档有版本号）。

## 验收清单

- [ ] `skills/picture_makeup/image_format.png` 存在
- [ ] `parse_run_dir/tutorial.json` 且 `contract_version === tutorial.v1`
- [ ] 每步有 `steps/<step_id>/base_prompt.txt`
- [ ] 每步 `final_prompt.txt` **以 `base_prompt` 为前缀**（自检：`final_prompt.startswith(base_prompt)`）
- [ ] 每步至少尝试 1 次 wan；成功则有 `diagram_01.jpg`
- [ ] `manifest.json` 含 `image_model: wan2.7-image-pro`、`text_model` / `vision_model: qwen3.7-plus`
- [ ] 无关键帧 enrich 时：`warnings` 含 `no_keyframes_for_enrich` 且 `final_prompt === base_prompt`

## 延伸阅读

| 文档 | 内容 |
|------|------|
| [step-prompt-qwen.md](step-prompt-qwen.md) | 第 1 阶段 base_prompt |
| [keyframe-enrich-qwen.md](keyframe-enrich-qwen.md) | 第 2 阶段 append-only enrich |
| [diagram-prompt-wan.md](diagram-prompt-wan.md) | wan 单图 prompt 与调用 |
| [output-contract.md](output-contract.md) | run 目录与 manifest |
| [reference.md](reference.md) | API、模型、故障 |
| [examples.md](examples.md) | Agent 操作示例 |
| [module-structure.md](module-structure.md) | Phase 2 包化边界 |

上游：[`tutorial-mapper`](../tutorial-mapper/) · [`beauty-video-parse`](../beauty-video-parse/)。  
wan 调用形态参考：[`kol-makeup-preview/transfer-prompt.md`](../kol-makeup-preview/transfer-prompt.md)。
