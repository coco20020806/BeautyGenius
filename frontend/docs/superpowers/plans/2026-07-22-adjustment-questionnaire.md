# Adjustment Questionnaire Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current makeup adjustment questions with the approved three-section questionnaire without changing the established visual or navigation behavior.

**Architecture:** Model multi-select answers as arrays and skin type as a scalar in `AdjustmentRequest`. Reuse the existing choice-card components and submit through `LearningService.saveAdjustment`, then keep navigating to the generated tutorial by ID.

**Tech Stack:** React, TypeScript, CSS, Vitest, Testing Library

---

### Task 1: Define questionnaire behavior with tests

**Files:**
- Modify: `src/pages/AdjustPage.test.tsx`
- Modify: `src/services/learningService.test.ts`

- [ ] Assert all three section headings and representative multi-select/single-select controls.
- [ ] Assert old questions and free-text input are absent.
- [ ] Assert multiple choices can be submitted and persisted using the new request shape.
- [ ] Run focused tests and confirm they fail for the missing questionnaire.

### Task 2: Implement the questionnaire and request contract

**Files:**
- Modify: `src/pages/AdjustPage.tsx`
- Modify: `src/types/learning.ts`
- Modify: `src/services/learningService.ts`

- [ ] Replace old state with the six approved answer groups.
- [ ] Render the three sections using the existing `choice-section` and `choice-chip` styles.
- [ ] Preserve submit loading state and tutorial navigation.
- [ ] Update local tutorial naming and session storage to use the new request.
- [ ] Run focused tests and confirm they pass.

### Task 3: Document and verify

**Files:**
- Modify: `docs/backend-integration.md`

- [ ] Replace the adjustment request example and field documentation with the new contract.
- [ ] Run all tests, build, lint, and `git diff --check`.
- [ ] Commit the verified changes to the feature branch.
