import { ArrowLeft, BookOpenCheck, Check, ChevronRight, Clock3, Film, Layers3, PackageOpen, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FaceLayers } from '../components/FaceLayers';
import { MobileShell } from '../components/MobileShell';
import { canPlaySourceVideo, StepClipPlayer } from '../components/StepClipPlayer';
import { learningService } from '../services/learningService';
import type { IllustratedTutorial, TutorialMode } from '../types/learning';

export function TutorialPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const routeState = location.state as { from?: string; tutorialId?: string } | null;
  const returnTo = routeState?.from ?? '/preview';
  const [tutorial, setTutorial] = useState<IllustratedTutorial | null>(null);
  const [stepIndex, setStepIndex] = useState(0);
  const [mode, setMode] = useState<TutorialMode>('beginner');
  const [videoOpen, setVideoOpen] = useState(false);

  useEffect(() => {
    setVideoOpen(false);
    void learningService.getTutorial(routeState?.tutorialId).then(setTutorial);
  }, [routeState?.tutorialId]);

  if (!tutorial) {
    return (
      <MobileShell>
        <div className="preview-loading">
          <Sparkles className="spin" />
          <p>正在准备图示教程…</p>
        </div>
      </MobileShell>
    );
  }

  const step = tutorial.steps[stepIndex];
  const hasDiagram = Boolean(step.diagramImage);
  const canPlayVideo = canPlaySourceVideo(tutorial.videoUrl);

  return (
    <MobileShell className="learning-page tutorial-page">
      <header className="detail-header">
        <button className="icon-button" type="button" aria-label="返回" onClick={() => navigate(returnTo)}>
          <ArrowLeft size={21} />
        </button>
        <div>
          <span className="page-kicker">ILLUSTRATED GUIDE</span>
          <h1>图示教程</h1>
        </div>
        <button className="icon-button" type="button" aria-label="保存教程">
          <BookOpenCheck size={20} />
        </button>
      </header>

      <section className="tutorial-title-card">
        <div>
          <h2>{tutorial.title}</h2>
          <p>
            <span>{tutorial.difficulty}</span>
            <span>
              <Clock3 size={13} />
              {tutorial.duration}
            </span>
          </p>
        </div>
        <div className="mode-switch" role="group" aria-label="教程模式">
          <button type="button" className={mode === 'beginner' ? 'is-active' : ''} onClick={() => setMode('beginner')}>
            新手
          </button>
          <button type="button" className={mode === 'skilled' ? 'is-active' : ''} onClick={() => setMode('skilled')}>
            熟练
          </button>
        </div>
      </section>

      <section className="face-guide-card">
        {hasDiagram ? (
          <img className="collected-diagram-image" src={step.diagramImage} alt={`${step.title} 示例图`} />
        ) : (
          <FaceLayers activePart={step.part} color={step.color} />
        )}
        <div className="current-layer">
          <Layers3 size={15} />
          <span>当前图层</span>
          <strong>{step.title}</strong>
        </div>
      </section>

      <section className="timeline-section" aria-labelledby="timeline-title">
        <div className="section-heading">
          <h2 id="timeline-title">步骤进度</h2>
          <span>
            {stepIndex + 1}/{tutorial.steps.length}
          </span>
        </div>
        <div className="step-timeline">
          {tutorial.steps.map((item, index) => (
            <button
              type="button"
              key={item.id}
              className={index === stepIndex ? 'is-active' : index < stepIndex ? 'is-completed' : ''}
              aria-label={`${item.order}. ${item.title}`}
              onClick={() => setStepIndex(index)}
            >
              <span>{index < stepIndex ? <Check size={12} /> : item.order}</span>
              <small>{item.title}</small>
            </button>
          ))}
        </div>
      </section>

      <section className="step-detail-card">
        <span className="step-number">STEP {String(step.order).padStart(2, '0')}</span>
        <h2>{step.title}</h2>
        {mode === 'beginner' && <p>{step.instruction}</p>}
        <div className="product-row">
          <span>
            <PackageOpen size={17} />
          </span>
          <div>
            <small>使用产品</small>
            <strong>{step.product}</strong>
          </div>
          <i style={{ backgroundColor: step.color }} />
        </div>
        {mode === 'beginner' && (
          <div className="expert-tip">
            <Sparkles size={14} />
            <span>{step.expertTip}</span>
          </div>
        )}
        <button
          className="slice-button"
          type="button"
          disabled={!canPlayVideo}
          onClick={() => {
            if (canPlayVideo) setVideoOpen(true);
          }}
        >
          <Film size={16} />
          <span>查看原视频切片</span>
          <small>{step.videoSlice}</small>
          <ChevronRight size={15} />
        </button>
      </section>

      {videoOpen && tutorial.videoUrl ? (
        <StepClipPlayer
          open={videoOpen}
          videoUrl={tutorial.videoUrl}
          title={step.title}
          onClose={() => setVideoOpen(false)}
        />
      ) : null}
    </MobileShell>
  );
}
