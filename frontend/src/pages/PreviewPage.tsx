import { ArrowLeft, Check, Clock3, RotateCcw, SlidersHorizontal, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BeforeAfterSlider } from '../components/BeforeAfterSlider';
import { MobileShell } from '../components/MobileShell';
import { makeupService } from '../services/makeupService';
import type { MakeupIntensityLevel, MakeupPreview } from '../types/makeup';

const DEFAULT_INTENSITY_LEVELS: MakeupIntensityLevel[] = [
  { id: 'L1', color: '#ead6cf', opacity: 0.2 },
  { id: 'L2', color: '#d8aaa0', opacity: 0.4 },
  { id: 'L3', color: '#b87870', opacity: 0.6 },
  { id: 'L4', color: '#8e554f', opacity: 0.8 },
  { id: 'L5', color: '#5c3a36', opacity: 1.0 },
];

const DEFAULT_INTENSITY_ID = 'L4';

function taskId() {
  try { return JSON.parse(sessionStorage.getItem('makeupTask') ?? '{}').taskId ?? 'demo-task'; }
  catch { return 'demo-task'; }
}

export function PreviewPage() {
  const navigate = useNavigate();
  const [preview, setPreview] = useState<MakeupPreview | null>(null);
  const [intensityId, setIntensityId] = useState(DEFAULT_INTENSITY_ID);

  useEffect(() => { void makeupService.getPreview(taskId()).then(setPreview); }, []);

  const intensityLevels = preview?.intensityLevels?.length
    ? preview.intensityLevels
    : DEFAULT_INTENSITY_LEVELS;
  const activeLevel =
    intensityLevels.find((level) => level.id === intensityId) ??
    intensityLevels.find((level) => level.id === DEFAULT_INTENSITY_ID) ??
    intensityLevels[intensityLevels.length - 1];

  const generationFailed = Boolean(
    preview && (preview.generationFailed || !preview.afterImage),
  );
  const failureReason =
    preview?.generationFailureReason
    ?? '妆容生成失败，暂无适配预览';

  return (
    <MobileShell className="preview-page">
      <header className="detail-header">
        <button className="icon-button" type="button" aria-label="返回" onClick={() => navigate('/', { replace: true })}><ArrowLeft size={21} /></button>
        <div><span className="page-kicker">YOUR MAKEUP MATCH</span><h1>适配预览</h1></div>
        <span className="header-spacer" />
      </header>

      {preview ? (
        <>
          {generationFailed ? (
            <section className="preview-generation-error" aria-label="妆容生成失败">
              <RotateCcw size={26} />
              <h2>妆容生成失败</h2>
              <p>{failureReason}</p>
              <button className="primary-button" type="button" onClick={() => navigate('/', { replace: true })}>
                重新上传
              </button>
            </section>
          ) : (
            <BeforeAfterSlider
              beforeSrc={preview.beforeImage}
              afterSrc={preview.afterImage!}
              frameAspectRatio={
                preview.comparison
                  ? preview.comparison.width / preview.comparison.height
                  : undefined
              }
              objectPosition={preview.comparison?.objectPosition}
              afterOpacity={activeLevel?.opacity ?? 0.8}
            />
          )}

          <section className="makeup-summary" aria-labelledby="summary-title">
            <div className="summary-heading"><div><span className="section-eyebrow">解析妆容</span><h2 id="summary-title">{preview.title}</h2></div><span className="difficulty-pill">{preview.difficulty}</span></div>
            {!generationFailed && (
              <div className="palette" role="group" aria-label="妆容浓淡">
                {intensityLevels.map((level) => (
                  <button
                    key={level.id}
                    type="button"
                    className={level.id === activeLevel?.id ? 'is-active' : undefined}
                    style={{ backgroundColor: level.color }}
                    aria-label={`妆容浓淡 ${level.id}`}
                    aria-pressed={level.id === activeLevel?.id}
                    title={`妆容浓淡 ${Math.round(level.opacity * 100)}%`}
                    onClick={() => setIntensityId(level.id)}
                  />
                ))}
              </div>
            )}
            <div className="summary-meta"><span><Sparkles size={14} />{preview.style}</span><span><Clock3 size={14} />{preview.duration}</span><span>{preview.occasion}</span></div>
          </section>

          <section className="adaptation-section" aria-labelledby="adapt-title">
            <div className="section-heading"><h2 id="adapt-title">关键适配提示</h2><span>为你调整</span></div>
            <div className="hint-list">
              {preview.hints.map((hint) => (
                <article className={`hint-card tone-${hint.tone}`} key={hint.title}>
                  <span>{hint.tone === 'positive' ? <Check size={16} /> : hint.tone === 'adjust' ? <SlidersHorizontal size={16} /> : <Sparkles size={16} />}</span>
                  <div><h3>{hint.title}</h3><p>{hint.description}</p></div>
                </article>
              ))}
            </div>
          </section>

          {!generationFailed && (
            <section className="decision-card" aria-label="妆容适配判断">
              <h2>这个妆适合你吗？</h2>
              <p>你的选择会帮助我们继续优化教程</p>
              <div className="decision-actions">
                <button
                  type="button"
                  className="is-positive"
                  onClick={() => {
                    try {
                      const raw = sessionStorage.getItem('makeupTask');
                      const parsed = raw ? JSON.parse(raw) as { taskId?: string } : {};
                      sessionStorage.setItem(
                        'makeupTask',
                        JSON.stringify({ ...parsed, suitability: 'accepted' }),
                      );
                    } catch {
                      /* ignore */
                    }
                    navigate('/practice');
                  }}
                >
                  <Check size={17} />
                  适合我
                </button>
                <button
                  type="button"
                  onClick={() => {
                    try {
                      const raw = sessionStorage.getItem('makeupTask');
                      const parsed = raw ? JSON.parse(raw) as { taskId?: string } : {};
                      sessionStorage.setItem(
                        'makeupTask',
                        JSON.stringify({ ...parsed, suitability: 'adjust' }),
                      );
                    } catch {
                      /* ignore */
                    }
                    navigate('/adjust');
                  }}
                >
                  <SlidersHorizontal size={17} />
                  需要微调
                </button>
              </div>
            </section>
          )}
        </>
      ) : <div className="preview-loading"><Sparkles className="spin" size={26} /><p>正在生成你的适配效果…</p></div>}
    </MobileShell>
  );
}
