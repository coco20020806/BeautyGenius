"""DashScope ASR (fun-asr)."""

from __future__ import annotations

import json
import time
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib import request as urlrequest

import dashscope
from dashscope.audio.asr import Transcription
from dashscope.utils.oss_utils import OssUtils

from video_parse.config import ParseConfig


def parse_asr_result(payload: dict[str, Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for transcript in payload.get("transcripts", []):
        for sentence in transcript.get("sentences", []):
            begin = sentence.get("begin_time", 0)
            end = sentence.get("end_time", begin)
            text = (sentence.get("text") or "").strip()
            if not text:
                continue
            segments.append(
                {
                    "start_sec": begin / 1000.0,
                    "end_sec": end / 1000.0,
                    "text": text,
                }
            )
    return segments


def run_asr(
    config: ParseConfig, audio_path: Path, run_dir: Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    t0 = time.perf_counter()
    file_url, _ = OssUtils.upload(
        model=config.asr_model,
        file_path=str(audio_path.resolve()),
        api_key=config.api_key,
    )
    task = Transcription.async_call(
        model=config.asr_model,
        file_urls=[file_url],
        language_hints=["zh", "en"],
    )
    if task.status_code != HTTPStatus.OK:
        raise RuntimeError(f"ASR 提交失败: {getattr(task, 'message', task)}")
    result = Transcription.wait(task=task.output.task_id)
    elapsed = time.perf_counter() - t0
    if result.status_code != HTTPStatus.OK:
        raise RuntimeError(f"ASR 失败: {getattr(result, 'message', result)}")
    segments: list[dict[str, Any]] = []
    raw_results: list[Any] = []
    for item in result.output.get("results", []):
        if item.get("subtask_status") != "SUCCEEDED":
            continue
        url = item.get("transcription_url")
        if not url:
            continue
        body = json.loads(urlrequest.urlopen(url).read().decode("utf-8"))
        raw_results.append(body)
        segments.extend(parse_asr_result(body))
    transcript_doc = {"segments": segments, "raw": raw_results}
    (run_dir / "transcript.json").write_text(
        json.dumps(transcript_doc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return segments, {"elapsed_sec": elapsed, "model": config.asr_model}
