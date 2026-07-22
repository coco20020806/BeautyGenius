# Preset Library Mix Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn knowledge-library items into preset video-cover links and replace instant mix generation with a complete five-part decision, loading, preview, suitability, and tutorial flow.

**Architecture:** Extend the typed learning service with preset cover/tutorial metadata, complete mix decisions, and persistent preset mix results. Keep selection at `/library?tab=mix`, add dedicated `/mix/generating` and `/mix/preview` pages, and reuse the existing before/after and adjustment interaction patterns.

**Tech Stack:** React, TypeScript, React Router, CSS, Vitest, Testing Library, sessionStorage

---

### Task 1: Define preset asset and mix-result contracts

**Files:**
- Modify: `src/types/learning.ts`
- Modify: `src/services/learningService.test.ts`
- Modify: `src/services/learningService.ts`

- [ ] Add a failing service test that requests library assets and expects `coverImage` and `tutorialId`, then submits a complete five-part decision containing both asset IDs and `null` skips and expects a persisted `MixResult`.

- [ ] Add these contract types:

```ts
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
```

Add `coverImage: string` and `tutorialId: string` to `LibraryAsset`. Replace `generateMix(selection: MixSelection): Promise<IllustratedTutorial>` with `generateMix(decision: MixDecision): Promise<MixResult>` and add `getMixResult(resultId?: string): Promise<MixResult | null>`.

- [ ] Update local assets with bundled placeholder cover URLs and stable tutorial IDs. Persist decisions as `makeupMixDecision` and results as `makeupMixResult` in `sessionStorage`. Build a preset tutorial from selected non-null assets, remember it under `tutorialId`, and return a deterministic result using existing before/after assets.

- [ ] Run `npm test -- --run src/services/learningService.test.ts` and confirm the service tests pass.

### Task 2: Show preset video covers and route every asset to its tutorial

**Files:**
- Modify: `src/components/AssetCard.tsx`
- Modify: `src/pages/LibraryPage.tsx`
- Modify: `src/pages/LibraryPage.test.tsx`
- Modify: `src/styles/learning.css`

- [ ] Add failing tests asserting that cards contain an image named `${asset.title}视频封面`, no file input or video player exists, and both tutorial and part cards navigate to `/tutorial` with their mapped tutorial ID.

- [ ] Replace the synthetic card artwork with:

```tsx
<img src={asset.coverImage} alt={`${asset.title}视频封面`} />
```

Keep the practiced marker and copy layout. Update `selectAsset` so both supported categories call:

```ts
navigate('/tutorial', { state: { from: `/library?tab=${category}`, tutorialId: asset.tutorialId } });
```

- [ ] Update cover image CSS to use `object-fit: cover`, preserve the current card proportions, and remove unused mini-eye/mini-lips styles.

- [ ] Run `npm test -- --run src/pages/LibraryPage.test.tsx` and confirm it passes.

### Task 3: Replace the mix image with five complete decisions

**Files:**
- Modify: `src/components/MixEditor.tsx`
- Delete: `src/components/MixFace.tsx`
- Modify: `src/pages/MixPage.test.tsx`
- Modify: `src/styles/learning.css`

- [ ] Add failing tests asserting no `混搭妆容预览` image exists, all five part sections exist, each offers `跳过此部位`, and `生成效果` remains disabled until every part is selected or skipped.

- [ ] Replace `MixSelection` state with a decision state that distinguishes unresolved from skipped:

```ts
type DraftMixDecision = Record<MixPart, string | null | undefined>;
const initialDecision = { base: undefined, eyes: undefined, blush: undefined, contour: undefined, lips: undefined };
const complete = mixParts.every((part) => decision[part] !== undefined);
```

Render five option sections. Each section displays preset assets for that part plus a `跳过此部位` button. Selected and skipped states use the existing rose selection treatment. Show `已完成 X/5` and disable `生成效果` until `complete`.

- [ ] On submit, save the complete `MixDecision` to `sessionStorage` and navigate to `/mix/generating` without calling `generateMix` on the selection page.

- [ ] Remove `MixFace` imports, component file, face-slot CSS, compatibility card, and instant tutorial generation.

- [ ] Run `npm test -- --run src/pages/MixPage.test.tsx` and confirm it passes.

### Task 4: Add the visual loading page

**Files:**
- Create: `src/pages/MixGeneratingPage.tsx`
- Create: `src/pages/MixGeneratingPage.test.tsx`
- Modify: `src/App.tsx`
- Modify: `src/styles/learning.css`

- [ ] Add failing tests using fake timers: an incomplete or absent decision redirects to `/library?tab=mix`; a complete decision displays progress/stages, calls `generateMix`, and navigates to `/mix/preview` with `resultId`.

- [ ] Implement `/mix/generating` with an accessible progressbar, three stages (`整理部位选择`, `匹配预制妆效`, `准备效果预览`), remaining-time copy, and back action. Animate progress while awaiting `learningService.generateMix`.

- [ ] On success, navigate with:

```ts
navigate('/mix/preview', { replace: true, state: { resultId: result.id } });
```

On failure, render the failure reason plus `重新生成` and `返回修改` buttons.

- [ ] Add the route in `AppRoutes` and run the focused page test.

### Task 5: Add preset mix preview and suitability routing

**Files:**
- Create: `src/pages/MixPreviewPage.tsx`
- Create: `src/pages/MixPreviewPage.test.tsx`
- Modify: `src/App.tsx`
- Modify: `src/pages/AdjustPage.tsx`
- Modify: `src/styles/learning.css`

- [ ] Add failing tests asserting the page restores a `MixResult`, renders `BeforeAfterSlider`, sends `适合我` to the result tutorial ID, and sends `需要微调` to `/adjust` with `baseTutorialId`.

- [ ] Implement `/mix/preview` using `learningService.getMixResult(resultId)`. Render the existing comparison component, preset title/summary, decision card, and buttons matching the current preview page.

- [ ] Route decisions as follows:

```ts
navigate('/tutorial', { state: { from: '/mix/preview', tutorialId: result.tutorialId } });
navigate('/adjust', { state: { from: '/mix/preview', baseTutorialId: result.tutorialId } });
```

- [ ] Update `AdjustPage` to read `baseTutorialId` and `from`, pass the base tutorial context into `saveAdjustment`, and return the adjusted tutorial with `from` preserved. Extend `AdjustmentRequest` with optional `baseTutorialId?: string` if needed by the service boundary.

- [ ] Add the route and run the focused preview and adjustment flow tests.

### Task 6: Cover the complete route flow

**Files:**
- Modify: `src/pages/LearningFlow.test.tsx`
- Modify: `src/pages/AppFlow.test.tsx`

- [ ] Add an integration test that enters the mix tab, resolves five parts through selections/skips, starts generation, observes the loading route, reaches preview, chooses `适合我`, and sees `图示教程`.

- [ ] Add the alternate integration branch that chooses `需要微调`, submits the existing questionnaire, and reaches the adjusted tutorial.

- [ ] Run `npm test -- --run src/pages/LearningFlow.test.tsx src/pages/AppFlow.test.tsx` and confirm both branches pass.

### Task 7: Update backend integration documentation

**Files:**
- Modify: `docs/backend-integration.md`

- [ ] Document `coverImage`, `tutorialId`, `MixDecision`, `MixResult`, and the routes `/mix/generating` and `/mix/preview`.

- [ ] Specify that knowledge assets are curated backend content: no upload endpoint and no playback requirement. Specify that mix generation maps decisions to preset results rather than generating images in real time.

- [ ] Add API examples for submitting a complete decision with nullable skipped parts and polling/fetching the preset result.

### Task 8: Final verification and commit

**Files:**
- Verify all modified files

- [ ] Run `npm test -- --run`; expect all tests to pass.
- [ ] Run `npm run build`; expect TypeScript and Vite build success.
- [ ] Run `npm run lint`; expect zero warnings and errors.
- [ ] Run `git diff --check`; expect no whitespace errors.
- [ ] Verify `curl -I http://127.0.0.1:5174/library?tab=mix` returns HTTP 200.
- [ ] Commit implementation with `git commit -m "feat: add preset mix preview flow"`.
