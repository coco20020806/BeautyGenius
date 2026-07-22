import { ArrowLeft, ImageIcon, Play, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';
import { canPlayStepClip, StepClipPlayer } from '../components/StepClipPlayer';
import { makeupService } from '../services/makeupService';
import type { StepDiagramItem, StepDiagramsResponse } from '../types/makeup';

function readTaskId() {
  try {
    return JSON.parse(sessionStorage.getItem('makeupTask') ?? '{}').taskId ?? null;
  } catch {
    return null;
  }
}

function diagramStepDomId(stepId: string) {
  return `diagram-step-${stepId}`;
}

function sortDiagramSteps(steps: StepDiagramItem[]) {
  return [...steps].sort((a, b) => a.index - b.index);
}

export function StepDiagramsPage() {
  const navigate = useNavigate();
  const taskId = readTaskId();
  const [data, setData] = useState<StepDiagramsResponse | null>(null);
  const [error, setError] = useState('');
  const [activeItem, setActiveItem] = useState<StepDiagramItem | null>(null);
  const [activeStepId, setActiveStepId] = useState<string | null>(null);

  const sortedSteps = data?.steps?.length ? sortDiagramSteps(data.steps) : [];

  useEffect(() => {
    if (!taskId) {
      setError('缺少任务，请从跟练页进入');
      return;
    }
    let cancelled = false;
    let timer: ReturnType<typeof setInterval> | null = null;

    const poll = async () => {
      try {
        const doc = await makeupService.getStepDiagrams(taskId);
        if (cancelled) return;
        setData(doc);
        setError('');
        if (doc.status === 'completed' || doc.status === 'failed') {
          if (timer) clearInterval(timer);
        }
      } catch (reason) {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : '示例图加载失败');
      }
    };

    void (async () => {
      try {
        await makeupService.startStepDiagrams(taskId);
      } catch {
        /* GET may still work if job already running */
      }
      await poll();
      timer = setInterval(() => void poll(), 1500);
    })();

    return () => {
      cancelled = true;
      if (timer) clearInterval(timer);
    };
  }, [taskId]);

  useEffect(() => {
    if (!sortedSteps.length) {
      setActiveStepId(null);
      return;
    }

    const steps = sortedSteps;
    setActiveStepId((current) => current ?? steps[0].stepId);

    if (typeof IntersectionObserver === 'undefined') return;

    const ratios = new Map<string, number>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const stepId = entry.target.getAttribute('data-step-id');
          if (!stepId) continue;
          ratios.set(stepId, entry.isIntersecting ? entry.intersectionRatio : 0);
        }
        let bestId: string | null = null;
        let bestRatio = 0;
        for (const step of steps) {
          const ratio = ratios.get(step.stepId) ?? 0;
          if (ratio > bestRatio) {
            bestRatio = ratio;
            bestId = step.stepId;
          }
        }
        if (bestId) setActiveStepId(bestId);
      },
      { rootMargin: '-12% 0px -45% 0px', threshold: [0, 0.25, 0.4, 0.6, 1] },
    );

    for (const step of steps) {
      const node = document.getElementById(diagramStepDomId(step.stepId));
      if (node) observer.observe(node);
    }

    return () => observer.disconnect();
  }, [data?.steps]);

  const jumpToStep = (stepId: string) => {
    const node = document.getElementById(diagramStepDomId(stepId));
    if (!node) return;
    setActiveStepId(stepId);
    node.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const processing = data?.status === 'processing' || data?.status === 'idle';
  const progress = data?.progress;

  return (
    <MobileShell className="practice-page diagram-gallery-page">
      <header className="detail-header">
        <button
          className="icon-button"
          type="button"
          aria-label="返回跟练"
          onClick={() => navigate('/practice')}
        >
          <ArrowLeft size={21} />
        </button>
        <div>
          <span className="page-kicker">STEP DIAGRAMS</span>
          <h1>步骤示例图</h1>
        </div>
        <span className="header-spacer" />
      </header>

      {error ? (
        <section className="analysis-error" role="alert">
          <p>{error}</p>
        </section>
      ) : null}

      {processing && !data?.steps?.length ? (
        <div className="preview-loading">
          <Sparkles className="spin" size={26} />
          <p>正在生成步骤示例图…</p>
          {progress && progress.total > 0 ? (
            <p className="diagram-progress">
              {progress.done}/{progress.total} 步
            </p>
          ) : null}
        </div>
      ) : null}

      {data?.failureReason ? (
        <section className="analysis-error" role="alert">
          <p>{data.failureReason}</p>
        </section>
      ) : null}

      {sortedSteps.length ? (
        <>
          {processing && progress && progress.total > 0 ? (
            <p className="diagram-progress-banner" role="status">
              生成中 {progress.done}/{progress.total} 步…
            </p>
          ) : null}
          <div className="diagram-gallery-layout">
            <ul className="diagram-gallery" aria-label="步骤示例图列表">
              {sortedSteps.map((item) => {
                const playable = canPlayStepClip(data?.videoUrl, item.videoClip);
                return (
                  <li
                    key={item.stepId}
                    id={diagramStepDomId(item.stepId)}
                    data-step-id={item.stepId}
                    className="diagram-card"
                  >
                    <h2>{item.heading}</h2>
                    <div className="diagram-card__media">
                      {item.imageUrl ? (
                        <img src={item.imageUrl} alt={`${item.heading} 着色范围示意`} loading="lazy" />
                      ) : (
                        <div
                          className={`diagram-card__placeholder${item.status === 'failed' ? ' is-error' : ''}`}
                          role={item.status === 'failed' ? 'alert' : undefined}
                        >
                          <ImageIcon size={32} />
                          {item.status === 'pending' ? (
                            <span>生成中…</span>
                          ) : item.status === 'failed' ? (
                            <>
                              <span>生成失败</span>
                              {item.error ? <p className="diagram-card__error">{item.error}</p> : null}
                            </>
                          ) : (
                            <span>暂无图示</span>
                          )}
                        </div>
                      )}
                    </div>
                    {item.finalPrompt ? (
                      <details className="diagram-card__prompt">
                        <summary>标注说明</summary>
                        <p>{item.finalPrompt}</p>
                      </details>
                    ) : null}
                    <button
                      className="step-clip-trigger"
                      type="button"
                      disabled={!playable}
                      onClick={() => setActiveItem(item)}
                    >
                      <Play size={14} />
                      看视频
                    </button>
                  </li>
                );
              })}
            </ul>

            <nav className="diagram-step-index" aria-label="步骤索引">
              {sortedSteps.map((item) => {
                const label = String(item.index + 1);
                const isActive = activeStepId === item.stepId;
                return (
                  <button
                    key={item.stepId}
                    type="button"
                    className={`diagram-step-index__btn${isActive ? ' is-active' : ''}`}
                    aria-label={`跳转到步骤 ${label}`}
                    aria-current={isActive ? 'true' : undefined}
                    onClick={() => jumpToStep(item.stepId)}
                  >
                    {label}
                  </button>
                );
              })}
            </nav>
          </div>

          {activeItem && data?.videoUrl && activeItem.videoClip ? (
            <StepClipPlayer
              open
              videoUrl={data.videoUrl}
              clip={activeItem.videoClip}
              title={activeItem.heading}
              onClose={() => setActiveItem(null)}
            />
          ) : null}
        </>
      ) : null}
    </MobileShell>
  );
}
