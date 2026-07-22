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
  hasEyeGuide?: boolean;
}

export interface IllustratedTutorial {
  id: string;
  title: string;
  difficulty: string;
  duration: string;
  mode: TutorialMode;
  steps: TutorialStep[];
}

export interface EyeRegionGuide {
  id: string;
  label: string;
  description: string;
  adaptation: string;
  color: string;
  videoSlice: string;
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

export interface LibraryFilter {
  query?: string;
  category?: AssetCategory;
  placement?: 'library' | 'mix';
  part?: MakeupPart;
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

export interface LearningService {
  saveAdjustment(request: AdjustmentRequest): Promise<IllustratedTutorial>;
  getTutorial(tutorialId?: string): Promise<IllustratedTutorial>;
  getEyeGuides(tutorialId?: string): Promise<EyeRegionGuide[]>;
  listAssets(filter: LibraryFilter): Promise<LibraryAsset[]>;
  checkCompatibility(selection: MixSelection): Promise<CompatibilityHint[]>;
  generateMix(decision: MixDecision): Promise<MixResult>;
  getMixResult(resultId?: string): Promise<MixResult | null>;
}
