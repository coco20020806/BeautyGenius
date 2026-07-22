# Page Header and Profile Background Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a consistent English heading to the home page and apply an asset-backed, library-style background to the profile page while removing its Chinese title.

**Architecture:** Keep the existing React page structure and CSS architecture. Copy the selected source image into the bundled asset directory, then verify markup and CSS behavior with the existing Vitest suite.

**Tech Stack:** React, TypeScript, CSS, Vitest, Testing Library, Vite

---

### Task 1: Specify heading behavior

**Files:**
- Modify: `src/pages/UploadPage.test.tsx`
- Modify: `src/pages/ProfilePage.test.tsx`

- [ ] Add assertions that home renders `MY BEAUTY STUDIO`, profile renders `MY BEAUTY PROFILE`, and profile does not render an `h1` named `我的`.
- [ ] Run `npm test -- --run src/pages/UploadPage.test.tsx src/pages/ProfilePage.test.tsx` and confirm the new home-title assertion fails.

### Task 2: Implement page headings and background

**Files:**
- Modify: `src/pages/UploadPage.tsx`
- Modify: `src/pages/ProfilePage.tsx`
- Modify: `src/styles/global.css`
- Modify: `src/styles/learning.css`
- Create: `src/assets/bg-profile-flower.png`

- [ ] Copy `图片资产/知识库页 (1).png` to `src/assets/bg-profile-flower.png`.
- [ ] Add a home header containing `<span className="page-kicker">MY BEAUTY STUDIO</span>`.
- [ ] Remove the profile heading's Chinese `<h1>我的</h1>`.
- [ ] Apply the library gradient values to `.profile-page` with `bg-profile-flower.png`.
- [ ] Run the focused tests and confirm they pass.

### Task 3: Verify and commit

**Files:**
- Verify all modified files

- [ ] Run `npm test -- --run` and expect all tests to pass.
- [ ] Run `npm run build` and expect a successful Vite build.
- [ ] Run `npm run lint` and expect no lint errors.
- [ ] Run `git diff --check` and expect no whitespace errors.
- [ ] Commit with `git commit -m "feat: refine home and profile page styling"`.
