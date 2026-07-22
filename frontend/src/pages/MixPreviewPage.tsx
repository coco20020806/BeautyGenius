import { ArrowLeft, Check, SlidersHorizontal, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { BeforeAfterSlider } from '../components/BeforeAfterSlider';
import { MobileShell } from '../components/MobileShell';
import { learningService } from '../services/learningService';
import type { MixResult } from '../types/learning';

export function MixPreviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const resultId = (location.state as { resultId?: string } | null)?.resultId;
  const [result, setResult] = useState<MixResult | null | undefined>(undefined);
  useEffect(() => { void learningService.getMixResult(resultId).then(setResult); }, [resultId]);
  if (result === null) return <Navigate to="/library?tab=mix" replace />;
  return <MobileShell className="preview-page mix-preview-page">
    <header className="detail-header"><button className="icon-button" type="button" aria-label="返回混搭" onClick={() => navigate('/library?tab=mix')}><ArrowLeft size={21} /></button><div><span className="page-kicker">YOUR PRESET MIX</span><h1>混搭效果预览</h1></div><span className="header-spacer" /></header>
    {result ? <><BeforeAfterSlider beforeSrc={result.beforeImage} afterSrc={result.afterImage} /><section className="makeup-summary" aria-labelledby="mix-summary-title"><div className="summary-heading"><div><span className="section-eyebrow">预制妆效</span><h2 id="mix-summary-title">{result.title}</h2></div><span className="difficulty-pill">组合完成</span></div><p className="mix-result-summary">{result.summary}</p></section><section className="decision-card" aria-label="混搭适配判断"><h2>这个妆适合你吗？</h2><p>确认后将进入对应的预制图示教程</p><div className="decision-actions"><button type="button" className="is-positive" onClick={() => navigate('/tutorial', { state: { from: '/mix/preview', tutorialId: result.tutorialId } })}><Check size={17} />适合我</button><button type="button" onClick={() => navigate('/adjust', { state: { from: '/mix/preview', baseTutorialId: result.tutorialId } })}><SlidersHorizontal size={17} />需要微调</button></div></section></> : <div className="preview-loading"><Sparkles className="spin" size={26} /><p>正在读取预制效果…</p></div>}
  </MobileShell>;
}
