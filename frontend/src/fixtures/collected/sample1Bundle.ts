import type { CollectedSampleDetail, MakeupPart, TutorialStep } from '../../types/learning';
import type { Tutorial } from '../../types/makeup';
import detailJson from './sample-1/detail.json';
import tutorialJson from './sample-1/tutorial.json';
import beforeImage from './sample-1/media/target_display.jpg';
import afterImage from './sample-1/media/preview_display.jpg';
import coverImage from './sample-1/media/preview_display.jpg';
import diagramPrep01 from './sample-1/media/diagram_prep_01.jpg';
import diagramBase01 from './sample-1/media/diagram_base_01.jpg';
import diagramSet01 from './sample-1/media/diagram_set_01.jpg';
import diagramEye01 from './sample-1/media/diagram_eye_01.jpg';
import diagramContour01 from './sample-1/media/diagram_contour_01.jpg';
import diagramEye02 from './sample-1/media/diagram_eye_02.jpg';
import diagramBrow01 from './sample-1/media/diagram_brow_01.jpg';
import diagramBlush01 from './sample-1/media/diagram_blush_01.jpg';
import diagramLip01 from './sample-1/media/diagram_lip_01.jpg';

const DIAGRAM_BY_STEP: Record<string, string> = {
  prep_01: diagramPrep01,
  base_01: diagramBase01,
  set_01: diagramSet01,
  eye_01: diagramEye01,
  contour_01: diagramContour01,
  eye_02: diagramEye02,
  brow_01: diagramBrow01,
  blush_01: diagramBlush01,
  lip_01: diagramLip01,
};

function asMakeupPart(value: string): MakeupPart {
  const allowed: MakeupPart[] = ['base', 'brows', 'eyes', 'blush', 'contour', 'highlight', 'lips'];
  return (allowed.includes(value as MakeupPart) ? value : 'base') as MakeupPart;
}

const illustratedSteps: TutorialStep[] = detailJson.illustratedSteps.map((step) => ({
  id: step.id,
  order: step.order,
  title: step.title,
  part: asMakeupPart(step.part),
  product: step.product,
  color: step.color,
  instruction: step.instruction,
  expertTip: step.expertTip,
  videoSlice: step.videoSlice,
  diagramImage: DIAGRAM_BY_STEP[step.id] ?? '',
}));

const practiceTutorial: Tutorial = {
  ...(tutorialJson as Tutorial),
  videoUrl: '/fixtures/collected/sample-1.mp4',
};

export const sample1CoverImage = coverImage;

export const sample1CollectedDetail: CollectedSampleDetail = {
  id: detailJson.id,
  title: detailJson.title,
  previewTitle: detailJson.previewTitle,
  style: detailJson.style,
  occasion: detailJson.occasion,
  difficulty: detailJson.difficulty,
  duration: detailJson.duration,
  hints: detailJson.hints.map((hint) => ({
    title: hint.title,
    description: hint.description,
    tone: hint.tone as CollectedSampleDetail['hints'][number]['tone'],
  })),
  practiceTutorial,
  illustratedSteps,
  beforeImage,
  afterImage,
  comparison: {
    width: detailJson.comparison.width,
    height: detailJson.comparison.height,
    ...(detailJson.comparison.objectPosition
      ? { objectPosition: detailJson.comparison.objectPosition }
      : {}),
  },
};
