import { describe, expect, it } from 'vitest';
import type { TutorialStep } from '../types/makeup';
import { formatProductLine, formatRangeText, formatTechnique } from './formatTutorialStep';

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
  it('returns 无 when visual layer is empty', () => {
    expect(formatRangeText({})).toBe('无');
  });

  it('combines position shape and color', () => {
    expect(
      formatRangeText({
        position: '眼下',
        shape: 'diffuse',
        color: '#d8aaa0',
      }),
    ).toBe('眼下 · diffuse · #d8aaa0');
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
