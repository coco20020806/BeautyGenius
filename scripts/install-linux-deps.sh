#!/usr/bin/env bash
# Install system packages needed by Beauty Genius on headless Linux (Debian/Ubuntu).
# Usage (on the cloud server, from repo root or anywhere):
#   sudo bash scripts/install-linux-deps.sh
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "请使用 root 或 sudo 运行: sudo bash scripts/install-linux-deps.sh" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -y

# MediaPipe → opencv-contrib-python 在无桌面环境需要 libGL.so.1
if apt-cache show libgl1 >/dev/null 2>&1; then
  apt-get install -y libgl1 libglib2.0-0
else
  # 旧版 Ubuntu
  apt-get install -y libgl1-mesa-glx libglib2.0-0
fi

# 视频解析抽帧 / 探针
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  apt-get install -y ffmpeg
fi

echo "已安装 Linux 系统依赖。请重启 API（uvicorn / systemd）后再试公开版任务。"
echo "验证: python -c \"import cv2; print(cv2.__version__)\""
echo "      python -c \"import mediapipe; print('ok')\""
