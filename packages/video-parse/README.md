# video-parse

Beauty Genius 美妆教程视频解析包。Skill 文档：`skills/beauty-video-parse/`。

默认产出 `contract_version` **v2.1**，含片尾 `makeup_replication_refs`（`复刻-妆前` / `复刻-妆后`）。可用 `ParseConfig(enable_replication_refs=False)` 或 CLI `--skip-replication-refs` 保持 v2。

```python
from pathlib import Path
from video_parse import ParseConfig, run_parse_job

result = run_parse_job(
    Path("tutorial.mp4"),
    output_root=Path("outputs/runs"),
    config=ParseConfig(api_key="...", skill_dir=Path("skills/beauty-video-parse")),
)
```
