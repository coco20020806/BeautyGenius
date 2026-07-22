# makeup-preview

KOL 整妆个人预览包。Skill：`skills/kol-makeup-preview/`。

```python
from pathlib import Path
from makeup_preview import PreviewConfig, run_preview_job

result = run_preview_job(
    parse_run_dir=Path("outputs/runs/20260721_225221"),
    reference_image=None,
    user_photo=None,
    use_baseline=True,
    baseline="female",
    reference_step=None,
    output_root=Path("outputs/makeup-preview"),
    config=PreviewConfig(api_key="...", skill_dir=Path("skills/kol-makeup-preview")),
)
```
