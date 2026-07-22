"""ffmpeg / ffprobe preprocessing."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from video_parse.config import ParseConfig

SUBPROCESS_CAPTURE = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}


def resolve_ffmpeg(config: ParseConfig) -> str:
    if config.ffmpeg_path:
        return config.ffmpeg_path
    from shutil import which

    found = which("ffmpeg")
    if found:
        return found
    local = Path.home() / ".local" / "ffmpeg" / "bin" / "ffmpeg.exe"
    if local.is_file():
        return str(local)
    raise RuntimeError("未找到 ffmpeg")


def resolve_ffprobe(config: ParseConfig, ffmpeg: str) -> str:
    if config.ffprobe_path:
        return config.ffprobe_path
    probe = Path(ffmpeg).parent / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
    if probe.is_file():
        return str(probe)
    from shutil import which

    found = which("ffprobe")
    if found:
        return found
    raise RuntimeError("未找到 ffprobe")


def to_file_uri(path: Path) -> str:
    return f"file://{path.resolve().as_posix()}"


def run_cmd(args: list[str]) -> None:
    proc = subprocess.run(args, **SUBPROCESS_CAPTURE)
    if proc.returncode != 0:
        raise RuntimeError(
            f"命令失败 ({proc.returncode}): {' '.join(args)}\n{proc.stderr or proc.stdout}"
        )


def probe_video(ffprobe: str, video_path: Path) -> dict[str, Any]:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=avg_frame_rate,duration",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(video_path),
    ]
    proc = subprocess.run(cmd, check=True, **SUBPROCESS_CAPTURE)
    data = json.loads(proc.stdout)
    duration = 0.0
    if data.get("format", {}).get("duration"):
        duration = float(data["format"]["duration"])
    fps = 25.0
    streams = data.get("streams") or []
    if streams:
        if streams[0].get("duration"):
            duration = float(streams[0]["duration"])
        rate = streams[0].get("avg_frame_rate", "25/1")
        if isinstance(rate, str) and "/" in rate:
            num, den = rate.split("/", 1)
            if float(den) != 0:
                fps = float(num) / float(den)
    return {"duration_sec": duration, "fps": round(fps, 3)}


def compress_for_upload(
    ffmpeg: str, source: Path, dest: Path, max_bytes: int
) -> None:
    scales = ["-2:720", "-2:540", "-2:480"]
    crfs = [28, 32, 36]
    dest.parent.mkdir(parents=True, exist_ok=True)
    for scale in scales:
        for crf in crfs:
            if dest.exists():
                dest.unlink()
            run_cmd(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(source),
                    "-vf",
                    f"scale={scale}",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    str(crf),
                    "-c:a",
                    "aac",
                    "-b:a",
                    "96k",
                    str(dest),
                ]
            )
            if dest.stat().st_size <= max_bytes:
                return
    raise RuntimeError(
        f"压缩后仍超过 {max_bytes // (1024 * 1024)}MB，请缩短视频或提供公网 URL"
    )


def prepare_video_for_api(
    ffmpeg: str, source: Path, run_dir: Path, max_bytes: int
) -> tuple[Path, bool]:
    size = source.stat().st_size
    if size <= max_bytes:
        return source, False
    proxy = run_dir / "upload_proxy.mp4"
    print(
        f"视频 {size / (1024 * 1024):.1f}MB，正在压缩到 {max_bytes // (1024 * 1024)}MB 以内…"
    )
    compress_for_upload(ffmpeg, source, proxy, max_bytes)
    return proxy, True


def extract_audio(ffmpeg: str, video_path: Path, wav_path: Path) -> None:
    run_cmd(
        [
            ffmpeg,
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(wav_path),
        ]
    )
