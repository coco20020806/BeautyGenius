import {
  ArrowLeft,
  Check,
  ChevronRight,
  Clock3,
  Film,
  Layers3,
  PackageOpen,
  Play,
  SlidersHorizontal,
  Sparkles,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import faceAfter from '../assets/face-after.svg';
import faceBefore from '../assets/face-before.svg';
import { BeforeAfterSlider } from '../components/BeforeAfterSlider';
import { FaceLayers } from '../components/FaceLayers';
import { MobileShell } from '../components/MobileShell';
import { canPlayStepClip, StepClipPlayer } from '../components/StepClipPlayer';
import { learningService } from '../services/learningService';
import type { CollectedSampleDetail } from '../types/learning';
import type { TutorialStep as PracticeTutorialStep } from '../types/makeup';
import {
  formatProductLine,
  formatRangeText,
  formatTechnique,
  groupHeading,
  resolveTutorialGroups,
  stepSegmentTitle,
} from '../utils/formatTutorialStep';

const INTENSITY_LEVELS = [
  { id: 'L1', color: '#ead6cf', opacity: 0.2 },
  { id: 'L2', color: '#d8aaa0', opacity: 0.4 },
  { id: 'L3', color: '#b87870', opacity: 0.6 },
  { id: 'L4', color: '#8e554f', opacity: 0.8 },
  { id: 'L5', color: '#5c3a36', opacity: 1.0 },
];

export function CollectedTutorialPage() {
  const navigate = useNavigate();
  const { assetId = '' } = useParams<{ assetId: string }>();
  const [sample, setSample] = useState<CollectedSampleDetail | null | undefined>(undefined);
  const [intensityId, setIntensityId] = useState('L4');
  const [stepIndex, setStepIndex] = useState(0);
  const [activeClip, setActiveClip] = useState<{
    step: PracticeTutorialStep;
    title: string;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    void learningService.getCollectedSample(assetId).then((detail) => {
      if (cancelled) return;
      if (!detail) {
        navigate('/library', { replace: true });
        return;
      }
      setSample(detail);
    });
    return () => {
      cancelled = true;
    };
  }, [assetId, navigate]);

  const practiceGroups = useMemo(
    () => (sample ? resolveTutorialGroups(sample.practiceTutorial) : []),
    [sample],
  );

  const practiceStepById = useMemo(() => {
    if (!sample) return new Map<string, PracticeTutorialStep>();
    return new Map(sample.practiceTutorial.steps.map((item) => [item.step_id, item]));
  }, [sample]);

  if (sample === undefined) {
    return (
      <MobileShell className="learning-page collected-detail-page">
        <div className="preview-loading">
          <Sparkles className="spin" />
          <p>正在准备收藏详情…</p>
        </div>
      </MobileShell>
    );
  }

  if (!sample) return null;

  const hasRealPreview = Boolean(sample.beforeImage && sample.afterImage);
  const activeLevel = INTENSITY_LEVELS.find((level) => level.id === intensityId) ?? INTENSITY_LEVELS[3];
  const step = sample.illustratedSteps[stepIndex];
  const hasDiagram = Boolean(step.diagramImage);
  const hasRealPractice = sample.practiceTutorial.tutorial_id.startsWith('tutorial_');
  const illustratedPracticeStep = practiceStepById.get(step.id);
  const illustratedClipPlayable = canPlayStepClip(
    sample.practiceTutorial.videoUrl,
    illustratedPracticeStep?.video_clip,
  );

  return (
    <MobileShell className="learning-page collected-detail-page">
      <header className="detail-header">
        <button className="icon-button" type="button" aria-label="返回" onClick={() => navigate('/library')}>
          <ArrowLeft size={21} />
        </button>
        <div>
          <span className="page-kicker">ARCHIVED LOOK</span>
          <h1>{sample.title}</h1>
        </div>
        <span className="header-spacer" />
      </header>

      <section className="collected-section" aria-labelledby="collected-preview-title">
        <div className="section-heading">
          <h2 id="collected-preview-title">妆容预览</h2>
          <span>{hasRealPreview ? '真实解析' : '占位'}</span>
        </div>
        <div className="collected-preview-frame">
          <BeforeAfterSlider
            beforeSrc={sample.beforeImage ?? faceBefore}
            afterSrc={sample.afterImage ?? faceAfter}
            afterOpacity={activeLevel.opacity}
            frameAspectRatio={
              sample.comparison ? sample.comparison.width / sample.comparison.height : undefined
            }
            objectPosition={sample.comparison?.objectPosition}
          />
          {!hasRealPreview ? (
            <p className="collected-placeholder-note">对比图为结构占位，待接入真实解析妆前/妆后</p>
          ) : null}
        </div>
        <section className="makeup-summary" aria-labelledby="collected-summary-title">
          <div className="summary-heading">
            <div>
              <span className="section-eyebrow">解析妆容</span>
              <h2 id="collected-summary-title">{sample.previewTitle}</h2>
            </div>
            <span className="difficulty-pill">{sample.difficulty}</span>
          </div>
          <div className="palette" role="group" aria-label="妆容浓淡">
            {INTENSITY_LEVELS.map((level) => (
              <button
                key={level.id}
                type="button"
                className={level.id === activeLevel.id ? 'is-active' : undefined}
                style={{ backgroundColor: level.color }}
                aria-label={`妆容浓淡 ${level.id}`}
                aria-pressed={level.id === activeLevel.id}
                onClick={() => setIntensityId(level.id)}
              />
            ))}
          </div>
          <div className="summary-meta">
            <span>
              <Sparkles size={14} />
              {sample.style}
            </span>
            <span>
              <Clock3 size={14} />
              {sample.duration}
            </span>
            <span>{sample.occasion}</span>
          </div>
        </section>
        <section className="adaptation-section" aria-labelledby="collected-adapt-title">
          <div className="section-heading">
            <h2 id="collected-adapt-title">关键适配提示</h2>
            <span>{hasRealPreview ? '为你调整' : '占位'}</span>
          </div>
          <div className="hint-list">
            {sample.hints.map((hint) => (
              <article className={`hint-card tone-${hint.tone}`} key={hint.title}>
                <span>
                  {hint.tone === 'positive' ? (
                    <Check size={16} />
                  ) : hint.tone === 'adjust' ? (
                    <SlidersHorizontal size={16} />
                  ) : (
                    <Sparkles size={16} />
                  )}
                </span>
                <div>
                  <h3>{hint.title}</h3>
                  <p>{hint.description}</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </section>

      <section className="collected-section" aria-labelledby="collected-practice-title">
        <div className="section-heading">
          <h2 id="collected-practice-title">跟练步骤</h2>
          <span>{hasRealPractice ? '产品 · 范围 · 手法' : '占位'}</span>
        </div>
        {!hasRealPractice ? (
          <p className="collected-placeholder-note">示例结构 · 待接入真实解析</p>
        ) : null}
        <p className="tutorial-intro collected-practice-intro">按视频步骤使用对应产品、范围与手法跟练。</p>
        <ol className="tutorial-step-list" aria-label="教程步骤">
          {practiceGroups.map(({ group, steps }) => (
            <li key={group.group_id} className="tutorial-step-card">
              <h3>{groupHeading(group)}</h3>
              <div className="tutorial-step-segments">
                {steps.map((practiceStep) => {
                  const multi = steps.length > 1;
                  const playable = canPlayStepClip(sample.practiceTutorial.videoUrl, practiceStep.video_clip);
                  return (
                    <div key={practiceStep.step_id} className="tutorial-step-segment">
                      {multi ? (
                        <h4 className="tutorial-step-segment__title">{stepSegmentTitle(practiceStep)}</h4>
                      ) : null}
                      <dl className="tutorial-step-fields">
                        <div>
                          <dt>产品</dt>
                          <dd>{formatProductLine(practiceStep)}</dd>
                        </div>
                        <div>
                          <dt>范围</dt>
                          <dd>{formatRangeText(practiceStep.visual_layer)}</dd>
                        </div>
                        <div>
                          <dt>手法</dt>
                          <dd>{formatTechnique(practiceStep)}</dd>
                        </div>
                      </dl>
                      <button
                        className="step-clip-trigger"
                        type="button"
                        disabled={!playable}
                        onClick={() =>
                          setActiveClip({
                            step: practiceStep,
                            title: multi
                              ? `${groupHeading(group)} · ${stepSegmentTitle(practiceStep)}`
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
      </section>

      <section className="collected-section" aria-labelledby="collected-guide-title">
        <div className="section-heading">
          <h2 id="collected-guide-title">图示教程</h2>
          <span>{hasDiagram ? '步骤示例图' : '占位'}</span>
        </div>
        <section className="face-guide-card">
          {hasDiagram ? (
            <img
              className="collected-diagram-image"
              src={step.diagramImage}
              alt={`${step.title} 示例图`}
            />
          ) : (
            <FaceLayers activePart={step.part} color={step.color} />
          )}
          <div className="current-layer">
            <Layers3 size={15} />
            <span>当前图层</span>
            <strong>{step.title}</strong>
          </div>
        </section>
        <section className="timeline-section" aria-labelledby="collected-timeline-title">
          <div className="section-heading">
            <h2 id="collected-timeline-title">步骤进度</h2>
            <span>
              {stepIndex + 1}/{sample.illustratedSteps.length}
            </span>
          </div>
          <div className="step-timeline">
            {sample.illustratedSteps.map((item, index) => (
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
          <p>{step.instruction}</p>
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
          <div className="expert-tip">
            <Sparkles size={14} />
            <span>{step.expertTip}</span>
          </div>
          <button
            className="slice-button"
            type="button"
            disabled={!illustratedClipPlayable || !illustratedPracticeStep}
            onClick={() => {
              if (!illustratedPracticeStep) return;
              setActiveClip({ step: illustratedPracticeStep, title: step.title });
            }}
          >
            <Film size={16} />
            <span>查看原视频切片</span>
            <small>{step.videoSlice}</small>
            <ChevronRight size={15} />
          </button>
        </section>
      </section>

      {activeClip && sample.practiceTutorial.videoUrl ? (
        <StepClipPlayer
          open
          videoUrl={sample.practiceTutorial.videoUrl}
          clip={activeClip.step.video_clip}
          title={activeClip.title}
          onClose={() => setActiveClip(null)}
        />
      ) : null}
    </MobileShell>
  );
}
