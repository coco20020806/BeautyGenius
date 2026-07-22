import { ArrowLeft, Check, Circle, LoaderCircle, RotateCcw } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';
import { learningService } from '../services/learningService';
import type { MixDecision, MixPart } from '../types/learning';

const parts: MixPart[] = ['base', 'eyes', 'blush', 'contour', 'lips'];
const stages = ['整理部位选择', '匹配预制妆效', '准备效果预览'];

function readDecision(): MixDecision | null {
  try {
    const value = JSON.parse(sessionStorage.getItem('makeupMixDecision') ?? 'null') as Partial<MixDecision> | null;
    return value && parts.every((part) => value[part] !== undefined) ? value as MixDecision : null;
  } catch { return null; }
}

export function MixGeneratingPage() {
  const navigate = useNavigate();
  const [decision] = useState(readDecision);
  const [progress, setProgress] = useState(8);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  function retry() {
    setError('');
    setProgress(8);
    setAttempt((value) => value + 1);
  }

  useEffect(() => {
    if (!decision) return;
    const interval = window.setInterval(() => setProgress((value) => Math.min(92, value + 7)), 140);
    let active = true;
    void Promise.all([learningService.generateMix(decision), new Promise((resolve) => window.setTimeout(resolve, 1400))]).then(([result]) => {
      if (active) navigate('/mix/preview', { replace: true, state: { resultId: result.id } });
    }).catch((reason) => active && setError(reason instanceof Error ? reason.message : '预制效果加载失败'));
    return () => { active = false; window.clearInterval(interval); };
  }, [attempt, decision, navigate]);

  if (!decision) return <Navigate to="/library?tab=mix" replace />;
  const activeStage = progress < 34 ? 0 : progress < 72 ? 1 : 2;
  return <MobileShell className="learning-page mix-generating-page">
    <header className="detail-header"><button className="icon-button" type="button" aria-label="返回修改" onClick={() => navigate('/library?tab=mix')}><ArrowLeft size={21} /></button><div><span className="page-kicker">PRESET MATCH</span><h1>生成妆效中</h1></div><span className="header-spacer" /></header>
    {error ? <section className="mix-generation-error"><RotateCcw size={26} /><h2>暂时无法准备效果</h2><p>{error}</p><button className="primary-button" type="button" onClick={retry}>重新生成</button><button className="secondary-button" type="button" onClick={() => navigate('/library?tab=mix')}>返回修改</button></section> : <><section className="mix-progress-visual" aria-label="生成进度图"><div className="mix-progress-ring" role="progressbar" aria-label="生成进度" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress} style={{ '--mix-progress': `${progress * 3.6}deg` } as CSSProperties}><span><strong>{progress}%</strong><small>预制匹配</small></span></div><h2>正在准备你的混搭效果</h2><p>预计剩余 {Math.max(1, Math.ceil((100 - progress) / 35))} 秒</p></section><section className="mix-generation-stages" aria-label="生成阶段">{stages.map((stage, index) => <div className={index < activeStage ? 'is-done' : index === activeStage ? 'is-active' : ''} key={stage}><span>{index < activeStage ? <Check size={14} /> : index === activeStage ? <LoaderCircle className="spin" size={14} /> : <Circle size={14} />}</span><strong>{stage}</strong></div>)}</section></>}
  </MobileShell>;
}
