# 视频解析 → Tutorial 映射 → 妆容预览 串联

Beauty Genius 端到端本地 job：教程视频 → parse run → `tutorial.json` → makeup preview → job manifest。

## 命令

```powershell
cd "<repo-root>"
# 全流程（解析 + Tutorial 映射 + 平均脸预览；不调 wan 时用 -SkipTransfer）
.\scripts\run-beauty-replicate.ps1 -Video "D:\tutorial.mp4" -UseBaseline -SkipTransfer

# 冒烟：parse 跳过 L2；Tutorial 仅确定性映射（关 enrich）
.\scripts\run-beauty-replicate.ps1 -Video "D:\tutorial.mp4" -Mode fast -UseBaseline -SkipTransfer

# 已有 parse run（仍会跑 Tutorial 映射，除非 -SkipTutorialMap）
.\scripts\run-beauty-replicate.ps1 -ParseRun "outputs\runs\20260721_225221" -UseBaseline -SkipTransfer

# 仅解析 + Tutorial，跳过 preview
.\scripts\run-beauty-replicate.ps1 -ParseRun "outputs\runs\<id>" -SkipPreview

# 个人自拍
.\scripts\run-beauty-replicate.ps1 -ParseRun "outputs\runs\<id>" -UserPhoto "D:\selfie.jpg"
```

Python 等价：`scripts/run_beauty_replicate.py`。

| 开关 | 作用 |
|------|------|
| `-Mode fast` / `--mode fast` | parse 跳过 L2；Tutorial **仅确定性**映射 |
| `-SkipTutorialMap` | 不跑 tutorial-mapper |
| `-SkipTextEnrich` / `-SkipVisionEnrich` | full 下关闭一侧 enrich |
| `-SkipPreview` / `-SkipTransfer` | 跳过预览 / 不调 wan |

默认向 **stderr** 打印解析 `[n/10]`、映射 `[map n/6]` 与 `[job] …`；可用 `-Quiet` / `--quiet` / `BEAUTY_PARSE_QUIET=1` 关闭。

## 数据流

1. **解析**（可选）：`video_parse.run_parse_job` → `analysis.json` + `keyframes/`（默认可含 v2.1 复刻参考）。
2. **Tutorial 映射**（默认开启，有 parse run 时）：`tutorial_mapper.run_mapper_job` → `tutorial.json` + `enrichment_meta.json`（含 `tutorial_step_validation` 步骤语义校验，写在同一 parse run 目录）。
3. **上游妆面图**：`makeup_preview.resolve_transfer_reference` 优先 `makeup_replication_refs.after` + `before`。
4. **预览**：`makeup_preview.run_preview_job` → `outputs/makeup-preview/runs/<id>/`。
5. **Manifest**：`outputs/jobs/<timestamp>/manifest.json` 链接 parse / tutorial / preview。

**步骤示例图（picture-makeup）**：不在本串联脚本默认步骤中；由 Web API 在用户进入跟练示例页时按需触发（`POST …/step-diagrams`），产物在 `outputs/picture-makeup/runs/` 并复制到任务 `media_dir`。CLI：`scripts/run_picture_makeup.py`。

## manifest.json（job_version: 1）

| 字段 | 说明 |
|------|------|
| `parse_run_dir` | 解析产物目录 |
| `tutorial_path` | `tutorial.json` 路径（未映射则为 null） |
| `tutorial_id` | Tutorial 对象 id |
| `preview_run_dir` | 预览产物目录 |
| `upstream_reference.tier` | `replication_after` \| `step_end_face` \| `makeup_detail` \| `manual` |
| `target` | 与 `preview.json.target` 一致 |

## 退出码

| Code | 含义 |
|------|------|
| 0 | 成功 |
| 1 | 用户照质检失败 |
| 2 | 参数/文件/API 错误（含 Tutorial 映射失败） |
| 3 | `--strict-replication` 且复刻参考未验证 |

## Agent 注意

- 预览前优先确认 parse run 为 **v2.1** 且含 `makeup_replication_refs`；否则建议重跑 parse（勿 `--skip-replication-refs`）。
- Tutorial 映射失败会中断 job（exit 2）；可用 `-SkipTutorialMap` 跳过。
- 有教程 before 时：transfer 为 **图1=妆后、图2=教程妆前、图3=用户/平均脸**；无 before 时降级为二图并 warning。
- Transfer 的 **text** 从 [kol-makeup-preview/transfer-prompt.md](../skills/kol-makeup-preview/transfer-prompt.md) 加载（长 prompt），非 `config.py` 短句 fallback（md 缺失时才会 fallback）。

## 相关 Skill

- [beauty-video-parse](../skills/beauty-video-parse/)
- [tutorial-mapper](../skills/tutorial-mapper/)
- [kol-makeup-preview](../skills/kol-makeup-preview/)
