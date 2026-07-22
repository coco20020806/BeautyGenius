import { ArrowLeft, Check, ChevronRight, Hand, Palette, ScanFace, WandSparkles } from 'lucide-react';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { BottomNav } from '../components/BottomNav';
import { MobileShell } from '../components/MobileShell';
import { learningService } from '../services/learningService';
import { makeupService } from '../services/makeupService';

const styleOptions = ['清透自然', '甜美元气', '清冷高级', '性感成熟', '个性酷感'];
const occasionOptions = ['日常上学', '通勤工作', '约会聚会', '艺术妆造'];
const retainedPartOptions = ['修容', '腮红', '眼妆'];
const skinTypeOptions = ['油性肌肤', '干性肌肤', '混合性肌肤', '敏感肌'];
const concernOptions = ['增加立体感', '减少脸部留白', '弱化轮廓感', '放大眼睛', '降低眼位', '缩短中庭'];
const constraintOptions = ['没有专业刷具', '产品不齐全', '早上时间少', '不会复杂眼妆', '不喜欢厚重底妆'];

function toggleValue(value: string, current: string[], update: (next: string[]) => void) {
  update(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
}

function MultiChoice({ name, options, selected, onChange }: { name: string; options: string[]; selected: string[]; onChange: (next: string[]) => void }) {
  return <div className="choice-grid">{options.map((item) => {
    const checked = selected.includes(item);
    return <label className={`choice-chip${checked ? ' is-selected' : ''}`} key={item}><input type="checkbox" name={name} checked={checked} onChange={() => toggleValue(item, selected, onChange)} /><span>{item}</span>{checked && <Check size={13} />}</label>;
  })}</div>;
}

function readTaskId(): string | null {
  try {
    const raw = sessionStorage.getItem('makeupTask');
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { taskId?: string };
    return parsed.taskId ?? null;
  } catch {
    return null;
  }
}

export function AdjustPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const routeState = location.state as { from?: string; baseTutorialId?: string } | null;
  const taskId = readTaskId();
  const [style, setStyle] = useState('');
  const [occasions, setOccasions] = useState<string[]>([]);
  const [retainedParts, setRetainedParts] = useState<string[]>([]);
  const [skinType, setSkinType] = useState('混合性肌肤');
  const [concerns, setConcerns] = useState<string[]>([]);
  const [constraints, setConstraints] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    const request = {
      styles: style ? [style] : [],
      occasions,
      retainedParts,
      skinType,
      concerns,
      constraints,
      baseTutorialId: routeState?.baseTutorialId,
    };
    try {
      if (taskId) {
        await makeupService.saveAdjustment(taskId, request);
        navigate('/practice');
        return;
      }
      const tutorial = await learningService.saveAdjustment(request);
      navigate('/tutorial', { state: { from: routeState?.from ?? '/adjust', tutorialId: tutorial.id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成方案失败，请重试');
      setSubmitting(false);
    }
  }

  const backTo = taskId ? '/preview' : (routeState?.from ?? '/preview');

  return (
    <MobileShell withNav className="learning-page adjust-page">
      <header className="detail-header">
        <button className="icon-button" type="button" aria-label="返回" onClick={() => navigate(backTo)}><ArrowLeft size={21} /></button>
        <div><span className="page-kicker">PERSONALIZE</span><h1>微调设置</h1></div><span className="header-spacer" />
      </header>

      <div className="adjust-intro"><WandSparkles size={19} /><p>告诉我们你想怎么调整，我们会改写范围、颜色、位置、工具和顺序。</p></div>

      <form className="adjust-form" onSubmit={submit}>
        <fieldset className="choice-section" aria-labelledby="personal-style-title"><div className="choice-section__heading"><Palette size={17} /><h2 id="personal-style-title">个人风格</h2></div>
          <div className="choice-question"><h3>你希望这个妆容更偏向哪种风格？</h3><small>单选</small><div className="choice-grid">{styleOptions.map((item) => <label className={`choice-chip${style === item ? ' is-selected' : ''}`} key={item}><input type="radio" name="styles" value={item} checked={style === item} onChange={() => setStyle(item)} /><span>{item}</span>{style === item && <Check size={13} />}</label>)}</div></div>
          <div className="choice-question"><h3>这个妆主要使用在哪些场景？</h3><small>多选</small><MultiChoice name="occasions" options={occasionOptions} selected={occasions} onChange={setOccasions} /></div>
        </fieldset>

        <fieldset className="choice-section" aria-labelledby="face-match-title"><div className="choice-section__heading"><ScanFace size={17} /><h2 id="face-match-title">脸部匹配</h2></div>
          <div className="choice-question"><h3>你希望保留原教程的哪些部分？</h3><small>多选</small><MultiChoice name="retainedParts" options={retainedPartOptions} selected={retainedParts} onChange={setRetainedParts} /></div>
          <div className="choice-question"><h3>你的肤质更接近哪种？</h3><small>单选</small><div className="choice-grid">{skinTypeOptions.map((item) => <label className={`choice-chip${skinType === item ? ' is-selected' : ''}`} key={item}><input type="radio" name="skinType" value={item} checked={skinType === item} onChange={() => setSkinType(item)} /><span>{item}</span>{skinType === item && <Check size={13} />}</label>)}</div></div>
          <div className="choice-question"><h3>你希望通过化妆修饰什么问题？</h3><small>多选</small><MultiChoice name="concerns" options={concernOptions} selected={concerns} onChange={setConcerns} /></div>
        </fieldset>

        <fieldset className="choice-section" aria-labelledby="tools-title"><div className="choice-section__heading"><Hand size={17} /><h2 id="tools-title">工具</h2></div>
          <div className="choice-question"><h3>你有哪些限制？</h3><small>多选</small><MultiChoice name="constraints" options={constraintOptions} selected={constraints} onChange={setConstraints} /></div>
        </fieldset>

        {error ? <p className="form-error" role="alert">{error}</p> : null}
        <button className="primary-button" type="submit" disabled={submitting}>{submitting ? '正在生成…' : <>生成方案<ChevronRight size={18} /></>}</button>
      </form>
      <BottomNav />
    </MobileShell>
  );
}
