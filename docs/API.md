# Beauty Genius HTTP API（MVP）

FastAPI 接入层，契约与 [`frontend/docs/backend-integration.md`](../frontend/docs/backend-integration.md) 对齐。

## 启动

**一条命令（API + 前端）**：

```powershell
cd "<repo-root>"
.\scripts\run-dev.ps1
```

浏览器：**http://127.0.0.1:5174**。Ctrl+C 停止全部。

**仅 API**：

```powershell
cd "<repo-root>"
.\scripts\run-api.ps1
```

服务默认：`http://127.0.0.1:8000`  
健康检查：`GET /health`

## Linux 系统依赖（云部署）

无桌面服务器除 `pip install -r requirements.txt` 外还需：

- **ffmpeg / ffprobe** — 视频解析抽帧
- **libgl1 + libglib2.0-0** — MediaPipe/OpenCV（妆容预览）；缺失会出现 `libGL.so.1: cannot open shared object file`

```bash
sudo bash scripts/install-linux-deps.sh
# 或
sudo apt-get install -y libgl1 libglib2.0-0 ffmpeg
```

装完后重启 uvicorn / API 进程。

## 环境变量

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 解析 / 映射 / 预览（必需，除非 `SKIP_TRANSFER=1` 且仅测上传） |
| `SKIP_TRANSFER=1` | 全局跳过 wan transfer（与任务 `skip_transfer` 为或关系）；首页也可勾选「跳过妆容预览」按任务跳过 |
| `PARSE_MODE=fast` | 无 `fastParse` 字段时的服务端默认；上传表单 `fastParse` 优先 |
| `API_PUBLIC_BASE_URL` | 预览图 URL 前缀，默认 `http://127.0.0.1:8000` |
| `ENABLE_DEV_SHORTCUTS=1` 或 `APP_ENV=development` | 开启 `POST /api/v1/makeup/dev/skip-to-preview`（读取 `configs/dev-pinned-runs.json`） |
| `OCCUPANCY_MAX_CONCURRENT` | 重任务最大并发数，默认 `2` |
| `OCCUPANCY_STALE_SECONDS` | 占用槽过期秒数，默认 `2700` |

## 任务存储

- 元数据：`outputs/tasks/{taskId}/task.json`
- 上传文件：`outputs/tasks/{taskId}/upload/`
- 预览媒体副本：`outputs/tasks/{taskId}/media/`

## 路由

| 方法 | 路径 |
|------|------|
| POST | `/api/v1/makeup/tasks` |
| POST | `/api/v1/makeup/tasks/{taskId}/photo` |
| POST | `/api/v1/makeup/tasks/{taskId}/analysis` |
| GET | `/api/v1/makeup/tasks/{taskId}/analysis` |
| GET | `/api/v1/makeup/tasks/{taskId}/preview` |
| GET | `/api/v1/makeup/tasks/{taskId}/tutorial` |
| POST | `/api/v1/makeup/tasks/{taskId}/adjustment` |
| POST | `/api/v1/makeup/tasks/{taskId}/step-diagrams` |
| GET | `/api/v1/makeup/tasks/{taskId}/step-diagrams` |
| GET | `/api/v1/makeup/server/status` |
| POST | `/api/v1/makeup/dev/skip-to-preview`（仅 dev；见 `ENABLE_DEV_SHORTCUTS`） |
| GET | `/media/{taskId}/{filename}` |

MVP 无用户鉴权；任务 ID 即访问凭证。

### 照片上传与质检

`POST /api/v1/makeup/tasks/{taskId}/photo`：

- **跳过**（`skipped=true`）：直接 `photo_ready`，使用标准人脸底图；不跑质检
- **上传本人照片**：落盘后同步执行 L0 → L1 MediaPipe → L2 Qwen（`validate_only`）。仅通过后才写入 `photo_ready`，响应含 `validationPass: true`，task 记录 `photo_qa`
- **不合格**：HTTP `422`，`code: USER_PHOTO_REJECTED`，`message` 为质检原因；**不**进入 `photo_ready`，前端应留在照片页提示重拍

解析流水线若已有通过的 `photo_qa`，妆容预览阶段跳过二次质检。

### 并发占用（忙线）

重任务（`analysis` / `adjustment` / `step-diagrams`）共用进程内槽位，**默认最多 2 个不同 task 同时跑**。第 3 个启动请求返回：

- HTTP `409`
- `code`: `SERVER_BUSY`
- `message`: 含「排队中」

`GET /api/v1/makeup/server/status` 返回：

```json
{ "busy": false, "activeCount": 1, "maxConcurrent": 2, "slots": [...] }
```

`busy === true` 表示槽位已满。同一 `taskId` 幂等重入不额外占槽。

| 环境变量 | 说明 |
|----------|------|
| `OCCUPANCY_MAX_CONCURRENT` | 最大并发槽位数，默认 `2` |
| `OCCUPANCY_STALE_SECONDS` | 槽位过期秒数，默认 `2700`（45 分钟） |

**部署注意**：占用状态在进程内存中，云上请使用 **uvicorn 单 worker**；多 worker / 多机下互斥无效。

上传 `POST /tasks` 表单：`video`（必填）、`fastParse`（可选，默认 true，对应 `-Mode fast`）、`skipMakeupPreview`（可选，默认 false；为 true 时写入 `task.skip_transfer`，等价跳过 wan 妆容预览）。

ETA 历史样本：`outputs/tasks/_eta_stats.jsonl`（用于改善 `remainingSeconds`）。

### 开发：跳过至预览

```http
POST /api/v1/makeup/dev/skip-to-preview
```

需 `ENABLE_DEV_SHORTCUTS=1` 或 `APP_ENV=development`。读取 [`configs/dev-pinned-runs.json`](../configs/dev-pinned-runs.json) 中的 `parse_run_dir` 与 `preview_run_dir`，注册 `status=completed` 任务并复制预览图到 `outputs/tasks/{taskId}/media/`。路径无效时 `409`，`code` 为 `DEV_RUNS_NOT_PINNED`。固定路径：`python scripts/pin-latest-dev-runs.py`。

## 前端联调

```powershell
# 推荐：一条命令
.\scripts\run-dev.ps1
```

或分开启动：

```powershell
# 终端 1
.\scripts\run-api.ps1

# 终端 2
cd frontend
copy .env.example .env
npm install
npm run dev
```

Vite 已配置 `/api` 与 `/media` 代理到 `8000`；也可在 `.env` 设置 `VITE_API_BASE_URL=http://127.0.0.1:8000`。

本地 mock：`VITE_USE_MOCK=1 npm run dev`
