import { learningService } from './learningService';

test('filters library assets by search and category', async () => {
  const assets = await learningService.listAssets({ query: '眼妆', category: 'part' });

  expect(assets.every((asset) => asset.category === 'part')).toBe(true);
  expect(assets.some((asset) => asset.title.includes('眼妆'))).toBe(true);
  expect(assets.every((asset) => asset.coverImage && asset.tutorialId)).toBe(true);
});

test('reports a style conflict for strong eyes and sheer cheeks', async () => {
  const result = await learningService.checkCompatibility({ eyes: 'eyes-smoky', blush: 'blush-sheer' });

  expect(result).toContainEqual(expect.objectContaining({ type: 'style-conflict' }));
});

test('filters library assets by occasion and difficulty', async () => {
  const assets = await learningService.listAssets({ category: 'part', occasion: '通勤', difficulty: '新手' });

  expect(assets.length).toBeGreaterThan(0);
  expect(assets.every((asset) => asset.occasion === '通勤' && asset.difficulty === '新手')).toBe(true);
});

test('filters part assets by makeup part', async () => {
  const assets = await learningService.listAssets({ category: 'part', part: 'eyes' });

  expect(assets.length).toBeGreaterThan(0);
  expect(assets.every((asset) => asset.category === 'part' && asset.part === 'eyes')).toBe(true);
});

test('exposes only one eye contour and lip asset to the part library', async () => {
  const assets = await learningService.listAssets({ category: 'part', placement: 'library' });

  expect(assets.map(({ part }) => part)).toEqual(['eyes', 'contour', 'lips']);
});

test('keeps personalized adjustment and mix results as the current tutorial', async () => {
  const request = {
    styles: ['清冷高级', '个性酷感'],
    occasions: ['约会聚会'],
    retainedParts: ['眼妆'],
    skinType: '混合性肌肤',
    concerns: ['放大眼睛'],
    constraints: ['没有专业刷具'],
  };
  const adjusted = await learningService.saveAdjustment(request);
  expect(adjusted.title).toContain('清冷高级');
  expect(JSON.parse(sessionStorage.getItem('makeupAdjustment') ?? '{}')).toEqual(request);
  expect((await learningService.getTutorial()).id).toBe(adjusted.id);

  const decision = { base: null, eyes: 'eyes-smoky', blush: 'blush-sheer', contour: null, lips: 'lips-rose' };
  const mixed = await learningService.generateMix(decision);
  expect(mixed.tutorialId).toContain('tutorial-mix-');
  expect((await learningService.getTutorial(mixed.tutorialId)).steps.find((step) => step.part === 'eyes')?.product).toBe('低饱和烟熏眼妆');
  expect(await learningService.getMixResult(mixed.id)).toEqual(mixed);
  expect(JSON.parse(sessionStorage.getItem('makeupMixDecision') ?? '{}')).toEqual(decision);
});

test('selects tutorials by id so the default flow cannot reuse stale personalization', async () => {
  const mixed = await learningService.generateMix({ base: null, eyes: null, blush: 'blush-peach', contour: null, lips: null });

  expect((await learningService.getTutorial(mixed.tutorialId)).id).toBe(mixed.tutorialId);
  expect((await learningService.getTutorial('tutorial-rose-commute')).title).toBe('清透玫瑰通勤妆');
});
