# Library Slots and Static Preference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove redundant library section titles, show exactly one eye/contour/lip part card, and make profile style a non-interactive information row.

**Architecture:** Add a display-scope flag to curated part assets so the service can expose only three cards to the library while retaining all five-part options for the mix editor. Keep the existing filters and routes intact; simplify the profile component by replacing its stateful style control with static markup.

**Tech Stack:** React 19, TypeScript, React Router, Testing Library, Vitest, CSS

---

### Task 1: Specify the knowledge library content

**Files:**
- Modify: `src/services/learningService.test.ts`
- Modify: `src/pages/LibraryPage.test.tsx`

- [ ] **Step 1: Write a failing service test for the three library part slots**

```ts
test('exposes only one eye contour and lip asset to the part library', async () => {
  const assets = await learningService.listAssets({ category: 'part', placement: 'library' });
  expect(assets.map(({ part }) => part)).toEqual(['eyes', 'contour', 'lips']);
});
```

- [ ] **Step 2: Write failing page assertions for titles and retained filters**

On the part tab, assert `教程资产` and `部位资产` are absent, all six original filter labels exist, the all view contains three cards, and the eyes filter contains one card.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
npm test -- --run src/services/learningService.test.ts src/pages/LibraryPage.test.tsx
```

Expected: FAIL because `LibraryFilter` has no placement field, the service exposes every part asset, and section headings still render.

### Task 2: Separate library slots from mix options

**Files:**
- Modify: `src/types/learning.ts`
- Modify: `src/services/learningService.ts`
- Modify: `src/pages/LibraryPage.tsx`

- [ ] **Step 1: Add an optional asset placement filter**

Extend the filter without changing asset response fields:

```ts
export interface LibraryFilter {
  category?: AssetCategory;
  placement?: 'library' | 'mix';
  // existing fields remain
}
```

- [ ] **Step 2: Mark exactly three part assets as library-visible**

Add a private `placements` field to the local asset literals. The rose eyes, soft contour, and rose lips assets include `library`; base and blush remain `mix` only. In `listAssets`, apply placement filtering before returning results. The mix editor requests `{ category: 'part', placement: 'mix' }`; the library requests `{ category: 'part', placement: 'library' }`.

- [ ] **Step 3: Remove the asset heading row**

Replace the asset section contents with the grid or existing empty state directly:

```tsx
<section className="asset-section" aria-live="polite">
  {assets.length ? <div className="asset-grid">...</div> : <div className="empty-library">...</div>}
</section>
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```bash
npm test -- --run src/services/learningService.test.ts src/pages/LibraryPage.test.tsx src/pages/MixPage.test.tsx
```

Expected: all focused tests pass, including mix availability.

### Task 3: Make profile preference static

**Files:**
- Modify: `src/pages/ProfilePage.test.tsx`
- Modify: `src/pages/ProfilePage.tsx`
- Modify: `src/styles/learning.css`

- [ ] **Step 1: Replace the editing test with a failing static-row test**

```tsx
test('shows preference style as static profile information', () => {
  render(<MemoryRouter><ProfilePage /></MemoryRouter>);
  expect(screen.getByText('偏好风格')).toBeInTheDocument();
  expect(screen.getByText('清透自然')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /偏好风格/ })).not.toBeInTheDocument();
  expect(screen.queryByRole('listbox', { name: '选择偏好风格' })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run the profile test and verify RED**

Run `npm test -- --run src/pages/ProfilePage.test.tsx`.

Expected: FAIL because preference style is currently a button.

- [ ] **Step 3: Remove editing state and render static markup**

Remove `styleOptions`, `stylesOpen`, and preference click handling. Render:

```tsx
<div className="profile-setting-static">
  <span><Palette size={17} /></span>
  <div><strong>偏好风格</strong><small>{profile.style}</small></div>
</div>
```

Keep `profile` state and `save` because learning reminders still persist. Extend the settings row CSS selectors so the static row matches adjacent controls without receiving button behavior.

- [ ] **Step 4: Run the profile test and verify GREEN**

Run `npm test -- --run src/pages/ProfilePage.test.tsx`.

Expected: PASS.

### Task 4: Verify, commit, and merge

**Files:**
- Modify: `docs/backend-integration.md`

- [ ] **Step 1: Document curated library placement**

State that the library part view exposes three curated cover slots, while mix options are a separate preset placement and are not constrained to those three cards.

- [ ] **Step 2: Run complete verification**

```bash
npm test -- --run
npm run lint
npm run build
git diff --check
```

Expected: all tests pass, ESLint reports no warnings, Vite production build succeeds, and no whitespace errors exist.

- [ ] **Step 3: Commit implementation**

```bash
git add docs/backend-integration.md src/types/learning.ts src/services/learningService.ts src/services/learningService.test.ts src/pages/LibraryPage.tsx src/pages/LibraryPage.test.tsx src/components/MixEditor.tsx src/pages/ProfilePage.tsx src/pages/ProfilePage.test.tsx src/styles/learning.css
git commit -m "feat: refine library slots and profile preference"
```

- [ ] **Step 4: Merge after final verification**

Because the user selected local merge, switch to `main`, merge `feature/makeup-learning-pages`, rerun the full test suite on the merged result, and remove the feature worktree only after the merge verification succeeds.
