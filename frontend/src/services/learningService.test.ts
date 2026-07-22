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

test('exposes collected-tutorial cards with sample-1 cover from fixture', async () => {
  const assets = await learningService.listAssets({ category: 'tutorial' });

  expect(assets).toHaveLength(2);
  expect(assets.map(({ title }) => title)).toEqual(['示例视频1', '示例视频2']);
  expect(assets[0]?.coverImage).toBeTruthy();
  expect(assets[0]?.source).toBe('本地解析');
  expect(assets[1]?.coverImage).toBe('');
  expect(assets[1]?.source).toBe('待解析');
});

test('loads collected sample detail placeholders by asset id', async () => {
  const sample = await learningService.getCollectedSample('collected-sample-2');

  expect(sample?.title).toBe('示例视频2');
  expect(sample?.practiceTutorial.tutorial_id).toContain('placeholder_sample_2');
  expect(sample?.practiceTutorial.steps.length).toBeGreaterThan(0);
  expect(sample?.illustratedSteps.length).toBeGreaterThan(0);
  expect(await learningService.getCollectedSample('missing')).toBeNull();
});

test('loads collected sample 1 from packaged pipeline fixture', async () => {
  const sample = await learningService.getCollectedSample('collected-sample-1');

  expect(sample?.title).toBe('示例视频1');
  expect(sample?.beforeImage).toBeTruthy();
  expect(sample?.afterImage).toBeTruthy();
  expect(sample?.practiceTutorial.tutorial_id).toBe('tutorial_20260723_011751');
  expect(sample?.practiceTutorial.videoUrl).toBe('/fixtures/collected/sample-1.mp4');
  expect(sample?.practiceTutorial.steps.length).toBe(9);
  expect(sample?.illustratedSteps).toHaveLength(9);
  expect(sample?.illustratedSteps.every((step) => Boolean(step.diagramImage))).toBe(true);
});

test('exposes only one eye contour and lip asset to the part library', async () => {
  const assets = await learningService.listAssets({ category: 'part', placement: 'library' });

  expect(assets.map(({ part }) => part)).toEqual(['eyes', 'contour', 'lips']);
  expect(assets.every((asset) => asset.coverImage && !asset.coverImage.includes('photo-collage'))).toBe(true);
  expect(assets.every((asset) => asset.source === '知识库部位素材')).toBe(true);
});

test('loads part preset tutorials with packaged diagram images and source videos', async () => {
  const expectedVideos: Record<string, RegExp> = {
    'preset-eyes-rose': /eyes\/media\/source\.mp4/,
    'preset-contour-soft': /contour\/media\/source\.mp4/,
    'preset-lips-rose': /lips\/media\/source\.mp4/,
  };
  for (const [tutorialId, videoPattern] of Object.entries(expectedVideos)) {
    const tutorial = await learningService.getTutorial(tutorialId);
    expect(tutorial.id).toBe(tutorialId);
    expect(tutorial.steps).toHaveLength(1);
    expect(tutorial.steps[0]?.diagramImage).toBeTruthy();
    expect(tutorial.videoUrl).toMatch(videoPattern);
  }
});

test('returns no assets for the full-face part filter', async () => {
  const assets = await learningService.listAssets({ category: 'part', placement: 'library', part: 'full-face' });

  expect(assets).toEqual([]);
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

  const decision = { base: null, eyes: 'eyes-rose', blush: null, contour: 'contour-soft', lips: 'lips-rose' };
  const mixed = await learningService.generateMix(decision);
  expect(mixed.tutorialId).toContain('tutorial-mix-');
  const tutorial = await learningService.getTutorial(mixed.tutorialId);
  expect(tutorial.title).toBe('我的混搭图示流程');
  expect(tutorial.steps.map((step) => step.part)).toEqual(['eyes', 'contour', 'lips']);
  expect(tutorial.steps[0]?.product).toBe('裸粉眼影');
  expect(tutorial.steps[0]?.diagramImage).toBeTruthy();
  expect(tutorial.steps[1]?.product).toBe('暖棕修容粉');
  expect(tutorial.steps[2]?.product).toBe('低饱和玫瑰唇釉');
  expect(await learningService.getMixResult(mixed.id)).toEqual(mixed);
  expect(JSON.parse(sessionStorage.getItem('makeupMixDecision') ?? '{}')).toEqual(decision);
});

test('selects tutorials by id so the default flow cannot reuse stale personalization', async () => {
  const mixed = await learningService.generateMix({ base: null, eyes: null, blush: null, contour: null, lips: 'lips-rose' });

  expect((await learningService.getTutorial(mixed.tutorialId)).id).toBe(mixed.tutorialId);
  expect((await learningService.getTutorial(mixed.tutorialId)).steps).toHaveLength(1);
  expect((await learningService.getTutorial('tutorial-rose-commute')).title).toBe('清透玫瑰通勤妆');
});
