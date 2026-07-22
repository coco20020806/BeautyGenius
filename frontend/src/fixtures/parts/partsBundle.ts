import type { IllustratedTutorial, MakeupPart } from '../../types/learning';
import eyesCover from './eyes/media/cover.png';
import eyesDiagram from './eyes/media/diagram.jpg';
import eyesVideo from './eyes/media/source.mp4?url';
import contourCover from './contour/media/cover.png';
import contourDiagram from './contour/media/diagram.png';
import contourVideo from './contour/media/source.mp4?url';
import lipsCover from './lips/media/cover.png';
import lipsDiagram from './lips/media/diagram.png';
import lipsVideo from './lips/media/source.mp4?url';

export const partCovers = {
  eyes: eyesCover,
  contour: contourCover,
  lips: lipsCover,
} as const;

type PartPreset = {
  tutorialId: string;
  title: string;
  part: MakeupPart;
  product: string;
  color: string;
  instruction: string;
  expertTip: string;
  diagramImage: string;
  /** Original source video from each part media folder (source.mp4). */
  videoUrl: string;
};

const PART_PRESETS: PartPreset[] = [
  {
    tutorialId: 'preset-eyes-rose',
    title: '清透玫瑰眼妆',
    part: 'eyes',
    product: '裸粉眼影',
    color: '#bd7b82',
    instruction: '从睫毛根部向上晕染，范围不超过眼窝，眼尾略加深即可。',
    expertTip: '先用浅色铺底，再叠深色过渡，避免硬边。',
    diagramImage: eyesDiagram,
    videoUrl: eyesVideo,
  },
  {
    tutorialId: 'preset-contour-soft',
    title: '柔和轮廓修容',
    part: 'contour',
    product: '暖棕修容粉',
    color: '#b18b7b',
    instruction: '沿颧骨下缘与发际轻扫，边缘用干净刷具晕开，保持轮廓柔和。',
    expertTip: '少量多次，避免在面中留下明显色块。',
    diagramImage: contourDiagram,
    videoUrl: contourVideo,
  },
  {
    tutorialId: 'preset-lips-rose',
    title: '低饱和玫瑰唇',
    part: 'lips',
    product: '低饱和玫瑰唇釉',
    color: '#a94f5b',
    instruction: '先薄涂全唇，再在唇中叠加一层，边缘用指腹柔化。',
    expertTip: '唇线不要过深，保持低饱和日常感。',
    diagramImage: lipsDiagram,
    videoUrl: lipsVideo,
  },
];

export function getPartPresetTutorial(tutorialId: string): IllustratedTutorial | null {
  const preset = PART_PRESETS.find((item) => item.tutorialId === tutorialId);
  if (!preset) return null;
  return {
    id: preset.tutorialId,
    title: preset.title,
    difficulty: '新手友好',
    duration: '约 5 分钟',
    mode: 'beginner',
    videoUrl: preset.videoUrl,
    steps: [
      {
        id: preset.part,
        order: 1,
        title: preset.title,
        part: preset.part,
        product: preset.product,
        color: preset.color,
        instruction: preset.instruction,
        expertTip: preset.expertTip,
        videoSlice: '完整原视频',
        diagramImage: preset.diagramImage,
        videoUrl: preset.videoUrl,
      },
    ],
  };
}
