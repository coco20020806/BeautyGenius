# 使用示例

## Windows（推荐）

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned   # 首次如需
cd "C:\Users\fei.kong\Desktop\Beauty Genius"
.\scripts\parse-beauty-video.ps1 -VideoPath "C:\path\to\tutorial.mp4"
```

交互输入路径：

```powershell
.\scripts\parse-beauty-video.ps1
```

## 直接调用 Python

```powershell
.\.venv\Scripts\python.exe .\scripts\parse_beauty_video.py --video "C:\path\to\tutorial.mp4"
```

### `--mode fast`（推荐冒烟入口）

跳过 L2 关键帧视觉质检（仍 L1 抽帧；`meta.mode=fast`，`keyframe-qa` 汇总含 `l2_skipped: true`）。正式验收请用默认 `full`。

```powershell
.\scripts\parse-beauty-video.ps1 -VideoPath "C:\path\to\tutorial.mp4" -Mode fast
.\.venv\Scripts\python.exe .\scripts\parse_beauty_video.py --video "C:\path\to\tutorial.mp4" --mode fast
```

等价细粒度开关（与 `--mode fast` 叠加时任一为真即关 L2）：

```powershell
.\.venv\Scripts\python.exe .\scripts\parse_beauty_video.py --video "C:\path\to\tutorial.mp4" --skip-keyframe-qa
```

跳过片尾复刻参考对（`contract_version` 保持 v2，无 `makeup_replication_refs`）：

```powershell
.\.venv\Scripts\python.exe .\scripts\parse_beauty_video.py --video "C:\path\to\tutorial.mp4" --skip-replication-refs
```

关闭阶段进度：

```powershell
.\.venv\Scripts\python.exe .\scripts\parse_beauty_video.py --video "C:\path\to\tutorial.mp4" --quiet
# 或
$env:BEAUTY_PARSE_QUIET = "1"
# PowerShell 包装：
.\scripts\parse-beauty-video.ps1 -VideoPath "C:\path\to\tutorial.mp4" -Quiet
```

## 环境变量

```powershell
$env:DASHSCOPE_API_KEY = "sk-..."
# 可选：关闭进度
$env:BEAUTY_PARSE_QUIET = "1"
```

或复制 `scripts/_qwen_local.example.py` → `scripts/_qwen_local.py` 并填入密钥（已 gitignore）。

## 阶段进度样例（stderr）

```
[1/10] Probe… (0s)
[2/10] Prepare（跳过压缩）… (1s)
[3/10] 抽取音频… (1s)
[4/10] Vision 分析中…（并行） (2s)
[5/10] ASR 转写中…（并行） (2s)
[6/10] Merge + taxonomy… (180s)
[7/10] 关键帧 QA… (181s)
[7/10] 关键帧 QA（步骤 2/7）定妆… (200s)
[8/10] 复刻参考对… (240s)
[9/10] Schema 校验… (250s)
[10/10] 写盘完成 (251s)
```

L2 失败帧会留在 `keyframes/` 且 `validation.pass: false`；`summary.failed` 反映最终未通过数。步级 L2 窗内重抽（`l2_rescued`）为 v2.2 设计，**当前未写入产物**。

## 成功输出示例（结构摘要）

```
outputs/runs/20260721_225221/
├── analysis.json      # contract v2.1 + taxonomy + makeup_replication_refs
├── taxonomy-coverage.json
├── keyframe-qa.json   # 含 replication_pair（v2.1）
├── meta.json
├── transcript.json
├── keyframes/
│   ├── 妆前-01-000000.jpg
│   ├── 复刻-妆前-01-000012.jpg
│   ├── 复刻-妆后-01-000358.jpg
│   └── ...
├── audio.wav
└── raw_vision_response.txt
```

`analysis.json` 中一步的片段形态：

```json
{
  "step_index": 1,
  "step_name": "妆前",
  "time_range": {
    "start_sec": 0.0,
    "end_sec": 38.0,
    "start_label": "0:00",
    "end_label": "0:38"
  },
  "text": {
    "subtitles": [{ "time_sec": 0, "text": "..." }],
    "on_screen": [{ "time_sec": 0, "text": "..." }],
    "voiceover": [{ "start_sec": 0.5, "end_sec": 4.2, "text": "..." }]
  },
  "keyframes": [
    {
      "index_in_step": 1,
      "role": "step_start_face",
      "timestamp_sec": 0.0,
      "filename": "妆前-01-000000.jpg"
    }
  ]
}
```

v2.1 顶层复刻参考片段：

```json
{
  "contract_version": "v2.1",
  "makeup_replication_refs": {
    "refs_version": "1",
    "after": {
      "role": "replication_after",
      "timestamp_sec": 358.0,
      "filename": "复刻-妆后-01-000358.jpg",
      "source": "tail_segment",
      "validation": { "pass": true, "l1_pass": true, "reason": "L1通过" }
    },
    "before": {
      "role": "replication_before",
      "timestamp_sec": 12.0,
      "filename": "复刻-妆前-01-000012.jpg",
      "source": "tutorial_baseline",
      "validation": { "pass": true, "l1_pass": true, "reason": "L1通过" }
    },
    "pair_validation": {
      "same_person": true,
      "before_is_bareer": true,
      "after_is_full_makeup": true,
      "pass": true,
      "reason": "同人且素/浓关系正确"
    }
  }
}
```

## 安装 skill 到 Cursor（将来）

将本目录链接或复制到：

- 项目级：从 `<repo-root>/skills/beauty-video-parse/` 复制或 junction 到 `.cursor/skills/beauty-video-parse/`
- 个人级：`~/.cursor/skills/beauty-video-parse/`（源码仍以仓库 `skills/` 为准）

在对话中 @beauty-video-parse 或描述「解析美妆教程视频」触发。

## 反例

- 仅粘贴路径字符串而不带 `-VideoPath` → PowerShell 只会 echo，不会运行解析。
- 期望 Qwen 单独完成口播 → 必须保留 ASR 路径。
