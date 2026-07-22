# Makeup Learning Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add interactive adjustment, illustrated tutorial, eye guide, library, and mix editor pages while removing the practice page and navigation item.

**Architecture:** Extend the existing typed local service with learning-content entities and keep page state in focused route components. Reuse the current mobile shell, visual tokens, portrait assets, and backend-replaceable service boundary.

**Tech Stack:** React, TypeScript, React Router, Lucide React, Vitest, Testing Library, CSS.

---

## File Map

- `src/types/learning.ts`: adjustment, tutorial, eye guide, library, and mix types.
- `src/services/learningService.ts`: local data service and future HTTP replacement boundary.
- `src/services/learningService.test.ts`: data filtering, adjustment, and compatibility tests.
- `src/pages/AdjustPage.tsx`: micro-adjustment form.
- `src/pages/TutorialPage.tsx`: illustrated face tutorial and timeline.
- `src/pages/EyeGuidePage.tsx`: interactive eye-region guide.
- `src/pages/LibraryPage.tsx`: searchable/filterable asset library.
- `src/pages/MixPage.tsx`: selectable makeup-part editor.
- `src/components/BottomNav.tsx`: home/library/mix/profile navigation.
- `src/App.tsx`: routes and removal of `/practice`.
- `src/styles/learning.css`: new-page styling.
- `src/pages/LearningFlow.test.tsx`: cross-page navigation regression tests.
- `docs/backend-integration.md`: extended integration contracts.

### Task 1: Add typed learning service

**Files:** Create `src/types/learning.ts`, `src/services/learningService.ts`, `src/services/learningService.test.ts`.

- [ ] **Step 1: Write failing service tests**

```ts
test('filters library assets by search and category', async () => {
  const assets = await learningService.listAssets({ query: '眼妆', category: 'part' });
  expect(assets.every((asset) => asset.category === 'part')).toBe(true);
  expect(assets.some((asset) => asset.title.includes('眼妆'))).toBe(true);
});

test('reports a style conflict for strong eyes and sheer cheeks', async () => {
  const result = await learningService.checkCompatibility({ eyes: 'eyes-smoky', blush: 'blush-sheer' });
  expect(result).toContainEqual(expect.objectContaining({ type: 'style-conflict' }));
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/services/learningService.test.ts`

Expected: FAIL because the learning service does not exist.

- [ ] **Step 3: Implement service types and deterministic local data**

```ts
export interface LearningService {
  saveAdjustment(request: AdjustmentRequest): Promise<IllustratedTutorial>;
  getTutorial(): Promise<IllustratedTutorial>;
  getEyeGuides(): Promise<EyeRegionGuide[]>;
  listAssets(filter: LibraryFilter): Promise<LibraryAsset[]>;
  checkCompatibility(selection: MixSelection): Promise<CompatibilityHint[]>;
}
```

Include seven tutorial steps, seven eye regions, nine library assets, and compatible mix selections with stable IDs.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- --run src/services/learningService.test.ts`

Expected: PASS.

```bash
git add src/types/learning.ts src/services/learningService.ts src/services/learningService.test.ts
git commit -m "feat: add typed makeup learning service"
```

### Task 2: Replace practice navigation and add routes

**Files:** Modify `src/components/BottomNav.tsx`, `src/App.tsx`, `src/pages/AppFlow.test.tsx`; create skeletal route components for the five pages.

- [ ] **Step 1: Write failing navigation test**

```tsx
test('uses home, library, mix and profile as top-level navigation', () => {
  renderNavigation();
  expect(screen.queryByRole('link', { name: /跟练/ })).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: /混搭/ })).toHaveAttribute('href', '/mix');
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/AppFlow.test.tsx`

Expected: FAIL because the practice entry still exists.

- [ ] **Step 3: Replace navigation and routes**

Set navigation to `/`, `/library`, `/mix`, `/profile`. Add `/adjust`, `/tutorial`, and `/eyes`; replace library placeholder; remove `/practice`.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- --run src/pages/AppFlow.test.tsx`

Expected: PASS.

```bash
git add src/App.tsx src/components/BottomNav.tsx src/pages src/pages/AppFlow.test.tsx
git commit -m "feat: add learning routes and update navigation"
```

### Task 3: Build micro-adjustment page and preview decisions

**Files:** Create `src/pages/AdjustPage.tsx`, `src/pages/AdjustPage.test.tsx`; modify `src/pages/PreviewPage.tsx`, `src/pages/PreviewPage.test.tsx`.

- [ ] **Step 1: Write failing interaction tests**

```tsx
test('submits selected adjustment and opens tutorial', async () => {
  renderAdjustPage();
  await user.click(screen.getByRole('radio', { name: '更日常' }));
  await user.click(screen.getByRole('checkbox', { name: '只有手指' }));
  await user.type(screen.getByLabelText('补充要求'), '眼妆淡一点');
  await user.click(screen.getByRole('button', { name: '生成方案' }));
  expect(screen.getByRole('heading', { name: '图示教程' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/AdjustPage.test.tsx src/pages/PreviewPage.test.tsx`

Expected: FAIL because the form and decision routes are missing.

- [ ] **Step 3: Implement form and route decisions**

Render single-select style and occasion groups, multi-select tools, optional text, and a primary action. “适合我” opens `/tutorial`; the other two preview decisions open `/adjust`.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- --run src/pages/AdjustPage.test.tsx src/pages/PreviewPage.test.tsx`

Expected: PASS.

```bash
git add src/pages/AdjustPage.tsx src/pages/AdjustPage.test.tsx src/pages/PreviewPage.tsx src/pages/PreviewPage.test.tsx
git commit -m "feat: add makeup adjustment flow"
```

### Task 4: Build illustrated tutorial

**Files:** Create `src/pages/TutorialPage.tsx`, `src/pages/TutorialPage.test.tsx`, `src/components/FaceLayers.tsx`.

- [ ] **Step 1: Write failing tutorial tests**

```tsx
test('changes current step and opens eye guide for eye makeup', async () => {
  renderTutorialPage();
  await user.click(screen.getByRole('button', { name: /眼影打底/ }));
  expect(screen.getByText('裸粉眼影')).toBeInTheDocument();
  await user.click(screen.getByRole('link', { name: '查看眼部精讲' }));
  expect(screen.getByRole('heading', { name: '眼部精讲' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/TutorialPage.test.tsx`

Expected: FAIL because tutorial interactions are missing.

- [ ] **Step 3: Implement face layers, timeline, products, and mode switch**

Use the existing portrait geometry with SVG blush, contour, highlight, eye, and lip overlays. Selecting a step updates overlay opacity, product copy, and video-slice action.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- --run src/pages/TutorialPage.test.tsx`

Expected: PASS.

```bash
git add src/components/FaceLayers.tsx src/pages/TutorialPage.tsx src/pages/TutorialPage.test.tsx
git commit -m "feat: add illustrated makeup tutorial"
```

### Task 5: Build eye detail guide

**Files:** Create `src/pages/EyeGuidePage.tsx`, `src/pages/EyeGuidePage.test.tsx`, `src/components/EyeDiagram.tsx`.

- [ ] **Step 1: Write failing region test**

```tsx
test('updates guidance when an eye region is selected', async () => {
  renderEyeGuidePage();
  await user.click(screen.getByRole('button', { name: '眼线走势' }));
  expect(screen.getByText(/眼尾向外延伸/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/EyeGuidePage.test.tsx`

Expected: FAIL because the guide does not exist.

- [ ] **Step 3: Implement seven regions and slice controls**

Render all overlays on one eye diagram, region chips, slider-like video progress, previous/next controls, and current adaptation advice.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- --run src/pages/EyeGuidePage.test.tsx`

Expected: PASS.

```bash
git add src/components/EyeDiagram.tsx src/pages/EyeGuidePage.tsx src/pages/EyeGuidePage.test.tsx
git commit -m "feat: add interactive eye makeup guide"
```

### Task 6: Build searchable knowledge library

**Files:** Create `src/pages/LibraryPage.tsx`, `src/pages/LibraryPage.test.tsx`, `src/components/AssetCard.tsx`.

- [ ] **Step 1: Write failing filter and selection tests**

```tsx
test('filters assets and sends a selected part to mix editor', async () => {
  renderLibraryPage();
  await user.type(screen.getByRole('searchbox'), '眼妆');
  await user.click(screen.getByRole('tab', { name: '部位' }));
  await user.click(screen.getByRole('button', { name: /清透玫瑰眼妆/ }));
  expect(screen.getByRole('heading', { name: '混搭编辑' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/LibraryPage.test.tsx`

Expected: FAIL because searchable cards are missing.

- [ ] **Step 3: Implement tabs, search, filters, and asset grid**

Use accessible tabs and search input. Encode preselection as `/mix?part=eyes&asset=eyes-rose`.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- --run src/pages/LibraryPage.test.tsx`

Expected: PASS.

```bash
git add src/components/AssetCard.tsx src/pages/LibraryPage.tsx src/pages/LibraryPage.test.tsx
git commit -m "feat: add searchable makeup library"
```

### Task 7: Build mix editor and compatibility guidance

**Files:** Create `src/pages/MixPage.tsx`, `src/pages/MixPage.test.tsx`, `src/components/MixFace.tsx`.

- [ ] **Step 1: Write failing mix tests**

```tsx
test('changes a part selection and generates a tutorial', async () => {
  renderMixPage('/mix?part=eyes&asset=eyes-rose');
  expect(screen.getByText('清透玫瑰眼妆')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '生成教程' }));
  expect(screen.getByRole('heading', { name: '图示教程' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/MixPage.test.tsx`

Expected: FAIL because the editor is missing.

- [ ] **Step 3: Implement slots, selected assets, and hints**

Use seven visible part slots around the face, selectable asset chips, compatibility status, and generate action.

- [ ] **Step 4: Verify GREEN and commit**

Run: `npm test -- --run src/pages/MixPage.test.tsx`

Expected: PASS.

```bash
git add src/components/MixFace.tsx src/pages/MixPage.tsx src/pages/MixPage.test.tsx
git commit -m "feat: add makeup mix editor"
```

### Task 8: Apply visual system, integration tests, and backend documentation

**Files:** Create `src/styles/learning.css`, `src/pages/LearningFlow.test.tsx`; modify `src/main.tsx`, `docs/backend-integration.md`.

- [ ] **Step 1: Write failing end-to-end learning flow test**

```tsx
test('moves from preview through adjustment to tutorial and eye guide', async () => {
  renderLearningFlow('/preview');
  await user.click(await screen.findByRole('button', { name: '需要微调' }));
  await user.click(screen.getByRole('button', { name: '生成方案' }));
  await user.click(screen.getByRole('button', { name: /眼影打底/ }));
  await user.click(screen.getByRole('link', { name: '查看眼部精讲' }));
  expect(screen.getByRole('heading', { name: '眼部精讲' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/LearningFlow.test.tsx`

Expected: FAIL until route interactions are fully connected.

- [ ] **Step 3: Add reference-aligned styling and document contracts**

Extend the collage visual language with compact mobile cards, central diagrams, timelines, chips, and four-item navigation. Document adjustment, tutorial, library, and mix endpoints in `docs/backend-integration.md`.

- [ ] **Step 4: Run complete verification**

Run: `npm test -- --run`

Expected: all tests PASS.

Run: `npm run build`

Expected: TypeScript and Vite build exit 0.

Run: `npm run lint`

Expected: ESLint exits 0 with no warnings.

- [ ] **Step 5: Commit**

```bash
git add src docs/backend-integration.md
git commit -m "feat: complete makeup learning pages"
```
