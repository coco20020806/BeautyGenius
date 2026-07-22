import { ArrowLeft, ImageIcon, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';
import { makeupService } from '../services/makeupService';
import type { StepDiagramsResponse } from '../types/makeup';

function readTaskId() {
  try {
    return JSON.parse(sessionStorage.getItem('makeupTask') ?? '{}').taskId ?? null;
  } catch {
    return null;
  }
}

export function StepDiagramsPage() {
  const navigate = useNavigate();
  const taskId = readTaskId();
  const [data, setData] = useState<StepDiagramsResponse | null>(null);
  const [error, setError] = useState('');

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

      {data?.steps?.length ? (
        <>
          {processing && progress && progress.total > 0 ? (
            <p className="diagram-progress-banner" role="status">
              生成中 {progress.done}/{progress.total} 步…
            </p>
          ) : null}
          <ul className="diagram-gallery" aria-label="步骤示例图列表">
            {data.steps.map((item) => (
              <li key={item.stepId} className="diagram-card">
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
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </MobileShell>
  );
}
