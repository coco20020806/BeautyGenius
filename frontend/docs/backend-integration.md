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

| 路由 | 页面文件 | 用途 | 是否需要后端 |
|---|---|---|---|
| `/` | `src/pages/UploadPage.tsx` | 选择并上传教程视频 | 是 |
| `/photo` | `src/pages/PhotoPage.tsx` | 上传本人照片或跳过 | 是 |
| `/parsing` | `src/pages/ParsingPage.tsx` | 展示解析进度和失败信息 | 是 |
| `/preview` | `src/pages/PreviewPage.tsx` | 展示妆前/妆后效果与适配建议 | 是 |
| `/practice` | `src/pages/PracticePage.tsx` | 展示 tutorial.json 步骤（产品/范围/手法） | 是 |
| `/practice/examples` | `src/pages/StepDiagramsPage.tsx` | 步骤着色范围示例图（按需生成） | 是 |
| `/library` | `src/pages/PlaceholderPage.tsx` | 知识库占位页 | 暂不需要 |
| `/profile` | `src/pages/PlaceholderPage.tsx` | 我的占位页 | 暂不需要 |

核心流程：

```text
上传视频 / → 照片确认 /photo → 解析进度 /parsing → 适配预览 /preview → 适合我 → 跟练 /practice → 示例图 /practice/examples（按需生成）
```

适配预览页的返回按钮会直接进入 `/`，不会重新进入解析页。

## 4. 前端代码边界

### 4.1 类型契约

所有业务类型集中在：

```text
src/types/makeup.ts
```

后端返回结构应尽量与这些接口保持一致。若接口字段需要调整，应先修改此文件，再由 TypeScript 提示所有受影响页面。

### 4.2 服务接口

前端统一通过 `MakeupService` 调用业务能力：

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

当前模拟实现位于：

```text
src/services/makeupService.ts
```

后端接入建议新建：

```text
src/services/httpMakeupService.ts
```

新服务继续实现 `MakeupService`，然后将导出的 `makeupService` 从本地模拟实现切换为 HTTP 实现。页面组件不应直接写 `fetch`、接口域名或鉴权头。

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
  "duration": "约 18 分钟",
  "beforeImage": "https://cdn.example.com/tasks/task_01JXYZ/before.webp",
  "afterImage": "https://cdn.example.com/tasks/task_01JXYZ/after.webp",
  "palette": ["#ead6cf", "#d8aaa0", "#b87870", "#8e554f", "#f2e5dd"],
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

`beforeImage` 和 `afterImage` 必须满足：

- 同一个人。
- 同一角度、裁切比例和图片尺寸。
- 人脸关键位置对齐。
- 浏览器允许前端域名访问图片；若跨域，CDN 需正确设置 CORS。
- 推荐 WebP 或 AVIF，并返回稳定的宽高，避免滑动对比时错位。
- 当 run 中存在展示裁切对时，后端应优先返回同尺寸的 `target_display.jpg`（妆前）与 `preview_display.jpg`（妆后）；否则回退 `target.jpg` / `preview_01.jpg`。

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

1. 新建通用 HTTP 客户端，处理基础地址、JSON 解析、超时和统一错误。
2. 新建 `HttpMakeupService` 并实现 `MakeupService`。
3. 将视频上传切换到 `POST /tasks`。
4. 修改照片页，在确认或跳过时调用照片接口。
5. 将 `analyze()` 替换为轮询或 SSE 实现。
6. 将适配预览切换到真实任务结果。
7. 刷新页面时根据 `taskId` 恢复服务端任务状态。
8. 添加接口错误、超时、鉴权失败和任务不存在的自动化测试。
9. 在联调环境验证大文件上传、慢网络和解析失败恢复。

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
- [ ] 用户不能访问他人的任务、照片和预览结果。
- [ ] 前端测试、构建和 lint 全部通过。

## 13. 关键文件索引

```text
src/App.tsx                         路由入口
src/types/makeup.ts                前后端数据契约
src/services/makeupService.ts      当前模拟服务及替换入口
src/pages/UploadPage.tsx           视频上传调用方
src/pages/PhotoPage.tsx            照片确认与跳过逻辑
src/pages/ParsingPage.tsx          解析进度消费方
src/pages/PreviewPage.tsx          适配结果消费方
src/components/BeforeAfterSlider.tsx 妆前/妆后滑动组件
```
