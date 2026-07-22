export type AnalysisStatus = 'processing' | 'completed' | 'failed';
export type AnalysisStageStatus = 'pending' | 'active' | 'completed';

export interface UploadVideoResult {
  taskId: string;
  fileName: string;
  fileSize: number;
  status: 'uploaded';
  parseMode?: 'fast' | 'full';
  skipMakeupPreview?: boolean;
}

export interface UploadPhotoResult {
  photoId: string | null;
  previewUrl: string | null;
  skipped: boolean;
}

export interface AnalysisStage {
  id: string;
  label: string;
  status: AnalysisStageStatus;
}

export interface AnalysisProgress {
  taskId: string;
  progress: number;
  currentStage: string;
  remainingSeconds: number;
  status: AnalysisStatus;
  stages: AnalysisStage[];
  failureReason?: string;
  detailMessage?: string;
  logLines?: string[];
  etaTotalSeconds?: number;
  completedWeight?: number;
}

export interface MakeupPreviewComparison {
  width: number;
  height: number;
  objectPosition?: string;
}

export interface MakeupIntensityLevel {
  id: string;
  color: string;
  opacity: number;
}

export interface MakeupPreview {
  taskId: string;
  title: string;
  style: string;
  occasion: string;
  difficulty: string;
  duration: string;
  beforeImage: string;
  afterImage: string;
  palette: string[];
  /** 妆浓淡色块；缺省时前端用固定 5 档 */
  intensityLevels?: MakeupIntensityLevel[];
  hints: Array<{ title: string; description: string; tone: 'positive' | 'adjust' | 'neutral' }>;
  comparison?: MakeupPreviewComparison;
}

export type TutorialPart =
  | 'prep'
  | 'base'
  | 'concealer'
  | 'set'
  | 'brow'
  | 'eye'
  | 'contour'
  | 'highlight'
  | 'cheek'
  | 'lip'
  | 'other';

export interface TutorialProduct {
  name: string;
  keywords: string[];
  description?: string;
}

export interface TutorialVisualLayer {
  shape?: string;
  color?: string;
  opacity?: number;
  position?: string;
}

export interface TutorialStep {
  step_id: string;
  part: TutorialPart;
  taxonomy_primary?: string;
  taxonomy_sub_steps?: string[];
  product: TutorialProduct;
  visual_layer: TutorialVisualLayer;
  instruction: string;
  adaptation_note: string;
  video_clip: { start: number; end: number };
  display_title?: string;
  display_group_id?: string;
  display_product?: string;
  display_product_tier?: 'specific' | 'characteristic' | 'category' | 'none';
  technique?: string;
}

export interface TutorialStepGroup {
  group_id: string;
  title: string;
  index: number;
  step_ids: string[];
}

export interface Tutorial {
  contract_version: string;
  tutorial_id: string;
  title: string;
  steps: TutorialStep[];
  step_groups?: TutorialStepGroup[];
  /** 上传原片的公开播放地址（API 追加，不在磁盘 tutorial.json 内） */
  videoUrl?: string;
}

export interface DevSkipPreviewResult {
  taskId: string;
  status: 'completed';
  parseRunDir?: string;
  previewRunDir?: string;
}

export interface MakeupService {
  uploadVideo(file: File, options?: { fastParse?: boolean; skipMakeupPreview?: boolean }): Promise<UploadVideoResult>;
  uploadPhoto(file: File | null): Promise<UploadPhotoResult>;
  analyze(taskId: string): AsyncGenerator<AnalysisProgress>;
  getPreview(taskId: string): Promise<MakeupPreview>;
  getTutorial(taskId: string): Promise<Tutorial>;
  startStepDiagrams(taskId: string): Promise<StepDiagramsStartResult>;
  getStepDiagrams(taskId: string): Promise<StepDiagramsResponse>;
  skipToDevPreview(): Promise<DevSkipPreviewResult>;
}

export type StepDiagramItemStatus = 'pending' | 'ok' | 'failed' | 'skipped';

export interface StepDiagramItem {
  stepId: string;
  index: number;
  heading: string;
  imageUrl: string | null;
  status: StepDiagramItemStatus;
  finalPrompt?: string;
  /** qwen 第 1 阶段 base_prompt，用于截取化妆手法句 */
  basePrompt?: string;
  /** 单步生成失败时的错误信息（来自 picture-makeup manifest） */
  error?: string;
  videoClip?: { start: number; end: number };
}

export type StepDiagramsJobStatus = 'idle' | 'processing' | 'completed' | 'failed';

export interface StepDiagramsResponse {
  taskId: string;
  status: StepDiagramsJobStatus;
  progress?: { done: number; total: number; currentStepId?: string };
  steps: StepDiagramItem[];
  failureReason?: string;
  videoUrl?: string;
}

export interface StepDiagramsStartResult {
  taskId: string;
  status: 'processing' | 'completed';
}
