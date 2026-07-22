/** Split picture-makeup final/base prompt into technique vs annotation. */

const ANNOTATION_MARKER =
  /[，,]?\s*请在原始图片上用色块标注(?:着色范围|作用区域)/;

export function splitDiagramPrompt(finalPrompt: string): {
  technique: string;
  annotation: string | null;
} {
  const text = (finalPrompt ?? '').trim();
  if (!text) {
    return { technique: '', annotation: null };
  }

  const match = ANNOTATION_MARKER.exec(text);
  if (!match || match.index === undefined) {
    return { technique: text, annotation: null };
  }

  const technique = text.slice(0, match.index).trim();
  const annotation = text.slice(match.index).replace(/^[，,]\s*/, '').trim();
  return {
    technique: technique || text,
    annotation: annotation || null,
  };
}
