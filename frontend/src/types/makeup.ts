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
  hints: Array<{ title: string; description: string; tone: 'positive' | 'adjust' | 'neutral' }>;
  comparison?: MakeupPreviewComparison;
}

export interface MakeupService {
  uploadVideo(file: File, options?: { fastParse?: boolean; skipMakeupPreview?: boolean }): Promise<UploadVideoResult>;
  uploadPhoto(file: File | null): Promise<UploadPhotoResult>;
  analyze(taskId: string): AsyncGenerator<AnalysisProgress>;
  getPreview(taskId: string): Promise<MakeupPreview>;
}
