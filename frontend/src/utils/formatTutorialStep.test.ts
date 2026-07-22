import { describe, expect, it } from 'vitest';
import type { Tutorial, TutorialStep } from '../types/makeup';
import {
  formatProductLine,
  formatRangeText,
  formatTechnique,
  groupHeading,
  resolveTutorialGroups,
  stepHeading,
} from './formatTutorialStep';

const baseStep: TutorialStep = {
  step_id: 'blush_01',
  part: 'cheek',
  product: { name: '橘朵腮红01', keywords: ['膨胀色腮红'] },
  visual_layer: { position: '颧骨外侧至太阳穴' },
  instruction: '少量多次轻拍晕染',
  adaptation_note: '',
  video_clip: { start: 0, end: 10 },
};

describe('formatProductLine', () => {
  it('prefers display_product single field', () => {
    expect(
      formatProductLine({
        ...baseStep,
        display_product: '珂岸面部素颜霜',
        display_product_tier: 'specific',
      }),
    ).toBe('珂岸面部素颜霜');
  });

  it('uses product name when no display_product', () => {
    expect(formatProductLine({ ...baseStep, taxonomy_primary: '腮红' })).toBe('橘朵腮红01');
  });

  it('falls back to category instead of 无>霜>底妆 chain', () => {
    expect(
      formatProductLine({
        ...baseStep,
        taxonomy_primary: '底妆',
        part: 'base',
        product: { name: 'unknown', keywords: ['霜'] },
      }),
    ).toBe('底妆');
  });
});

describe('formatRangeText', () => {
  it('returns 无 when step has no range info', () => {
    expect(formatRangeText({ ...baseStep, visual_layer: {} })).toBe('无');
  });

  it('prefers display_range over visual_layer fields', () => {
    expect(
      formatRangeText({
        ...baseStep,
        display_range: '全唇薄涂打底，呈内深外浅豆沙粉渐变',
        visual_layer: {
          position: '全唇薄涂',
          shape: 'gradient_inner_dark_outer_light',
          color: '#9E6B6B',
        },
      }),
    ).toBe('全唇薄涂打底，呈内深外浅豆沙粉渐变');
  });

  it('falls back to position only without raw shape or color', () => {
    expect(
      formatRangeText({
        ...baseStep,
        visual_layer: {
          position: '眼下',
          shape: 'diffuse',
          color: '#d8aaa0',
        },
      }),
    ).toBe('眼下');
  });
});

describe('formatTechnique', () => {
  it('prefers technique over long instruction', () => {
    expect(
      formatTechnique({
        ...baseStep,
        technique: '全脸推开',
        instruction: '很长的口播……',
      }),
    ).toBe('全脸推开');
  });

  it('returns instruction or 无', () => {
    expect(formatTechnique(baseStep)).toBe('少量多次轻拍晕染');
    expect(formatTechnique({ ...baseStep, instruction: '' })).toBe('无');
  });
});

describe('stepHeading', () => {
  it('prefers display_title', () => {
    expect(
      stepHeading({ ...baseStep, taxonomy_primary: '修容', display_title: '修容 · 鼻头两侧' }, 0),
    ).toBe('步骤 1 · 修容 · 鼻头两侧');
  });
});

describe('resolveTutorialGroups', () => {
  it('uses step_groups when present', () => {
    const tutorial: Tutorial = {
      contract_version: 'tutorial.v1',
      tutorial_id: 't1',
      title: 'demo',
      step_groups: [
        { group_id: 'group_01', title: '修容', index: 1, step_ids: ['contour_01', 'contour_02'] },
      ],
      steps: [
        {
          ...baseStep,
          step_id: 'contour_01',
          part: 'contour',
          taxonomy_primary: '修容',
          display_title: '修容 · 鼻头两侧',
        },
        {
          ...baseStep,
          step_id: 'contour_02',
          part: 'contour',
          taxonomy_primary: '修容',
          display_title: '修容 · 颧骨下方',
        },
      ],
    };
    const resolved = resolveTutorialGroups(tutorial);
    expect(resolved).toHaveLength(1);
    expect(groupHeading(resolved[0].group)).toBe('步骤 1 · 修容');
    expect(resolved[0].steps).toHaveLength(2);
  });

  it('falls back to one group per step', () => {
    const tutorial: Tutorial = {
      contract_version: 'tutorial.v1',
      tutorial_id: 't1',
      title: 'demo',
      steps: [{ ...baseStep, taxonomy_primary: '腮红' }],
    };
    const resolved = resolveTutorialGroups(tutorial);
    expect(resolved).toHaveLength(1);
    expect(groupHeading(resolved[0].group)).toBe('步骤 1 · 腮红');
  });
});
