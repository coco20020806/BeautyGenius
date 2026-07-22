# api-server

FastAPI 接入层，实现 `/api/v1/makeup/tasks` 契约并串联 video-parse → tutorial-mapper → makeup-preview。

启动（仓库根目录）：

```powershell
.\scripts\run-api.ps1      # 仅 API
.\scripts\run-dev.ps1      # API + 前端（一条命令）
```
