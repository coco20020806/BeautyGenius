# Beauty Genius

基于视频解析的美妆 Agent：用户上传美妆相关视频后，Agent 完成解析，并提供知识总结与沉淀能力。

## 能力规划

- **视频理解**：URL 或本地文件 → 抽帧、字幕/语音转写、内容结构化
- **知识总结**：步骤、产品、技巧、注意事项等可检索摘要
- **知识沉淀**：长期积累用户关心的美妆知识点（待实现）

## 本地视频解析（Qwen3.7-Plus + ASR）

在 PowerShell 中解析本地美妆教程视频（步骤时间轴、字幕/画面文字/口播、关键帧）：

```powershell
cd "Beauty Genius"
.\scripts\parse-beauty-video.ps1
# 或
.\scripts\parse-beauty-video.ps1 -VideoPath "D:\Videos\makeup.mp4"
```

依赖：`ffmpeg`（见 `scripts/install-ffmpeg-watch.ps1`）、Python 3.10+。首次运行会自动创建 `.venv` 并安装 `requirements.txt`（含可编辑包 `packages/video-parse`）。

解析核心实现在 **`packages/video-parse`**（`run_parse_job`）；CLI 仅负责参数与密钥。

API 密钥：设置环境变量 `DASHSCOPE_API_KEY`，或复制 `scripts/_qwen_local.example.py` 为 `scripts/_qwen_local.py` 并填入密钥（该文件已 gitignore）。

每次运行结果在 `outputs/runs/<时间戳>/`：`analysis.json`、`keyframes/`、`transcript.json`、`meta.json`。

## 本地妆容预览（KOL 抄整妆）

在已有解析 run 或手动参考图基础上，将妆面适配到用户正脸或平均脸底图（`wan2.7-image-pro`）：

```powershell
cd "Beauty Genius"
.\scripts\run-makeup-preview.ps1 -ParseRun "outputs\runs\20260721_225221" -UseBaseline
# 个人自拍（须平视正脸）：
.\scripts\run-makeup-preview.ps1 -ParseRun "outputs\runs\20260721_225221" -UserPhoto "D:\Photos\selfie.jpg"
```

输出：`outputs/makeup-preview/runs/<时间戳>/`（`preview.json`、`preview_01.jpg` 等）。Skill 文档：[`skills/kol-makeup-preview/`](skills/kol-makeup-preview/)。

**仅测 transfer（三图）**：

```powershell
cd "Beauty Genius"
python .\scripts\test_makeup_transfer_only.py
# 可选覆盖输入 run
python .\scripts\test_makeup_transfer_only.py --run-dir "outputs\makeup-preview\runs\20260722_164939"
```

该脚本会真实调用 WAN，并在 `outputs/makeup-preview/transfer-only-runs/<时间戳>/` 输出 `preview_01.jpg`、`transfer_raw.json`、`transfer_prompt.txt`、`result.json`；其中 `result.json` 会给出 `size_match`（是否与 `target.jpg` 同尺寸）。

**一键串联**（解析 + 预览 + job manifest）：

```powershell
.\scripts\run-beauty-replicate.ps1 -ParseRun "outputs\runs\<id>" -UseBaseline -SkipTransfer
```

见 [`docs/REPLICATE_PIPELINE.md`](docs/REPLICATE_PIPELINE.md)。

**Agent Skills（canonical 路径）**：[`skills/`](skills/) — 含 [`beauty-video-parse`](skills/beauty-video-parse/)（视频解析）、[`kol-makeup-preview`](skills/kol-makeup-preview/)（KOL 整妆个人预览）。安装到 Cursor 见各目录 `README.md` 或 [`skills/README.md`](skills/README.md)。

## 视频解析 Skill

本项目推荐使用 Cursor Agent Skill **watch**（[claude-video](https://github.com/bradautomates/claude-video)）作为视频解析能力基础：

```bash
npx skills add bradautomates/claude-video -g
```

Windows 上需安装 `ffmpeg`、`yt-dlp`，可选配置 Whisper API（见 `~/.config/watch/.env` 或本仓库 `.env.example`）。

## 仓库

- GitHub: https://github.com/coco20020806/BeautyGenius

## 开发

```bash
git clone https://github.com/coco20020806/BeautyGenius.git
cd BeautyGenius
cp .env.example .env   # 按需填写
```

应用代码与目录结构将随功能迭代补充。

## Web 联调（FastAPI + 前端）

移动端 Web 前端位于 [`frontend/`](frontend/)（上游：[makeup-frontend](https://github.com/qi00531/makeup-frontend)）。HTTP 接入层见 [`packages/api-server/`](packages/api-server/) 与 [`docs/API.md`](docs/API.md)。

**一条命令启动（推荐）**：

```powershell
cd "Beauty Genius"
# 可选：$env:SKIP_TRANSFER = "1"   # 省 wan 调用，先通 UI
# 可选：$env:DASHSCOPE_API_KEY = "..."
.\scripts\run-dev.ps1
```

浏览器打开 **http://127.0.0.1:5174**。按 **Ctrl+C** 会同时停止 API 与前端。

**开发捷径（跳过照片 + 解析，直达预览）**：将本机最新 parse / preview run 写入固定配置后，在首页底部点击「跳过前两步（开发）」。

```powershell
.\.venv\Scripts\python.exe .\scripts\pin-latest-dev-runs.py
$env:ENABLE_DEV_SHORTCUTS = "1"   # run-dev.ps1 默认已开启
.\scripts\run-dev.ps1
```

配置见 [`configs/dev-pinned-runs.json`](configs/dev-pinned-runs.json)；新跑完流水线后请重新执行 `pin-latest-dev-runs.py`。

（脚本通过 `npm.cmd` 启动前端，避免 PowerShell 执行策略拦截 `npm.ps1`。）

**分开启动**（便于单独看 API 日志）：

```powershell
.\scripts\run-api.ps1
# 另开终端
cd frontend
copy .env.example .env   # 首次
npm install              # 首次
npm run dev
```

纯前端演示（不连后端）：`frontend/.env` 中设置 `VITE_USE_MOCK=1`。

## License

TBD
