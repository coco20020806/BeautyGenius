# Collapsible Mix Selector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the always-expanded five-part mix selector with independent collapsed cards where untouched parts automatically generate as skipped.

**Architecture:** Keep `MixDecision` and the downstream generation routes unchanged. Simplify `MixEditor` so its decision state starts as a complete five-key `null` record, while a separate `Set<MixPart>` controls visual expansion; this separates submission meaning from presentation state.

**Tech Stack:** React 19, TypeScript, React Router, Testing Library, Vitest, CSS

---

### Task 1: Specify the collapsed selector behavior

**Files:**
- Modify: `src/pages/MixPage.test.tsx`
- Modify: `src/pages/LearningFlow.test.tsx`

- [ ] **Step 1: Replace the old five-required-decisions test with collapsed-card assertions**

Update the mix page test to assert that options are initially absent, an individual part can be expanded and collapsed, no internal skip wording is rendered, and generation is immediately enabled:

```tsx
test('starts collapsed and treats untouched parts as skipped', async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={['/library?tab=mix']}>
      <Routes>
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/mix/generating" element={<h1>生成妆效中</h1>} />
      </Routes>
    </MemoryRouter>,
  );

  const eyes = screen.getByRole('button', { name: '展开眼妆选项' });
  expect(screen.queryByRole('button', { name: '清透玫瑰眼妆' })).not.toBeInTheDocument();
  expect(screen.queryByText(/默认跳过|已展开|待选择|跳过此部位/)).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: '生成效果' })).toBeEnabled();

  await user.click(eyes);
  expect(await screen.findByRole('button', { name: '清透玫瑰眼妆' })).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '收起眼妆选项' }));
  expect(screen.queryByRole('button', { name: '清透玫瑰眼妆' })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Add selected-summary and generated-decision coverage**

Add a second test that expands eyes, selects the rose asset, verifies its title appears in the collapsed header, generates, and verifies storage contains all five keys with only `eyes` selected:

```tsx
test('shows the chosen asset and generates null for untouched parts', async () => {
  const user = userEvent.setup();
  render(/* same routes as above */);

  await user.click(screen.getByRole('button', { name: '展开眼妆选项' }));
  await user.click(await screen.findByRole('button', { name: '清透玫瑰眼妆' }));
  expect(screen.getByRole('button', { name: /收起眼妆选项/ })).toHaveTextContent('清透玫瑰眼妆');
  await user.click(screen.getByRole('button', { name: '生成效果' }));

  expect(JSON.parse(sessionStorage.getItem('makeupMixDecision') ?? '{}')).toEqual({
    base: null,
    eyes: 'eyes-rose',
    blush: null,
    contour: null,
    lips: null,
  });
});
```

- [ ] **Step 3: Update the end-to-end learning flow test**

Remove the old loop that clicks five skip buttons. Generate directly from the initial mix page, then retain the existing loading, preview, and tutorial assertions:

```tsx
expect(screen.getByRole('button', { name: '生成效果' })).toBeEnabled();
await user.click(screen.getByRole('button', { name: '生成效果' }));
expect(await screen.findByRole('heading', { name: '生成妆效中' })).toBeInTheDocument();
expect(await screen.findByRole('heading', { name: '混搭效果预览' }, { timeout: 3000 })).toBeInTheDocument();
```

- [ ] **Step 4: Run the focused tests and verify RED**

Run:

```bash
npm test -- --run src/pages/MixPage.test.tsx src/pages/LearningFlow.test.tsx
```

Expected: FAIL because the current selector exposes all options, shows skip buttons, and disables generation before five decisions.

### Task 2: Implement independent collapsible part cards

**Files:**
- Modify: `src/components/MixEditor.tsx`
- Modify: `src/styles/learning.css`

- [ ] **Step 1: Replace unresolved decision state with default null values**

Use a complete decision from the first render and add independent expansion state:

```tsx
const initialDecision: MixDecision = {
  base: null,
  eyes: null,
  blush: null,
  contour: null,
  lips: null,
};

const [decision, setDecision] = useState<MixDecision>(initialDecision);
const [expandedParts, setExpandedParts] = useState<Set<MixPart>>(() => new Set());
```

Add a toggle that creates a new set rather than mutating React state:

```tsx
function togglePart(part: MixPart) {
  setExpandedParts((current) => {
    const next = new Set(current);
    if (next.has(part)) next.delete(part);
    else next.add(part);
    return next;
  });
}
```

- [ ] **Step 2: Make each card header an accessible disclosure button**

Render each part header as a button with `aria-expanded`, `aria-controls`, and state-specific labels. Show the chosen asset title only when there is a selection:

```tsx
const selected = assetsByPart[id].find((asset) => asset.id === decision[id]);
const expanded = expandedParts.has(id);

<button
  className="mix-part-toggle"
  type="button"
  aria-expanded={expanded}
  aria-controls={`mix-options-${id}`}
  aria-label={`${expanded ? '收起' : '展开'}${label}选项`}
  onClick={() => togglePart(id)}
>
  <h2>{label}</h2>
  {selected && <small>{selected.title}</small>}
  {expanded ? <ChevronUp /> : <ChevronDown />}
</button>
```

Only render `.mix-option-list` when `expanded` is true. Remove the skip option, completion counter, `SkipForward`, `Circle`, and the disabled guard from generation.

- [ ] **Step 3: Preserve selection replacement and submission**

Keep asset buttons inside each expanded card. Selecting a button updates only its part:

```tsx
function decide(part: MixPart, value: string) {
  setDecision((current) => ({ ...current, [part]: value }));
}

function generate() {
  sessionStorage.setItem('makeupMixDecision', JSON.stringify(decision));
  navigate('/mix/generating');
}
```

- [ ] **Step 4: Style collapsed, expanded, and selected states**

Adjust `learning.css` so `.mix-part-card` has compact padding when collapsed, `.mix-part-card.is-expanded` uses the rose border, `.mix-part-toggle` spans the card width without a visible button chrome, and `.mix-option-list` gains its divider and top spacing only when rendered. Do not add visible internal-state labels.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
npm test -- --run src/pages/MixPage.test.tsx src/pages/LearningFlow.test.tsx
```

Expected: both files pass.

- [ ] **Step 6: Commit the behavior change**

```bash
git add src/components/MixEditor.tsx src/styles/learning.css src/pages/MixPage.test.tsx src/pages/LearningFlow.test.tsx
git commit -m "feat: collapse preset mix selectors"
```

### Task 3: Verify the unchanged downstream flow

**Files:**
- Verify: `src/pages/MixGeneratingPage.test.tsx`
- Verify: `src/pages/MixPreviewPage.test.tsx`
- Verify: `src/services/learningService.test.ts`

- [ ] **Step 1: Run the complete automated test suite**

Run:

```bash
npm test -- --run
```

Expected: 19 test files and all tests pass, including loading, result restoration, suitable tutorial routing, and adjustment routing.

- [ ] **Step 2: Run static validation and production build**

Run:

```bash
npm run lint
npm run build
git diff --check
```

Expected: ESLint exits with no warnings, TypeScript/Vite build succeeds, and Git reports no whitespace errors.

- [ ] **Step 3: Verify the development page on port 5174**

Run the existing Vite development command on port 5174 and request the root page:

```bash
npm run dev -- --host 127.0.0.1 --port 5174
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:5174/
```

Expected: Vite reports the 5174 URL and curl prints `200`.
