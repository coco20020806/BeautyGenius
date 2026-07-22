#!/usr/bin/env python3
"""Transfer-only smoke test for makeup preview."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image

from makeup_preview.config import PreviewConfig
from makeup_preview.transfer import run_transfer

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILL = REPO_ROOT / "skills" / "kol-makeup-preview"
DEFAULT_INPUT_RUN = (
    REPO_ROOT / "outputs" / "makeup-preview" / "runs" / "20260722_164939"
)
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "makeup-preview" / "transfer-only-runs"


def load_api_key() -> str:
    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if key:
        return key
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        from _qwen_local import DASHSCOPE_API_KEY  # type: ignore

        return DASHSCOPE_API_KEY.strip()
    except ImportError:
        pass
    sys.stderr.write(
        "缺少 DASHSCOPE_API_KEY：请设置环境变量或创建 scripts/_qwen_local.py\n"
    )
    sys.exit(2)


def _image_size(path: Path) -> list[int]:
    with Image.open(path) as im:
        w, h = im.size
    return [w, h]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="仅测试 makeup transfer（三图）"
    )
    parser.add_argument(
        "--run-dir",
        default=str(DEFAULT_INPUT_RUN),
        help="输入 run 目录（默认固定到 20260722_164939）",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="输出根目录（会创建 transfer-only 子 run）",
    )
    parser.add_argument("--n", type=int, default=1, help="生成张数，默认 1")
    args = parser.parse_args()

    input_run = Path(args.run_dir).resolve()
    output_root = Path(args.output_root).resolve()
    if args.n <= 0:
        raise ValueError("--n 必须 >= 1")

    reference = input_run / "reference.jpg"
    target = input_run / "target.jpg"
    tutorial_before = input_run / "tutorial_before.jpg"
    missing = [str(p) for p in (reference, target, tutorial_before) if not p.is_file()]
    if missing:
        sys.stderr.write("缺少输入文件:\n- " + "\n- ".join(missing) + "\n")
        sys.exit(2)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_run = output_root / stamp
    out_run.mkdir(parents=True, exist_ok=False)

    config = PreviewConfig(
        api_key=load_api_key(),
        skill_dir=DEFAULT_SKILL,
    )

    try:
        (
            names,
            prompt_version,
            requested_size,
            prompt_text_version,
            prompt_fallback,
            _prompt_mode,
            _scope,
        ) = run_transfer(
            reference_path=reference,
            target_path=target,
            config=config,
            run_dir=out_run,
            tutorial_before_path=tutorial_before,
            n=args.n,
            output_canvas_path=target,
        )
    except RuntimeError as e:
        sys.stderr.write(f"transfer 失败: {e}\n")
        sys.exit(1)

    target_size = _image_size(target)
    outputs: list[dict[str, object]] = []
    all_match = True
    for name in names:
        path = out_run / name
        size = _image_size(path)
        match = size == target_size
        all_match = all_match and match
        outputs.append(
            {
                "filename": name,
                "path": str(path),
                "size": size,
                "size_match_target": match,
            }
        )

    result = {
        "input_run_dir": str(input_run),
        "input_images": {
            "reference": str(reference),
            "tutorial_before": str(tutorial_before),
            "target": str(target),
        },
        "transfer": {
            "model": config.image_model,
            "prompt_version": prompt_version,
            "prompt_text_version": prompt_text_version,
            "requested_size": requested_size,
            "prompt_fallback": prompt_fallback,
            "n": args.n,
        },
        "target_size": target_size,
        "outputs": outputs,
        "size_match": all_match,
    }
    (out_run / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    verdict = "PASS" if all_match else "FAIL"
    print(out_run)
    print(out_run / "result.json")
    print(f"[{verdict}] target={target_size}, outputs={[o['size'] for o in outputs]}")
    if not all_match:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(2)
