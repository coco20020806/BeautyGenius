import { describe, expect, test } from 'vitest';
import { splitDiagramPrompt } from './splitDiagramPrompt';

describe('splitDiagramPrompt', () => {
  test('splits set-powder example into technique and annotation', () => {
    const full =
      '使用定妆产品，用粉扑或刷子轻轻按压定妆眼下、鼻部、嘴角及下巴等容易出油脱妆的部位，使妆容更持久服帖。请在原始图片上用色块标注作用区域画面中模特手持粉扑，正在对唇周、眼下及鼻部进行按压定妆，脸颊可见粉色腮红色块，粉扑边缘有轻微按压痕迹。';

    const { technique, annotation } = splitDiagramPrompt(full);

    expect(technique).toBe(
      '使用定妆产品，用粉扑或刷子轻轻按压定妆眼下、鼻部、嘴角及下巴等容易出油脱妆的部位，使妆容更持久服帖。',
    );
    expect(technique).not.toContain('请在原始图片上');
    expect(annotation).toMatch(/^请在原始图片上用色块标注作用区域/);
    expect(annotation).toContain('画面中模特手持粉扑');
  });

  test('returns whole text as technique when marker missing', () => {
    const { technique, annotation } = splitDiagramPrompt('少量多次轻扫腮红');
    expect(technique).toBe('少量多次轻扫腮红');
    expect(annotation).toBeNull();
  });
});
