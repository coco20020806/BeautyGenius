# api-server

FastAPI 接入层，实现 `/api/v1/makeup/tasks` 契约并串联 video-parse → tutorial-mapper → makeup-preview。

启动（仓库根目录）：

```powershell
.\scripts\run-api.ps1      # 仅 API
.\scripts\run-dev.ps1      # API + 前端（一条命令）
```

## Linux 系统依赖

云上无桌面环境需安装：

```bash
sudo bash scripts/install-linux-deps.sh
```

提供 `ffmpeg`/`ffprobe`，以及 MediaPipe 所需的 `libgl1` + `libglib2.0-0`（否则妆容预览阶段报 `libGL.so.1` 缺失）。详见 [`docs/API.md`](../../docs/API.md)。
