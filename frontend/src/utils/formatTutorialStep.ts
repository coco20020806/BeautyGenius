import type { Tutorial, TutorialStep, TutorialStepGroup, TutorialPart } from '../types/makeup';

const PART_LABELS: Record<TutorialPart, string> = {
  prep: '妆前',
  base: '底妆',
  concealer: '遮瑕',
  set: '定妆',
  brow: '眉毛',
  eye: '眼睛',
  contour: '修容',
  highlight: '高光',
  cheek: '腮红',
  lip: '唇妆',
  other: '其他',
};

function segmentOrNone(value: string | undefined | null): string {
  const trimmed = (value ?? '').trim();
  return trimmed ? trimmed : '无';
}

/** Prefer LLM display_product; else specific name > keyword > category. Single field only. */
export function formatProductLine(step: TutorialStep): string {
  const display = (step.display_product ?? '').trim();
  if (display) return display;

  const name = (step.product?.name ?? '').trim();
  if (name && name !== 'unknown') return name;

  const fromField = (step.product as { description?: string } | undefined)?.description?.trim();
  if (fromField) return fromField;
  const kw = step.product?.keywords?.[0];
  if (typeof kw === 'string' && kw.trim() && kw.trim().length > 1) {
    // Skip ultra-weak tokens like 霜 alone when we can fall back to category
    const weakOnly = kw.trim().length <= 2;
    if (!weakOnly) return kw.trim();
  }

  const primary = (step.taxonomy_primary ?? '').trim();
  if (primary) return primary;
  const part = step.part;
  if (part && PART_LABELS[part]) return PART_LABELS[part];
  if (typeof kw === 'string' && kw.trim()) return kw.trim();
  return '无';
}

/** Prefer LLM display_range; else position only — never append raw shape/color tokens. */
export function formatRangeText(step: TutorialStep | undefined): string {
  if (!step) return '无';
  const display = (step.display_range ?? '').trim();
  if (display) return display;
  const position = (step.visual_layer?.position ?? '').trim();
  return position || '无';
}

export function formatTechnique(step: TutorialStep): string {
  const technique = (step.technique ?? '').trim();
  if (technique) return technique;
  return segmentOrNone(step.instruction);
}

/** Flat-step heading (diagrams / legacy). Prefer display_title. */
export function stepHeading(step: TutorialStep, index: number): string {
  const display = (step.display_title ?? '').trim();
  if (display) return `步骤 ${index + 1} · ${display}`;
  const primary = (step.taxonomy_primary ?? '').trim();
  if (primary) return `步骤 ${index + 1} · ${primary}`;
  return `步骤 ${index + 1} · ${step.step_id}`;
}

export function groupHeading(group: TutorialStepGroup): string {
  const title = (group.title ?? '').trim() || '步骤';
  return `步骤 ${group.index} · ${title}`;
}

export function stepSegmentTitle(step: TutorialStep): string {
  const display = (step.display_title ?? '').trim();
  if (display) return display;
  return (step.taxonomy_primary ?? '').trim() || step.step_id;
}

export interface ResolvedTutorialGroup {
  group: TutorialStepGroup;
  steps: TutorialStep[];
}

/** Prefer tutorial.step_groups; fall back to one group per flat step. */
export function resolveTutorialGroups(tutorial: Tutorial): ResolvedTutorialGroup[] {
  const byId = new Map(tutorial.steps.map((s) => [s.step_id, s]));
  const groups = tutorial.step_groups;
  if (groups?.length) {
    return groups.map((group) => ({
      group,
      steps: group.step_ids.map((id) => byId.get(id)).filter((s): s is TutorialStep => Boolean(s)),
    }));
  }
  return tutorial.steps.map((step, index) => ({
    group: {
      group_id: `group_${String(index + 1).padStart(2, '0')}`,
      title: (step.taxonomy_primary ?? '').trim() || step.step_id,
      index: index + 1,
      step_ids: [step.step_id],
    },
    steps: [step],
  }));
}
