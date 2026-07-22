# 美妆教程跟练前端后端联调说明

版本：v0.1  
更新日期：2026-07-22  
适用代码：当前 `main` 分支 React + TypeScript + Vite 前端

## 1. 文档目的

本文用于帮助后端开发同学快速理解当前前端页面、任务流程、数据结构和接口替换位置。当前业务数据由前端模拟服务提供；接入后端时应保留现有页面组件与 TypeScript 类型，通过替换服务实现完成联调。

## 2. 技术栈与启动方式

- React
- TypeScript
- Vite
- React Router
- Vitest + Testing Library

本地启动：

```bash
npm install
npm run dev
```

默认开发地址由 Vite 输出。当前常用启动命令：

```bash
npm run dev -- --host 127.0.0.1 --port 5174
```

质量检查：

```bash
npm test -- --run
npm run build
npm run lint
```

## 3. 页面路由

前端手机画布使用响应式尺寸：宽度在 `320–440px` 间跟随设备视口，高度使用当前设备的 `100dvh`，并通过安全区变量适配刘海屏和底部手势区。浏览器页面本身锁定不滚动，超出内容仅在手机画布内部滚动；桌面预览保持手机宽度并居中显示。

| 路由 | 页面文件 | 用途 | 是否需要后端 |
|---|---|---|---|
| `/` | `src/pages/UploadPage.tsx` | 选择并上传教程视频 | 是 |
| `/photo` | `src/pages/PhotoPage.tsx` | 上传本人照片或跳过 | 是 |
| `/parsing` | `src/pages/ParsingPage.tsx` | 展示解析进度和失败信息 | 是 |
| `/preview` | `src/pages/PreviewPage.tsx` | 展示妆前/妆后效果与适配建议 | 是 |
| `/practice` | `src/pages/PracticePage.tsx` | 展示 tutorial.json 步骤（产品/范围/手法） | 是 |
| `/practice/examples` | `src/pages/StepDiagramsPage.tsx` | 步骤着色范围示例图（按需生成） | 是 |
| `/practice/examples/saved` | `src/pages/CollectSuccessPage.tsx` | 收藏到知识库成功占位页（前端占位，后续再接收藏 API） | 否 |
| `/adjust` | `src/pages/AdjustPage.tsx` | 输入个人风格、脸部匹配和工具限制 | 是（当前 mock） |
| `/tutorial` | `src/pages/TutorialPage.tsx` | 图示教程、步骤时间线与产品信息 | 是（当前 mock） |
| `/eyes` | `src/pages/EyeGuidePage.tsx` | 眼部区域精讲和视频切片 | 是（当前 mock） |
| `/library` | `src/pages/LibraryPage.tsx` | 教程、部位与混搭三个 TAB | 是（当前 mock） |
| `/mix` | `src/pages/MixPage.tsx` | 旧地址，兼容转到 `/library?tab=mix` | 否 |
| `/mix/generating` | `src/pages/MixGeneratingPage.tsx` | 展示预制妆效匹配进度 | 是（当前 mock） |
| `/mix/preview` | `src/pages/MixPreviewPage.tsx` | 展示预制混搭妆前/妆后效果 | 是（当前 mock） |
| `/profile` | `src/pages/ProfilePage.tsx` | 个人档案、学习数据、偏好和隐私入口 | 是（当前 mock） |

核心流程：

```text
上传视频 / → 照片确认 /photo → 解析进度 /parsing → 适配预览 /preview
  ├─ 适合我 → 跟练 /practice → 示例图 /practice/examples（按需生成）
  └─ 需要微调 → /adjust（问卷 → POST …/adjustment 优化 tutorial）→ 跟练 /practice → 示例图
```

适配预览页的返回按钮会直接进入 `/`，不会重新进入解析页。

示例图页在生成完成后可点击「收藏到知识库」，进入勾选模式后经「勾选完成」进入 `/practice/examples/saved` 占位成功页（前端交互闭环，暂无真实收藏 API）。

学习与混搭流程（前端 mock，待 HttpLearningService；无 taskId 时微调仍走本地）：

```text
需要微调（无 task）：/adjust → /tutorial → /eyes
素材混搭：/library?tab=mix → /mix/generating → /mix/preview → /tutorial
素材混搭微调：/mix/preview → /adjust → /tutorial
```
底部导航固定为「首页 / 知识库 / 我的」。`/practice` 仍保留，可通过预览「适合我」进入，但不在底栏展示。混搭编辑已迁入知识库第三个 TAB，旧 `/mix` 地址会保留查询参数后转发。

## 4. 前端代码边界

### 4.1 类型契约

解析与跟练管线类型集中在：

```text
src/types/makeup.ts
```

学习、知识库与混搭类型集中在：

```text
src/types/learning.ts
```

后端返回结构应尽量与这些接口保持一致。`Tutorial`（tutorial.json）与 `IllustratedTutorial`（图示教程 UI）暂并存，不强制统一。

### 4.2 服务接口

前端统一通过 `MakeupService` 调用解析管线能力：

```ts
export interface MakeupService {
  uploadVideo(file: File): Promise<UploadVideoResult>;
  uploadPhoto(file: File | null): Promise<UploadPhotoResult>;
  analyze(taskId: string): AsyncGenerator<AnalysisProgress>;
  getPreview(taskId: string): Promise<MakeupPreview>;
  getTutorial(taskId: string): Promise<Tutorial>;
  startStepDiagrams(taskId: string): Promise<StepDiagramsStartResult>;
  getStepDiagrams(taskId: string): Promise<StepDiagramsResponse>;
  skipToDevPreview(): Promise<DevSkipPreviewResult>;
}
```

当前实现：

```text
src/services/makeupService.ts      # 导出入口（HTTP 优先）
src/services/httpMakeupService.ts  # 已接入真实 API
src/services/httpClient.ts
```

学习与混搭能力：

```text
src/types/learning.ts
src/services/learningService.ts    # 当前本地 mock；后续可新增 HttpLearningService
```

`LearningService` 负责微调问卷、图示教程、眼部精讲、知识库预制素材与混搭预制结果。后端接入时应替换服务实现，不改页面调用方式。

## 5. 当前前端状态存储

当前使用 `sessionStorage` 保存任务流程中的少量数据：

| Key | 写入页面 | 内容 | 用途 |
|---|---|---|---|
| `makeupTask` | 视频上传页 | `UploadVideoResult` | 后续页面读取 `taskId` |
| `makeupPhoto` | 照片确认页 | `{ skipped, fileName }` | 记录用户是否跳过照片 |
| `makeupProgress` | 解析页 | `AnalysisProgress` | 页面刷新后保留最近进度的基础数据 |

注意：

- `sessionStorage` 不是后端任务状态的权威来源。
- 接入后端后，刷新页面应通过 `taskId` 重新查询任务状态。
- 不应在浏览器存储照片二进制、照片地址中的敏感签名或面部分析数据。
- 当前照片页只记录了选择结果，尚未真正调用 `uploadPhoto`。联调时应在“确认上传”和“暂时跳过”操作中分别调用后端照片接口。

## 6. 建议 API

以下路径是前后端联调建议，可以根据后端项目规范调整；字段语义应保持一致。

### 6.1 上传教程视频

```http
POST /api/v1/makeup/tasks
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `video` | File | 是 | MP4 或 MOV，前端限制 500MB |
| `fastParse` | string (`true`/`false`) | 否 | 默认 `true`：对应 CLI `-Mode fast`；`false` 为 full |
| `skipMakeupPreview` | string (`true`/`false`) | 否 | 默认 `false`：为 `true` 时不调 wan 妆容生成（等价 `--skip-transfer`）；与服务端 `SKIP_TRANSFER=1` 为或关系 |

成功响应：

```json
{
  "taskId": "task_01JXYZ",
  "fileName": "daily-look.mp4",
  "fileSize": 24801234,
  "status": "uploaded",
  "parseMode": "fast",
  "skipMakeupPreview": false
}
```
```

对应类型：`UploadVideoResult`。

### 6.2 上传或跳过本人照片

建议统一使用一个接口表达两种行为：

```http
POST /api/v1/makeup/tasks/{taskId}/photo
Content-Type: multipart/form-data
```

上传照片时：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `photo` | File | 是 | JPG、PNG 或 WebP |
| `skipped` | boolean | 是 | `false` |

跳过照片时：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `skipped` | boolean | 是 | `true` |

成功响应：

```json
{
  "photoId": "photo_01JXYZ",
  "previewUrl": "https://cdn.example.com/preview/photo_01JXYZ.jpg",
  "skipped": false
}
```

跳过时：

```json
{
  "photoId": null,
  "previewUrl": null,
  "skipped": true
}
```

对应类型：`UploadPhotoResult`。

### 6.3 启动解析

```http
POST /api/v1/makeup/tasks/{taskId}/analysis
Content-Type: application/json
```

请求体可为空。建议返回 `202 Accepted`：

```json
{
  "taskId": "task_01JXYZ",
  "status": "processing"
}
```

### 6.4 查询解析进度

简单方案使用轮询：

```http
GET /api/v1/makeup/tasks/{taskId}/analysis
```

响应：

```json
{
  "taskId": "task_01JXYZ",
  "progress": 45,
  "currentStage": "识别妆容步骤",
  "remainingSeconds": 16,
  "status": "processing",
  "stages": [
    { "id": "quality-check", "label": "检查视频质量", "status": "completed" },
    { "id": "step-detection", "label": "识别妆容步骤", "status": "active" },
    { "id": "preview-generation", "label": "生成适配预览", "status": "pending" },
    { "id": "hint-generation", "label": "整理关键建议", "status": "pending" }
  ],
  "detailMessage": "[4/10] Vision 分析中…（并行）",
  "logLines": ["[job] 开始解析…", "[1/10] Probe…", "[4/10] Vision 分析中…（并行）"],
  "etaTotalSeconds": 240,
  "completedWeight": 0.35
}
```

对应类型：`AnalysisProgress`。

当前前端的 `analyze()` 返回 `AsyncGenerator`。HTTP 实现可以在生成器内部轮询：

```ts
async *analyze(taskId: string): AsyncGenerator<AnalysisProgress> {
  await request(`/api/v1/makeup/tasks/${taskId}/analysis`, { method: 'POST' });

  while (true) {
    const progress = await request<AnalysisProgress>(
      `/api/v1/makeup/tasks/${taskId}/analysis`,
    );
    yield progress;

    if (progress.status === 'completed' || progress.status === 'failed') return;
    await delay(1500);
  }
}
```

若后端采用 SSE，也可以保持页面层不变，在 `analyze()` 内将事件流转换为 `AsyncGenerator<AnalysisProgress>`。

### 6.5 获取适配预览

```http
GET /api/v1/makeup/tasks/{taskId}/preview
```

响应：

```json
{
  "taskId": "task_01JXYZ",
  "title": "清透玫瑰通勤妆",
  "style": "清透自然",
  "occasion": "通勤 · 日常",
  "difficulty": "新手友好",
  "duration": "约 1 分钟",
  "beforeImage": "https://cdn.example.com/tasks/task_01JXYZ/before.webp",
  "afterImage": "https://cdn.example.com/tasks/task_01JXYZ/after.webp",
  "generationFailed": false,
  "palette": ["#ead6cf", "#d8aaa0", "#b87870", "#8e554f", "#5c3a36"],
  "intensityLevels": [
    { "id": "L1", "color": "#ead6cf", "opacity": 0.2 },
    { "id": "L2", "color": "#d8aaa0", "opacity": 0.4 },
    { "id": "L3", "color": "#b87870", "opacity": 0.6 },
    { "id": "L4", "color": "#8e554f", "opacity": 0.8 },
    { "id": "L5", "color": "#5c3a36", "opacity": 1.0 }
  ],
  "hints": [
    {
      "title": "腮红建议上移",
      "description": "将范围收在眼下到颧骨外侧，更显轻盈。",
      "tone": "adjust"
    }
  ]
}
```

对应类型：`MakeupPreview`。

- `afterImage`：仅真实生成妆后图（`preview_display.jpg` 优先，否则 `preview_01.jpg`）。**禁止**用教程 `reference.jpg` 冒充。若未生成，返回 `null`，并设 `generationFailed: true` 与 `generationFailureReason`（跳过时说明已跳过，否则说明生成失败）。
- `duration`：上传视频**真实时长**标签（`<60s` → `约 N 秒`；否则 `约 N 分钟`），**不用** `estimated_time`。契约见 `skills/kol-makeup-preview/display-contract.md`。
- `intensityLevels`：妆浓淡 5 档；色块越深，妆后对比图 opacity 越高。兼容字段 `palette` 为同序颜色。

### 6.6 获取教程解读（tutorial.json）

```http
GET /api/v1/makeup/tasks/{taskId}/tutorial
```

任务 `status` 为 `completed` 且存在 `tutorial_path` 时，返回磁盘上的 `tutorial.v1` JSON（与 parse run 目录中 `tutorial.json` 一致），并**追加**顶层字段 `videoUrl`（上传原片公开地址，形如 `{API_PUBLIC_BASE_URL}/media/{taskId}/video.mp4`；不写回磁盘）。各步仍含 `video_clip: { start, end }`（秒）。未就绪时返回 `409`，`code` 为 `TUTORIAL_NOT_READY`。

对应类型：`Tutorial`（见 `src/types/makeup.ts`）。跟练页 `/practice` 每步提供「看视频」，用原片 + `video_clip` 时间跳转播放。

### 6.7 步骤示例图（picture-makeup，按需）

启动生成（幂等；主任务 `completed` 且存在 tutorial 后）：

```http
POST /api/v1/makeup/tasks/{taskId}/step-diagrams
```

响应：`202`，`{ "taskId": "...", "status": "processing" | "completed" }`。

查询进度与图片 URL：

```http
GET /api/v1/makeup/tasks/{taskId}/step-diagrams
```

响应：`StepDiagramsResponse`（`status`: `idle` | `processing` | `completed` | `failed`；顶层 `videoUrl` 同上传原片；`steps[].imageUrl` 为 `{API_PUBLIC_BASE_URL}/media/{taskId}/diagram_{stepId}.jpg`；`steps[].videoClip` 来自 tutorial 对应步的 `video_clip`；可选 `steps[].basePrompt`（qwen 第 1 阶段，前端用于截取化妆手法）与 `steps[].finalPrompt`（手法+标注全文）；失败步含 `steps[].error`，全部失败时顶层 `failureReason` 会汇总首条错误）。

未就绪：`409`，`STEP_DIAGRAMS_NOT_READY` 或 `TUTORIAL_NOT_READY`。

前端：`/practice` 底部「前往示例图」进入 `/practice/examples`，进入后 POST + 轮询 GET；示例图每步同样有「看视频」按钮。

### 6.8 开发捷径：跳过照片与解析

```http
POST /api/v1/makeup/dev/skip-to-preview
```

响应：`{ "taskId": "...", "status": "completed", "parseRunDir": "...", "previewRunDir": "..." }`。需服务端开启 `ENABLE_DEV_SHORTCUTS`；固定路径来自仓库根目录 `configs/dev-pinned-runs.json`（由 `scripts/pin-latest-dev-runs.py` 生成）。首页在开发模式下展示「跳过前两步（开发）」按钮。开发捷径会将仓库根目录 `示例视频1.mp4` 复制到任务 `upload/video.mp4`，供 tutorial / step-diagrams 的 `videoUrl` 与「看视频」时间跳转使用。

### 6.9 保存微调条件并优化教程（已接入真实管线）

```http
POST /api/v1/makeup/tasks/{taskId}/adjustment
Content-Type: application/json
```

请求体对应 `AdjustmentRequest`（`styles` / `occasions` / `retainedParts` / `concerns` / `constraints` 为多选数组，`skinType` 为单选，可选 `baseTutorialId`）。

行为：

1. 调用 `makeup-visual-optimization`，按问卷改写 `tutorial.json` 的 `instruction` / `visual_layer` / `adaptation_note`。
2. 写入 `optimized_tutorial_path`；后续 `GET …/tutorial` 与 `step-diagrams` **优先**读取优化版。
3. 重置 `step_diagrams_status` 为 `idle`，避免沿用旧示例图。
4. **不**重跑妆容预览 transfer。

成功响应示例：`{ "taskId", "status": "completed", "summary", "optimizedTutorialPath" }`。

前端：`/preview` → `/adjust` 有 `sessionStorage.makeupTask.taskId` 时调用本接口，成功后进入 `/practice`；用户再点「前往示例图」触发 `POST …/step-diagrams`，图示 prompt 会基于优化后的 tutorial 生成。混搭学习流（无 taskId）仍走本地 `LearningService` → `/tutorial`。

### 6.10 获取图示教程与眼部精讲（学习流 mock，待接入）

```http
GET /api/v1/makeup/tutorials/{tutorialId}
GET /api/v1/makeup/tutorials/{tutorialId}/eye-guides
```
### 6.11 查询知识库素材（待接入）

```http
GET /api/v1/makeup/library/assets?category=part&part=eyes
```

返回 `LibraryAsset[]`（含 `coverImage`、`tutorialId`）。`category` 允许 `tutorial` / `part` / `product`；混搭 `part` 允许 `base` / `eyes` / `blush` / `contour` / `lips`。知识库部位页可只展示眼妆/修容/唇妆卡位，但混搭素材范围不应因此删减。

### 6.12 匹配预制混搭效果（待接入）

```http
POST /api/v1/makeup/mixes
```

请求体为五个部位到素材 ID 的映射（跳过传 `null`），返回 `MixResult`（含妆前/妆后与 `tutorialId`）。不执行实时生成，只匹配预制结果。

`beforeImage` 和 `afterImage` 必须满足：

- 同一个人。
- 同一角度、裁切比例和图片尺寸。
- 人脸关键位置对齐。
- 浏览器允许前端域名访问图片；若跨域，CDN 需正确设置 CORS。
- 推荐 WebP 或 AVIF，并返回稳定的宽高，避免滑动对比时错位。
- 当 run 中存在展示裁切对时，后端应优先返回同尺寸的 `target_display.jpg`（妆前）与 `preview_display.jpg`（妆后）；否则回退 `target.jpg` / `preview_01.jpg`。
- 若无真实妆后生成文件，`afterImage` 必须为 `null`（`generationFailed: true`），**不得**用 `reference.jpg` 冒充 preview。

可选字段 `comparison`（对齐 run 由后端填充；有 display 裁切时用 `display_size`）：

```json
{
  "comparison": {
    "width": 780,
    "height": 780,
    "objectPosition": "50% 37.1%"
  }
}
```

前端用 `width`/`height` 设置对比容器宽高比，用 `objectPosition` 同时作用于妆前、妆后两张图（`object-fit: cover`）。无此字段时沿用固定高度布局。

## 7. 状态枚举

解析任务状态：

```ts
type AnalysisStatus = 'processing' | 'completed' | 'failed';
```

解析节点状态：

```ts
type AnalysisStageStatus = 'pending' | 'active' | 'completed';
```

适配提示语气：

```ts
type HintTone = 'positive' | 'adjust' | 'neutral';
```

后端不要返回未约定的自由状态字符串。新增状态前需要同步调整前端类型和页面表现。

## 8. 错误响应约定

建议后端统一返回：

```json
{
  "code": "VIDEO_FORMAT_UNSUPPORTED",
  "message": "仅支持 MP4 或 MOV 视频",
  "requestId": "req_01JXYZ",
  "details": null
}
```

建议状态码：

| HTTP 状态码 | 场景 |
|---|---|
| `400` | 参数缺失或状态不允许 |
| `401` | 未登录或凭证失效 |
| `403` | 无权访问该任务 |
| `404` | 任务不存在 |
| `409` | 任务状态冲突，例如重复启动解析 |
| `413` | 视频或照片超过大小限制 |
| `415` | 文件格式不支持 |
| `422` | 视频内容无法解析，例如人脸或步骤不清晰 |
| `429` | 请求过于频繁 |
| `500` | 服务端异常 |
| `503` | AI 解析服务暂时不可用 |

前端需要展示后端返回的可读 `message`，同时保留 `code` 和 `requestId` 供日志定位。不要将模型堆栈、存储路径或内部错误原样返回前端。

## 9. 鉴权与环境变量

建议前端环境变量：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

读取方式：

```ts
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
```

如果使用 Cookie 会话：

- 前端请求设置 `credentials: 'include'`。
- 后端 CORS 必须指定准确前端来源，不能与凭证模式一起使用 `*`。
- 生产环境 Cookie 使用 `HttpOnly`、`Secure` 和合适的 `SameSite`。

如果使用 Bearer Token：

- 统一在 HTTP 客户端封装中添加 `Authorization`。
- 页面组件不直接读取或拼接 Token。

## 10. 上传与隐私要求

- 视频前端限制 MP4、MOV，最大 500MB；后端必须再次校验 MIME、扩展名和真实文件内容。
- 照片属于敏感个人信息，存储、日志和访问控制需单独评审。
- 上传后的预览地址建议使用短期签名 URL 或受鉴权保护的资源地址。
- 后端应提供照片、预览结果和面部分析数据的删除能力。
- 日志中不要记录图片内容、完整签名 URL 或面部特征结果。
- 解析异步任务应与当前用户绑定，不能仅凭 `taskId` 越权读取。

## 11. 前端接入步骤

1. 通用 HTTP 客户端与 `HttpMakeupService`（已完成）。
2. 将视频上传、照片、解析轮询、适配预览接到真实任务结果（已完成）。
3. 跟练 `getTutorial` 与步骤示例图 `step-diagrams`（已完成）。
4. 真实管线微调 `POST …/adjustment` → `/practice`（已完成）；混搭学习流仍可后续接 `HttpLearningService`。
5. 刷新页面时根据 `taskId` 和 `tutorialId` 恢复服务端状态。
6. 添加接口错误、超时、鉴权失败和任务不存在的自动化测试。
7. 在联调环境验证大文件上传、慢网络和解析失败恢复。

## 12. 联调验收清单

- [ ] 上传有效 MP4/MOV 后返回稳定 `taskId`。
- [ ] 非法格式、超限文件能得到明确错误。
- [ ] 上传照片和跳过照片都能启动解析。
- [ ] 刷新解析页后能恢复真实任务进度。
- [ ] 完成态自动进入适配预览。
- [ ] 失败态显示具体原因并可重试。
- [ ] 妆前和妆后图片尺寸、角度完全对齐。
- [ ] 滑动对比可以看到两张完整图片。
- [ ] 适配页返回后直接进入视频上传页。
- [ ] 「适合我」进入跟练 `/practice`，并可打开步骤示例图。
- [ ] 「需要微调」提交问卷后进入 `/practice`；示例图使用优化后的 tutorial。
- [ ] 知识库分类、筛选与混搭预制流程可走通。
- [ ] 底部导航为首页 / 知识库 / 我的（不含跟练入口，但 `/practice` 路由仍可用）。
- [ ] 用户不能访问他人的任务、照片和预览结果。
- [ ] 前端测试、构建和 lint 全部通过。

## 13. 关键文件索引

```text
src/App.tsx                         路由入口
src/types/makeup.ts                解析/跟练管线契约
src/services/makeupService.ts      MakeupService 导出入口
src/services/httpMakeupService.ts  HTTP 实现
src/types/learning.ts              学习/知识库/混搭契约
src/services/learningService.ts    学习流程 mock 及替换入口
src/pages/UploadPage.tsx           视频上传
src/pages/PhotoPage.tsx            照片确认
src/pages/ParsingPage.tsx          解析进度
src/pages/PreviewPage.tsx          适配预览
src/pages/PracticePage.tsx         跟练（tutorial.json）
src/pages/StepDiagramsPage.tsx     步骤示例图
src/pages/AdjustPage.tsx           微调问卷
src/pages/TutorialPage.tsx         图示教程
src/pages/EyeGuidePage.tsx         眼部精讲
src/pages/LibraryPage.tsx          知识库
src/components/MixEditor.tsx       混搭编辑器
src/pages/MixGeneratingPage.tsx    混搭生成中
src/pages/MixPreviewPage.tsx       混搭预览
src/pages/ProfilePage.tsx          我的
src/components/BeforeAfterSlider.tsx
```
