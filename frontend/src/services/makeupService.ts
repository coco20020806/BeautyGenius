import type {
  AdjustmentRequest,
  AdjustmentResult,
  AnalysisProgress,
  AnalysisStage,
  MakeupPreview,
  MakeupService,
  Tutorial,
  UploadPhotoResult,
  UploadVideoResult,
} from '../types/makeup';
import faceAfter from '../assets/face-after.svg';
import faceBefore from '../assets/face-before.svg';
import { HttpMakeupService } from './httpMakeupService';
import { HttpError, requestJson } from './httpClient';

const MAX_VIDEO_SIZE = 500 * 1024 * 1024;
const VIDEO_TYPES = new Set(['video/mp4', 'video/quicktime']);
const STAGE_LABELS = ['检查视频质量', '识别妆容步骤', '生成适配预览', '整理关键建议'];

function makeStages(activeIndex: number): AnalysisStage[] {
  return STAGE_LABELS.map((label, index) => ({
    id: `stage-${index + 1}`,
    label,
    status: index < activeIndex ? 'completed' : index === activeIndex ? 'active' : 'pending',
  }));
}

async function tick() {
  await new Promise((resolve) => window.setTimeout(resolve, 20));
}

class LocalMakeupService implements MakeupService {
  async uploadVideo(
    file: File,
    options?: { fastParse?: boolean; skipMakeupPreview?: boolean },
  ): Promise<UploadVideoResult> {
    if (!VIDEO_TYPES.has(file.type)) {
      throw new Error('仅支持 MP4 或 MOV 视频');
    }
    if (file.size > MAX_VIDEO_SIZE) {
      throw new Error('视频不能超过 500MB');
    }

    const fast = options?.fastParse !== false;
    return {
      taskId: `task-${Date.now()}`,
      fileName: file.name,
      fileSize: file.size,
      status: 'uploaded',
      parseMode: fast ? 'fast' : 'full',
      skipMakeupPreview: Boolean(options?.skipMakeupPreview),
    };
  }

  async uploadPhoto(file: File | null): Promise<UploadPhotoResult> {
    if (!file) return { photoId: null, previewUrl: null, skipped: true };
    if (!file.type.startsWith('image/')) throw new Error('请选择 JPG、PNG 或 WebP 照片');

    return {
      photoId: `photo-${Date.now()}`,
      previewUrl: URL.createObjectURL(file),
      skipped: false,
    };
  }

  async *analyze(taskId: string): AsyncGenerator<AnalysisProgress> {
    const mockLogs = [
      '[job] parse mode=fast（L2 关键帧 QA=关）',
      '[1/10] Probe…',
      '[4/10] Vision 分析中…（并行）',
      '[map 2/6] 确定性映射…',
      '[job] 妆容预览（选帧/底图/transfer）…',
      '[job] 完成',
    ];
    const checkpoints = [18, 45, 72, 100];
    for (let index = 0; index < checkpoints.length; index += 1) {
      await tick();
      const completed = index === checkpoints.length - 1;
      const logLines = mockLogs.slice(0, Math.min(mockLogs.length, index + 2));
      yield {
        taskId,
        progress: checkpoints[index],
        currentStage: STAGE_LABELS[index],
        remainingSeconds: completed ? 0 : (checkpoints.length - index - 1) * 45,
        status: completed ? 'completed' : 'processing',
        stages: makeStages(completed ? checkpoints.length : index),
        detailMessage: logLines[logLines.length - 1],
        logLines,
      };
    }
  }

  async getTutorial(taskId: string): Promise<Tutorial> {
    return {
      contract_version: 'tutorial.v1',
      tutorial_id: `tutorial_${taskId}`,
      title: '清透玫瑰通勤妆',
      videoUrl: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4',
      step_groups: [
        { group_id: 'group_01', title: '底妆', index: 1, step_ids: ['base_01'] },
        { group_id: 'group_02', title: '腮红', index: 2, step_ids: ['blush_01'] },
        { group_id: 'group_03', title: '唇妆', index: 3, step_ids: ['lip_01'] },
      ],
      steps: [
        {
          step_id: 'base_01',
          part: 'base',
          taxonomy_primary: '底妆',
          display_title: '底妆',
          display_group_id: 'group_01',
          product: { name: '珂岸面部素颜霜', keywords: ['素颜霜'] },
          display_product: '珂岸面部素颜霜',
          display_product_tier: 'specific',
          technique: '全脸推开',
          display_range: '全脸均匀薄涂，边缘自然过渡',
          visual_layer: { position: '全脸均匀铺开' },
          instruction: '从面中向外拍开，边缘少量带过',
          adaptation_note: '',
          video_clip: { start: 0, end: 45 },
        },
        {
          step_id: 'blush_01',
          part: 'cheek',
          taxonomy_primary: '腮红',
          display_title: '腮红',
          display_group_id: 'group_02',
          product: { name: '橘朵腮红01', keywords: ['膨胀色腮红'] },
          display_product: '橘朵腮红01',
          display_product_tier: 'specific',
          technique: '少量轻拍晕染',
          display_range: '颧骨外侧至太阳穴，柔和晕染偏杏色',
          visual_layer: { position: '颧骨外侧至太阳穴', color: '#d8aaa0' },
          instruction: '少量多次轻拍晕染，与底妆自然衔接',
          adaptation_note: '',
          video_clip: { start: 45, end: 90 },
        },
        {
          step_id: 'lip_01',
          part: 'lip',
          taxonomy_primary: '唇妆',
          display_title: '唇妆',
          display_group_id: 'group_03',
          product: { name: 'unknown', keywords: ['低饱和玫瑰色'] },
          display_product: '低饱和玫瑰色',
          display_product_tier: 'characteristic',
          technique: '薄涂指腹拍开',
          display_range: '唇峰与唇中薄涂，边缘轻柔拍开',
          visual_layer: { position: '唇峰与唇中' },
          instruction: '薄涂一层，指腹轻拍开边缘',
          adaptation_note: '',
          video_clip: { start: 90, end: 120 },
        },
      ],
    };
  }

  async saveAdjustment(taskId: string, request: AdjustmentRequest): Promise<AdjustmentResult> {
    return {
      taskId,
      status: 'completed',
      summary: {
        primary_goal: request.concerns[0] || request.styles[0] || '个性化微调',
        retained_modules: request.retainedParts,
        confidence: 'high',
      },
    };
  }

  async skipToDevPreview() {
    return { taskId: 'demo-task', status: 'completed' as const };
  }

  async getServerStatus() {
    return { busy: false, activeCount: 0, maxConcurrent: 2 };
  }

  async startStepDiagrams(taskId: string) {
    return { taskId, status: 'completed' as const };
  }

  async getStepDiagrams(taskId: string) {
    const tutorial = await this.getTutorial(taskId);
    return {
      taskId,
      status: 'completed' as const,
      videoUrl: tutorial.videoUrl,
      steps: tutorial.steps.map((step, index) => {
        const basePrompt =
          `${step.instruction || '按步骤上妆'}，请在原始图片上用色块标注着色范围`;
        const finalPrompt =
          `${basePrompt}画面中可见对应部位操作痕迹，范围边界柔和。`;
        return {
          stepId: step.step_id,
          index,
          heading: `步骤 ${index + 1} · ${step.display_title ?? step.taxonomy_primary ?? step.step_id}`,
          imageUrl: faceBefore,
          status: 'ok' as const,
          videoClip: step.video_clip,
          basePrompt,
          finalPrompt,
        };
      }),
    };
  }

  async getPreview(taskId: string): Promise<MakeupPreview> {
    return {
      taskId,
      title: '清透玫瑰通勤妆',
      style: '清透自然',
      occasion: '通勤 · 日常',
      difficulty: '新手友好',
      duration: '约 1 分钟',
      beforeImage: faceBefore,
      afterImage: faceAfter,
      generationFailed: false,
      palette: ['#ead6cf', '#d8aaa0', '#b87870', '#8e554f', '#5c3a36'],
      intensityLevels: [
        { id: 'L1', color: '#ead6cf', opacity: 0.2 },
        { id: 'L2', color: '#d8aaa0', opacity: 0.4 },
        { id: 'L3', color: '#b87870', opacity: 0.6 },
        { id: 'L4', color: '#8e554f', opacity: 0.8 },
        { id: 'L5', color: '#5c3a36', opacity: 1.0 },
      ],
      hints: [
        { title: '适合你的眼型', description: '眼尾轻微上扬能保持利落，也不会显得过浓。', tone: 'positive' },
        { title: '腮红建议上移', description: '将范围收在眼下到颧骨外侧，更显轻盈。', tone: 'adjust' },
        { title: '唇色协调', description: '低饱和玫瑰色与整体妆面自然衔接。', tone: 'neutral' },
      ],
    };
  }
}

const useMock = import.meta.env.VITE_USE_MOCK === '1';

export const makeupService: MakeupService = useMock
  ? new LocalMakeupService()
  : new HttpMakeupService();

export async function collectAnalysis(source: AsyncGenerator<AnalysisProgress>) {
  const states: AnalysisProgress[] = [];
  for await (const state of source) states.push(state);
  return states;
}

export async function fetchAnalysisSnapshot(taskId: string): Promise<AnalysisProgress | null> {
  if (useMock) return null;
  try {
    return await requestJson<AnalysisProgress>(`/api/v1/makeup/tasks/${taskId}/analysis`);
  } catch {
    return null;
  }
}

export function isServerBusyError(error: unknown): boolean {
  return error instanceof HttpError && error.code === 'SERVER_BUSY';
}

export function isPreemptedError(error: unknown): boolean {
  return error instanceof HttpError && error.code === 'PREEMPTED_BY_VIP';
}
