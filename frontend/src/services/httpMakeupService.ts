import type {
  AdjustmentRequest,
  AdjustmentResult,
  AnalysisProgress,
  MakeupPreview,
  MakeupService,
  StepDiagramsResponse,
  StepDiagramsStartResult,
  Tutorial,
  UploadPhotoResult,
  UploadVideoResult,
} from '../types/makeup';
import { delay, requestJson, requestMultipart } from './httpClient';

const API_PREFIX = '/api/v1/makeup';

export class HttpMakeupService implements MakeupService {
  async uploadVideo(
    file: File,
    options?: { fastParse?: boolean; skipMakeupPreview?: boolean },
  ): Promise<UploadVideoResult> {
    const form = new FormData();
    form.append('video', file);
    form.append('fastParse', options?.fastParse !== false ? 'true' : 'false');
    form.append('skipMakeupPreview', options?.skipMakeupPreview ? 'true' : 'false');
    return requestMultipart<UploadVideoResult>(`${API_PREFIX}/tasks`, form);
  }

  async uploadPhoto(file: File | null): Promise<UploadPhotoResult> {
    const taskId = readTaskId();
    if (!taskId) throw new Error('缺少任务 ID，请重新上传视频');
    const form = new FormData();
    if (file) form.append('photo', file);
    form.append('skipped', file ? 'false' : 'true');
    return requestMultipart<UploadPhotoResult>(`${API_PREFIX}/tasks/${taskId}/photo`, form);
  }

  async *analyze(taskId: string): AsyncGenerator<AnalysisProgress> {
    await requestJson<{ taskId: string; status: string }>(
      `${API_PREFIX}/tasks/${taskId}/analysis`,
      { method: 'POST' },
    );

    while (true) {
      const progress = await requestJson<AnalysisProgress>(
        `${API_PREFIX}/tasks/${taskId}/analysis`,
      );
      yield progress;
      if (progress.status === 'completed' || progress.status === 'failed') return;
      await delay(1500);
    }
  }

  async getPreview(taskId: string): Promise<MakeupPreview> {
    return requestJson<MakeupPreview>(`${API_PREFIX}/tasks/${taskId}/preview`);
  }

  async getTutorial(taskId: string): Promise<Tutorial> {
    return requestJson<Tutorial>(`${API_PREFIX}/tasks/${taskId}/tutorial`);
  }

  async saveAdjustment(taskId: string, request: AdjustmentRequest): Promise<AdjustmentResult> {
    return requestJson<AdjustmentResult>(`${API_PREFIX}/tasks/${taskId}/adjustment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
  }

  async startStepDiagrams(taskId: string): Promise<StepDiagramsStartResult> {
    return requestJson<StepDiagramsStartResult>(`${API_PREFIX}/tasks/${taskId}/step-diagrams`, {
      method: 'POST',
    });
  }

  async getStepDiagrams(taskId: string): Promise<StepDiagramsResponse> {
    return requestJson<StepDiagramsResponse>(`${API_PREFIX}/tasks/${taskId}/step-diagrams`);
  }

  async skipToDevPreview() {
    return requestJson<{ taskId: string; status: 'completed' }>(
      `${API_PREFIX}/dev/skip-to-preview`,
      { method: 'POST' },
    );
  }
}

function readTaskId(): string | null {
  try {
    const raw = sessionStorage.getItem('makeupTask');
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { taskId?: string };
    return parsed.taskId ?? null;
  } catch {
    return null;
  }
}
