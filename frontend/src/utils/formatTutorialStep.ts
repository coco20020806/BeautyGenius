import type { TutorialPart, TutorialStep, TutorialVisualLayer } from '../types/makeup';

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

export function formatRangeText(visualLayer: TutorialVisualLayer | undefined): string {
  if (!visualLayer) return '无';
  const parts: string[] = [];
  const position = (visualLayer.position ?? '').trim();
  if (position) parts.push(position);
  const shape = (visualLayer.shape ?? '').trim();
  if (shape) parts.push(shape);
  const color = (visualLayer.color ?? '').trim();
  if (color) parts.push(color);
  return parts.length ? parts.join(' · ') : '无';
}

export function formatTechnique(step: TutorialStep): string {
  const technique = (step.technique ?? '').trim();
  if (technique) return technique;
  return segmentOrNone(step.instruction);
}

export function stepHeading(step: TutorialStep, index: number): string {
  const primary = (step.taxonomy_primary ?? '').trim();
  if (primary) return `步骤 ${index + 1} · ${primary}`;
  return `步骤 ${index + 1} · ${step.step_id}`;
}
