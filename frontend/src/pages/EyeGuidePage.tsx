import { ArrowLeft, ChevronLeft, ChevronRight, CirclePlay, Lightbulb, Pause, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { BottomNav } from '../components/BottomNav';
import { EyeDiagram } from '../components/EyeDiagram';
import { MobileShell } from '../components/MobileShell';
import { learningService } from '../services/learningService';
import type { EyeRegionGuide } from '../types/learning';

export function EyeGuidePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const tutorialId = (location.state as { tutorialId?: string } | null)?.tutorialId;
  const [guides, setGuides] = useState<EyeRegionGuide[]>([]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  useEffect(() => { void learningService.getEyeGuides(tutorialId).then(setGuides); }, [tutorialId]);
  if (!guides.length) return <MobileShell><div className="preview-loading"><Sparkles className="spin" /><p>正在加载眼部图示…</p></div></MobileShell>;
  const current = guides[index];

  return (
    <MobileShell withNav className="learning-page eye-page">
      <header className="detail-header"><button className="icon-button" type="button" aria-label="返回" onClick={() => navigate('/tutorial', { state: { tutorialId } })}><ArrowLeft size={21} /></button><div><span className="page-kicker">EYE DETAIL</span><h1>眼部精讲</h1></div><span className="header-spacer" /></header>
      <section className="eye-visual-card"><EyeDiagram activeRegion={current.id} color={current.color} /><div className="eye-region-label"><span style={{ backgroundColor: current.color }} /><strong>{current.label}</strong><small>{index + 1}/{guides.length}</small></div></section>
      <div className="region-chips" role="list" aria-label="眼部区域">{guides.map((guide, guideIndex) => <button type="button" key={guide.id} className={guideIndex === index ? 'is-active' : ''} onClick={() => setIndex(guideIndex)}>{guide.label}</button>)}</div>
      <section className="video-slice-card"><div className="video-time"><span>原视频切片</span><strong>{current.videoSlice}</strong></div><div className="video-track"><span style={{ width: `${20 + index * 10}%` }} /><i style={{ left: `${20 + index * 10}%` }} /></div><div className="slice-controls"><button type="button" aria-label="上一个区域" onClick={() => setIndex((value) => Math.max(0, value - 1))}><ChevronLeft size={17} />上一步</button><button type="button" className="play-control" aria-label={playing ? '暂停切片' : '播放切片'} onClick={() => setPlaying((value) => !value)}>{playing ? <Pause size={18} /> : <CirclePlay size={18} />}</button><button type="button" aria-label="下一个区域" onClick={() => setIndex((value) => Math.min(guides.length - 1, value + 1))}>下一步<ChevronRight size={17} /></button></div></section>
      <section className="eye-copy-card"><span className="step-number">AREA {String(index + 1).padStart(2, '0')}</span><h2>{current.label}</h2><p>{current.description}</p><div className="adaptation-note"><Lightbulb size={16} /><div><strong>你的适配</strong><p>{current.adaptation}</p></div></div></section>
      <BottomNav />
    </MobileShell>
  );
}
