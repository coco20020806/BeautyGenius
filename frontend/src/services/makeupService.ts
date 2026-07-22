import type {
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
import { requestJson } from './httpClient';

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
      steps: [
        {
          step_id: 'base_01',
          part: 'base',
          taxonomy_primary: '底妆',
          product: { name: '珂岸面部素颜霜', keywords: ['素颜霜'] },
          display_product: '珂岸面部素颜霜',
          display_product_tier: 'specific',
          technique: '全脸推开',
          visual_layer: { position: '全脸均匀铺开' },
          instruction: '从面中向外拍开，边缘少量带过',
          adaptation_note: '',
          video_clip: { start: 0, end: 45 },
        },
        {
          step_id: 'blush_01',
          part: 'cheek',
          taxonomy_primary: '腮红',
          product: { name: '橘朵腮红01', keywords: ['膨胀色腮红'] },
          display_product: '橘朵腮红01',
          display_product_tier: 'specific',
          technique: '少量轻拍晕染',
          visual_layer: { position: '颧骨外侧至太阳穴', color: '#d8aaa0' },
          instruction: '少量多次轻拍晕染，与底妆自然衔接',
          adaptation_note: '',
          video_clip: { start: 45, end: 90 },
        },
        {
          step_id: 'lip_01',
          part: 'lip',
          taxonomy_primary: '唇妆',
          product: { name: 'unknown', keywords: ['低饱和玫瑰色'] },
          display_product: '低饱和玫瑰色',
          display_product_tier: 'characteristic',
          technique: '薄涂指腹拍开',
          visual_layer: { position: '唇峰与唇中' },
          instruction: '薄涂一层，指腹轻拍开边缘',
          adaptation_note: '',
          video_clip: { start: 90, end: 120 },
        },
      ],
    };
  }

  async skipToDevPreview() {
    return { taskId: 'demo-task', status: 'completed' as const };
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
      steps: tutorial.steps.map((step, index) => ({
        stepId: step.step_id,
        index,
        heading: `步骤 ${index + 1} · ${step.taxonomy_primary ?? step.step_id}`,
        imageUrl: faceBefore,
        status: 'ok' as const,
        videoClip: step.video_clip,
      })),
    };
  }

  async getPreview(taskId: string): Promise<MakeupPreview> {
    return {
      taskId,
      title: '清透玫瑰通勤妆',
      style: '清透自然',
      occasion: '通勤 · 日常',
      difficulty: '新手友好',
      duration: '约 18 分钟',
      beforeImage: faceBefore,
      afterImage: faceAfter,
      palette: ['#ead6cf', '#d8aaa0', '#b87870', '#8e554f', '#f2e5dd'],
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
