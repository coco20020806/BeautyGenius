import type { Tutorial } from './makeup';

export type TutorialMode = 'beginner' | 'skilled';
export type AssetCategory = 'tutorial' | 'part' | 'product';
export type MakeupPart = 'base' | 'brows' | 'eyes' | 'blush' | 'contour' | 'highlight' | 'lips';

export interface AdjustmentRequest {
  styles: string[];
  occasions: string[];
  retainedParts: string[];
  skinType: string;
  concerns: string[];
  constraints: string[];
  baseTutorialId?: string;
}

export interface TutorialStep {
  id: string;
  order: number;
  title: string;
  part: MakeupPart;
  product: string;
  color: string;
  instruction: string;
  expertTip: string;
  videoSlice: string;
  diagramImage?: string;
}

export interface IllustratedTutorial {
  id: string;
  title: string;
  difficulty: string;
  duration: string;
  mode: TutorialMode;
  steps: TutorialStep[];
  /** Full original source video URL when available (e.g. knowledge-base part presets). */
  videoUrl?: string;
}

export interface LibraryAsset {
  id: string;
  title: string;
  category: AssetCategory;
  part?: MakeupPart;
  source: string;
  style: string;
  occasion: string;
  difficulty: string;
  color: string;
  practiced: boolean;
  coverImage: string;
  tutorialId: string;
}

export type LibraryPartFilter = MakeupPart | 'full-face';

export interface LibraryFilter {
  query?: string;
  category?: AssetCategory;
  placement?: 'library' | 'mix';
  part?: LibraryPartFilter;
  style?: string;
  occasion?: string;
  difficulty?: string;
}

export type MixSelection = Partial<Record<MakeupPart, string>>;
export type MixPart = 'base' | 'eyes' | 'blush' | 'contour' | 'lips';
export type MixDecision = Record<MixPart, string | null>;

export interface MixResult {
  id: string;
  beforeImage: string;
  afterImage: string;
  title: string;
  summary: string;
  tutorialId: string;
}

export interface CompatibilityHint {
  type: 'compatible' | 'style-conflict' | 'difficulty' | 'color-conflict';
  message: string;
  suggestion: string;
}

export interface CollectedSampleHint {
  title: string;
  description: string;
  tone: 'positive' | 'adjust' | 'neutral';
}

export interface CollectedSampleComparison {
  width: number;
  height: number;
  objectPosition?: string;
}

export interface CollectedSampleDetail {
  id: string;
  title: string;
  previewTitle: string;
  style: string;
  occasion: string;
  difficulty: string;
  duration: string;
  hints: CollectedSampleHint[];
  /** 跟练步骤（产品 / 范围 / 手法），对齐 PracticePage */
  practiceTutorial: Tutorial;
  illustratedSteps: TutorialStep[];
  beforeImage?: string;
  afterImage?: string;
  comparison?: CollectedSampleComparison;
}

export interface LearningService {
  saveAdjustment(request: AdjustmentRequest): Promise<IllustratedTutorial>;
  getTutorial(tutorialId?: string): Promise<IllustratedTutorial>;
  listAssets(filter: LibraryFilter): Promise<LibraryAsset[]>;
  getCollectedSample(assetId: string): Promise<CollectedSampleDetail | null>;
  checkCompatibility(selection: MixSelection): Promise<CompatibilityHint[]>;
  generateMix(decision: MixDecision): Promise<MixResult>;
  getMixResult(resultId?: string): Promise<MixResult | null>;
}
