"""ffmpeg / ffprobe preprocessing."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from video_parse.config import ParseConfig, resolve_compress_plan

SUBPROCESS_CAPTURE = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
    "errors": "replace",
}

ProgressMessageCallback = Callable[[str], None]


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


def _run_ffmpeg_compress_with_progress(
    ffmpeg: str,
    source: Path,
    dest: Path,
    *,
    scale: str,
    preset: str,
    crf: int,
    duration_sec: float,
    on_progress: ProgressMessageCallback | None,
) -> None:
    args = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-vf",
        f"scale={scale}",
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-c:a",
        "aac",
        "-b:a",
        "96k",
        "-progress",
        "pipe:1",
        "-nostats",
        str(dest),
    ]
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.stdout is not None
    stderr_chunks: list[str] = []

    def _drain_stderr() -> None:
        if proc.stderr is None:
            return
        try:
            stderr_chunks.append(proc.stderr.read() or "")
        except Exception:
            pass

    drain = threading.Thread(target=_drain_stderr, daemon=True)
    drain.start()
    last_report = 0.0
    last_pct = -1
    returncode = -1
    try:
        for raw in proc.stdout:
            line = raw.strip()
            if not line.startswith("out_time_ms="):
                continue
            try:
                out_ms = int(line.split("=", 1)[1])
            except ValueError:
                continue
            if duration_sec <= 0:
                pct = 0
            else:
                pct = min(99, int((out_ms / 1_000_000.0) / duration_sec * 100))
            now = time.monotonic()
            if on_progress and (now - last_report >= 2.0 or pct - last_pct >= 5):
                on_progress(f"压缩中… 约 {pct}%（{scale}/{preset}/crf{crf}）")
                last_report = now
                last_pct = pct
        returncode = proc.wait()
    except Exception:
        proc.kill()
        proc.wait()
        raise
    finally:
        drain.join(timeout=5)

    stderr = "".join(stderr_chunks)
    if returncode != 0:
        raise RuntimeError(
            f"命令失败 ({returncode}): {' '.join(args)}\n{stderr}"
        )


def compress_for_upload(
    ffmpeg: str,
    source: Path,
    dest: Path,
    max_bytes: int,
    *,
    config: ParseConfig,
    duration_sec: float = 0.0,
    on_progress: ProgressMessageCallback | None = None,
) -> None:
    plan = resolve_compress_plan(config)
    dest.parent.mkdir(parents=True, exist_ok=True)
    for index, (scale, preset, crf) in enumerate(plan):
        if index > 0 and on_progress:
            on_progress("仍超限，降档重压…")
        if dest.exists():
            dest.unlink()
        _run_ffmpeg_compress_with_progress(
            ffmpeg,
            source,
            dest,
            scale=scale,
            preset=preset,
            crf=crf,
            duration_sec=duration_sec,
            on_progress=on_progress,
        )
        if dest.stat().st_size <= max_bytes:
            return
    raise RuntimeError(
        f"压缩后仍超过 {max_bytes // (1024 * 1024)}MB，请缩短视频或提供公网 URL"
    )


def prepare_video_for_api(
    ffmpeg: str,
    source: Path,
    run_dir: Path,
    max_bytes: int,
    *,
    config: ParseConfig,
    duration_sec: float = 0.0,
    on_progress: ProgressMessageCallback | None = None,
) -> tuple[Path, bool]:
    size = source.stat().st_size
    if size <= max_bytes:
        return source, False
    proxy = run_dir / "upload_proxy.mp4"
    size_mb = size / (1024 * 1024)
    limit_mb = max_bytes // (1024 * 1024)
    msg = f"正在压缩视频（{size_mb:.1f}MB → 上限 {limit_mb}MB）…"
    print(msg)
    if on_progress:
        on_progress(msg)
    compress_for_upload(
        ffmpeg,
        source,
        proxy,
        max_bytes,
        config=config,
        duration_sec=duration_sec,
        on_progress=on_progress,
    )
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
