import { ArrowLeft, ListOrdered, Play, Sparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';
import { canPlayStepClip, StepClipPlayer } from '../components/StepClipPlayer';
import { makeupService } from '../services/makeupService';
import type { Tutorial, TutorialStep } from '../types/makeup';
import {
  formatProductLine,
  formatRangeText,
  formatTechnique,
  groupHeading,
  resolveTutorialGroups,
  stepSegmentTitle,
} from '../utils/formatTutorialStep';

type LoadState = 'loading' | 'ready' | 'empty' | 'error';

function readTaskId() {
  try {
    return JSON.parse(sessionStorage.getItem('makeupTask') ?? '{}').taskId ?? null;
  } catch {
    return null;
  }
}

export function PracticePage() {
  const navigate = useNavigate();
  const taskId = readTaskId();
  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [loadState, setLoadState] = useState<LoadState>(taskId ? 'loading' : 'empty');
  const [errorMessage, setErrorMessage] = useState('');
  const [activeStep, setActiveStep] = useState<{
    step: TutorialStep;
    title: string;
  } | null>(null);

  const resolvedGroups = useMemo(
    () => (tutorial ? resolveTutorialGroups(tutorial) : []),
    [tutorial],
  );

  useEffect(() => {
    if (!taskId) {
      setLoadState('empty');
      return;
    }
    let cancelled = false;
    void makeupService
      .getTutorial(taskId)
      .then((doc) => {
        if (cancelled) return;
        if (!doc.steps?.length) {
          setLoadState('empty');
          return;
        }
        setTutorial(doc);
        setLoadState('ready');
      })
      .catch((reason) => {
        if (cancelled) return;
        setErrorMessage(reason instanceof Error ? reason.message : '教程暂时无法加载');
        setLoadState('error');
      });
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  return (
    <MobileShell className="practice-page">
      <header className="detail-header">
        <button
          className="icon-button"
          type="button"
          aria-label="返回"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft size={21} />
        </button>
        <div>
          <span className="page-kicker">FOLLOW ALONG</span>
          <h1>跟练教程</h1>
        </div>
        <span className="header-spacer" />
      </header>

      {loadState === 'loading' ? (
        <div className="preview-loading">
          <Sparkles className="spin" size={26} />
          <p>正在加载视频解读步骤…</p>
        </div>
      ) : null}

      {loadState === 'empty' ? (
        <section className="placeholder-card" aria-labelledby="practice-empty-title">
          <span>
            <ListOrdered size={28} />
          </span>
          <h2 id="practice-empty-title">暂无跟练教程</h2>
          <p>请先上传教程视频并完成适配预览，再点击「适合我」进入跟练。</p>
          <button className="primary-button" type="button" onClick={() => navigate('/')}>
            去上传教程
          </button>
        </section>
      ) : null}

      {loadState === 'error' ? (
        <section className="analysis-error" role="alert">
          <p>{errorMessage || '教程暂时无法加载'}</p>
          <button className="primary-button" type="button" onClick={() => navigate('/preview')}>
            返回适配预览
          </button>
        </section>
      ) : null}

      {loadState === 'ready' && tutorial ? (
        <>
          <section className="makeup-summary" aria-labelledby="tutorial-title">
            <div className="summary-heading">
              <div>
                <span className="section-eyebrow">视频解读</span>
                <h2 id="tutorial-title">{tutorial.title}</h2>
              </div>
            </div>
            <p className="tutorial-intro">按视频步骤使用对应产品、范围与手法跟练。</p>
          </section>

          <ol className="tutorial-step-list" aria-label="教程步骤">
            {resolvedGroups.map(({ group, steps }) => (
              <li key={group.group_id} className="tutorial-step-card">
                <h3>{groupHeading(group)}</h3>
                <div className="tutorial-step-segments">
                  {steps.map((step) => {
                    const playable = canPlayStepClip(tutorial.videoUrl, step.video_clip);
                    const multi = steps.length > 1;
                    return (
                      <div key={step.step_id} className="tutorial-step-segment">
                        {multi ? (
                          <h4 className="tutorial-step-segment__title">{stepSegmentTitle(step)}</h4>
                        ) : null}
                        <dl className="tutorial-step-fields">
                          <div>
                            <dt>产品</dt>
                            <dd>{formatProductLine(step)}</dd>
                          </div>
                          <div>
                            <dt>范围</dt>
                            <dd>{formatRangeText(step.visual_layer)}</dd>
                          </div>
                          <div>
                            <dt>手法</dt>
                            <dd>{formatTechnique(step)}</dd>
                          </div>
                        </dl>
                        <button
                          className="step-clip-trigger"
                          type="button"
                          disabled={!playable}
                          onClick={() =>
                            setActiveStep({
                              step,
                              title: multi
                                ? `${groupHeading(group)} · ${stepSegmentTitle(step)}`
                                : groupHeading(group),
                            })
                          }
                        >
                          <Play size={14} />
                          看视频
                        </button>
                      </div>
                    );
                  })}
                </div>
              </li>
            ))}
          </ol>

          <section className="practice-footer" aria-label="跟练下一步">
            <button
              className="primary-button practice-footer__cta"
              type="button"
              onClick={() => navigate('/practice/examples')}
            >
              前往示例图
            </button>
          </section>

          {activeStep && tutorial.videoUrl ? (
            <StepClipPlayer
              open
              videoUrl={tutorial.videoUrl}
              clip={activeStep.step.video_clip}
              title={activeStep.title}
              onClose={() => setActiveStep(null)}
            />
          ) : null}
        </>
      ) : null}
    </MobileShell>
  );
}
