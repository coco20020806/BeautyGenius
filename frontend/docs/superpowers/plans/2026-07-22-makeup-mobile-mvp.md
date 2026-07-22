# Makeup Mobile MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a mobile-first React frontend that completes the video upload, optional photo upload, simulated parsing, and draggable before/after makeup preview flow.

**Architecture:** Use route-level screens composed from focused shared components. Keep upload and parsing behavior behind typed service interfaces so a future backend implementation can replace the local service without changing screen structure.

**Tech Stack:** React 19, TypeScript, Vite, React Router, Vitest, Testing Library, CSS Modules/global design tokens, Lucide React.

---

## File Map

- `package.json`, `vite.config.ts`, `tsconfig*.json`, `index.html`: application and test tooling.
- `src/main.tsx`, `src/App.tsx`: application bootstrap and routes.
- `src/styles/global.css`: mobile design tokens, reset, shell, accessibility, and responsive rules.
- `src/types/makeup.ts`: backend-facing types.
- `src/services/makeupService.ts`: service contract and local MVP implementation.
- `src/services/makeupService.test.ts`: service behavior tests.
- `src/components/MobileShell.tsx`: centered mobile viewport and safe-area layout.
- `src/components/BottomNav.tsx`: four-item navigation.
- `src/components/BeforeAfterSlider.tsx`: pointer and keyboard accessible image comparison.
- `src/components/BeforeAfterSlider.test.tsx`: slider interaction tests.
- `src/pages/UploadPage.tsx`: video selection, requirements, recent tasks.
- `src/pages/PhotoPage.tsx`: photo selection, preview, skip and privacy copy.
- `src/pages/ParsingPage.tsx`: progress ring, stages, recovery and navigation.
- `src/pages/PreviewPage.tsx`: before/after preview, palette, summary and decisions.
- `src/pages/PlaceholderPage.tsx`: bottom-navigation placeholders.
- `src/pages/AppFlow.test.tsx`: end-to-end component flow tests.
- `src/assets/face-before.svg`, `src/assets/face-after.svg`: stable local demo portraits with identical geometry.

### Task 1: Scaffold and route shell

**Files:** Create `package.json`, `vite.config.ts`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `index.html`, `src/main.tsx`, `src/App.tsx`, `src/test/setup.ts`, `src/pages/PlaceholderPage.tsx`, `src/App.test.tsx`.

- [ ] **Step 1: Write the routing smoke test**

```tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AppRoutes } from './App';

test('renders the upload screen at the root route', () => {
  render(<MemoryRouter initialEntries={['/']}><AppRoutes /></MemoryRouter>);
  expect(screen.getByRole('heading', { name: '上传教程' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Install dependencies and verify RED**

Run: `npm install && npm test -- --run src/App.test.tsx`

Expected: FAIL because `AppRoutes` and the upload page do not exist.

- [ ] **Step 3: Add Vite/Vitest configuration and minimal routes**

```tsx
export function AppRoutes() {
  return <Routes><Route path="/" element={<UploadPage />} /><Route path="/practice" element={<PlaceholderPage title="跟练" />} /><Route path="/library" element={<PlaceholderPage title="知识库" />} /><Route path="/profile" element={<PlaceholderPage title="我的" />} /></Routes>;
}
```

- [ ] **Step 4: Verify GREEN**

Run: `npm test -- --run src/App.test.tsx`

Expected: PASS, 1 test.

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json vite.config.ts tsconfig.json tsconfig.app.json tsconfig.node.json index.html src/main.tsx src/App.tsx src/App.test.tsx src/test/setup.ts src/pages/PlaceholderPage.tsx src/pages/UploadPage.tsx
git commit -m "chore: scaffold makeup mobile frontend"
```

### Task 2: Add backend-ready service contract

**Files:** Create `src/types/makeup.ts`, `src/services/makeupService.ts`, `src/services/makeupService.test.ts`.

- [ ] **Step 1: Write failing service tests**

```ts
test('rejects unsupported video files', async () => {
  const file = new File(['x'], 'tutorial.txt', { type: 'text/plain' });
  await expect(makeupService.uploadVideo(file)).rejects.toThrow('仅支持 MP4 或 MOV 视频');
});

test('progress reaches preview-ready state', async () => {
  const states = await collectAnalysis(makeupService.analyze('task-1'));
  expect(states.at(-1)).toMatchObject({ progress: 100, status: 'completed' });
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/services/makeupService.test.ts`

Expected: FAIL because the service contract is missing.

- [ ] **Step 3: Implement explicit types and local service**

```ts
export interface MakeupService {
  uploadVideo(file: File): Promise<UploadVideoResult>;
  uploadPhoto(file: File | null): Promise<UploadPhotoResult>;
  analyze(taskId: string): AsyncGenerator<AnalysisProgress>;
  getPreview(taskId: string): Promise<MakeupPreview>;
}
```

The local implementation validates MIME type and size, yields four deterministic progress stages, and returns local portrait assets plus palette and suitability copy.

- [ ] **Step 4: Verify GREEN**

Run: `npm test -- --run src/services/makeupService.test.ts`

Expected: PASS, both service behaviors.

- [ ] **Step 5: Commit**

```bash
git add src/types/makeup.ts src/services/makeupService.ts src/services/makeupService.test.ts
git commit -m "feat: add typed makeup workflow service"
```

### Task 3: Build upload page and bottom navigation

**Files:** Create `src/components/MobileShell.tsx`, `src/components/BottomNav.tsx`; modify `src/pages/UploadPage.tsx`; create `src/pages/UploadPage.test.tsx`.

- [ ] **Step 1: Write failing upload interaction test**

```tsx
test('shows selected video and enables continue', async () => {
  renderUploadPage();
  const file = new File(['video'], 'daily-look.mp4', { type: 'video/mp4' });
  await userEvent.upload(screen.getByLabelText('选择教程视频'), file);
  expect(screen.getByText('daily-look.mp4')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '下一步' })).toBeEnabled();
  expect(screen.getByRole('navigation', { name: '主导航' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/UploadPage.test.tsx`

Expected: FAIL because upload controls and navigation are missing.

- [ ] **Step 3: Implement image-first structure**

Use the exact order: page title, primary dashed upload card, three video requirements, recent task cards, and fixed four-item bottom navigation. Continue calls `uploadVideo` and navigates to `/photo` with the task ID stored in session storage.

- [ ] **Step 4: Verify GREEN**

Run: `npm test -- --run src/pages/UploadPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/MobileShell.tsx src/components/BottomNav.tsx src/pages/UploadPage.tsx src/pages/UploadPage.test.tsx
git commit -m "feat: build mobile tutorial upload page"
```

### Task 4: Build optional photo confirmation

**Files:** Create `src/pages/PhotoPage.tsx`, `src/pages/PhotoPage.test.tsx`; modify `src/App.tsx`.

- [ ] **Step 1: Write failing skip and upload tests**

```tsx
test('allows the user to skip a personal photo', async () => {
  renderPhotoPage();
  await userEvent.click(screen.getByRole('button', { name: '暂时跳过' }));
  expect(mockNavigate).toHaveBeenCalledWith('/parsing');
});

test('previews a selected image before confirmation', async () => {
  renderPhotoPage();
  await userEvent.upload(screen.getByLabelText('上传本人照片'), new File(['face'], 'face.jpg', { type: 'image/jpeg' }));
  expect(screen.getByRole('img', { name: '待确认的本人照片' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/PhotoPage.test.tsx`

Expected: FAIL because the page does not exist.

- [ ] **Step 3: Implement the confirmation page**

Render title, portrait preview, three neutral requirements, privacy note, secondary re-upload, primary confirm, and visible skip action. Revoke old object URLs when replacing or leaving the selected photo.

- [ ] **Step 4: Verify GREEN**

Run: `npm test -- --run src/pages/PhotoPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/App.tsx src/pages/PhotoPage.tsx src/pages/PhotoPage.test.tsx
git commit -m "feat: add optional photo confirmation"
```

### Task 5: Build parsing progress screen

**Files:** Create `src/pages/ParsingPage.tsx`, `src/pages/ParsingPage.test.tsx`; modify `src/App.tsx`.

- [ ] **Step 1: Write failing progress test**

```tsx
test('shows progress stages and opens preview when complete', async () => {
  renderParsingPage();
  expect(screen.getByText('检查视频质量')).toBeInTheDocument();
  await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/preview'));
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/ParsingPage.test.tsx`

Expected: FAIL because progress UI is missing.

- [ ] **Step 3: Implement progress and recovery**

Consume the service async generator, render an SVG progress ring with numeric percentage, four node states, current stage and remaining seconds. Persist the latest state in session storage. On service error, show the supplied reason and a retry button.

- [ ] **Step 4: Verify GREEN**

Run: `npm test -- --run src/pages/ParsingPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/App.tsx src/pages/ParsingPage.tsx src/pages/ParsingPage.test.tsx
git commit -m "feat: add makeup analysis progress"
```

### Task 6: Build accessible before/after preview

**Files:** Create `src/assets/face-before.svg`, `src/assets/face-after.svg`, `src/components/BeforeAfterSlider.tsx`, `src/components/BeforeAfterSlider.test.tsx`, `src/pages/PreviewPage.tsx`, `src/pages/PreviewPage.test.tsx`; modify `src/App.tsx`.

- [ ] **Step 1: Write failing slider tests**

```tsx
test('supports complete before and after views', async () => {
  render(<BeforeAfterSlider beforeSrc="before.svg" afterSrc="after.svg" />);
  await userEvent.click(screen.getByRole('button', { name: '看妆后' }));
  expect(screen.getByRole('slider', { name: '妆前妆后对比位置' })).toHaveValue('100');
  await userEvent.click(screen.getByRole('button', { name: '看原图' }));
  expect(screen.getByRole('slider', { name: '妆前妆后对比位置' })).toHaveValue('0');
});

test('changes comparison with keyboard arrows', async () => {
  render(<BeforeAfterSlider beforeSrc="before.svg" afterSrc="after.svg" />);
  const slider = screen.getByRole('slider', { name: '妆前妆后对比位置' });
  slider.focus();
  await userEvent.keyboard('{ArrowRight}');
  expect(slider).toHaveValue('55');
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/components/BeforeAfterSlider.test.tsx`

Expected: FAIL because the slider is missing.

- [ ] **Step 3: Implement slider and preview page**

Use two identically sized stacked images. Clip the after image using the 0–100 slider value, update value from pointer position, and expose a native range input for keyboard and assistive technology. Render “原始状态” and “化妆后” labels, palette swatches, summary, three adaptation hints, and decision feedback.

- [ ] **Step 4: Verify component and page GREEN**

Run: `npm test -- --run src/components/BeforeAfterSlider.test.tsx src/pages/PreviewPage.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/App.tsx src/assets/face-before.svg src/assets/face-after.svg src/components/BeforeAfterSlider.tsx src/components/BeforeAfterSlider.test.tsx src/pages/PreviewPage.tsx src/pages/PreviewPage.test.tsx
git commit -m "feat: add interactive makeup adaptation preview"
```

### Task 7: Apply visual system and verify complete flow

**Files:** Create `src/styles/global.css`, `src/pages/AppFlow.test.tsx`; modify `src/main.tsx`, `src/components/MobileShell.tsx`, `src/components/BottomNav.tsx`, `src/components/BeforeAfterSlider.tsx`, `src/pages/UploadPage.tsx`, `src/pages/PhotoPage.tsx`, `src/pages/ParsingPage.tsx`, `src/pages/PreviewPage.tsx`, `src/pages/PlaceholderPage.tsx`.

- [ ] **Step 1: Write failing full-flow test**

```tsx
test('completes the MVP flow by skipping photo upload', async () => {
  renderApp();
  await selectVideo('tutorial.mp4');
  await userEvent.click(screen.getByRole('button', { name: '下一步' }));
  await userEvent.click(screen.getByRole('button', { name: '暂时跳过' }));
  await waitFor(() => expect(screen.getByRole('heading', { name: '适配预览' })).toBeInTheDocument());
  expect(screen.getByRole('slider', { name: '妆前妆后对比位置' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Verify RED**

Run: `npm test -- --run src/pages/AppFlow.test.tsx`

Expected: FAIL until the complete route flow is wired.

- [ ] **Step 3: Finish mobile styling and route wiring**

Define warm-white surfaces, charcoal text, muted rose action color, 44px touch targets, 320–430px responsive rules, desktop phone framing, safe-area padding, focus rings, and reduced-motion behavior. Keep the module order identical to the reference image.

- [ ] **Step 4: Run complete verification**

Run: `npm test -- --run`

Expected: all tests PASS with zero failures.

Run: `npm run build`

Expected: TypeScript and Vite build exit 0 and produce `dist/`.

Run: `npm run lint`

Expected: ESLint exits 0 with no warnings.

- [ ] **Step 5: Commit**

```bash
git add src
git commit -m "feat: complete makeup tutorial mobile MVP"
```
