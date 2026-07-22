import { Check, ChevronDown, ChevronRight, ChevronUp, WandSparkles } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { learningService } from '../services/learningService';
import type { LibraryAsset, MixDecision, MixPart } from '../types/learning';

const mixParts: Array<{ id: MixPart; label: string }> = [
  { id: 'base', label: '底妆' }, { id: 'eyes', label: '眼妆' }, { id: 'blush', label: '腮红' }, { id: 'contour', label: '修容' }, { id: 'lips', label: '唇妆' },
];
const initialDecision: MixDecision = { base: null, eyes: null, blush: null, contour: null, lips: null };

export function MixEditor() {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<LibraryAsset[]>([]);
  const [decision, setDecision] = useState<MixDecision>(initialDecision);
  const [expandedParts, setExpandedParts] = useState<Set<MixPart>>(() => new Set());

  useEffect(() => { void learningService.listAssets({ category: 'part', placement: 'mix' }).then(setAssets); }, []);
  const assetsByPart = useMemo(() => Object.fromEntries(mixParts.map(({ id }) => [id, assets.filter((asset) => asset.part === id)])) as Record<MixPart, LibraryAsset[]>, [assets]);

  function decide(part: MixPart, value: string) {
    setDecision((current) => ({ ...current, [part]: value }));
  }

  function togglePart(part: MixPart) {
    setExpandedParts((current) => {
      const next = new Set(current);
      if (next.has(part)) next.delete(part);
      else next.add(part);
      return next;
    });
  }

  function generate() {
    sessionStorage.setItem('makeupMixDecision', JSON.stringify(decision));
    navigate('/mix/generating');
  }

  return <section className="mix-editor" aria-label="混搭编辑">
    <div className="mix-progress"><div><strong>部位选择</strong><span>按需选择想要混搭的部位</span></div></div>
    <div className="mix-decision-list">
      {mixParts.map(({ id, label }) => {
        const selected = assetsByPart[id].find((asset) => asset.id === decision[id]);
        const expanded = expandedParts.has(id);
        return <section className={`mix-part-card${expanded ? ' is-expanded' : ''}${selected ? ' has-selection' : ''}`} role="group" aria-label={`${label}选择`} key={id}>
          <button className="mix-part-toggle" type="button" aria-expanded={expanded} aria-controls={`mix-options-${id}`} aria-label={`${expanded ? '收起' : '展开'}${label}选项`} onClick={() => togglePart(id)}><h2>{label}</h2>{selected && <small>{selected.title}</small>}{expanded ? <ChevronUp size={17} /> : <ChevronDown size={17} />}</button>
          {expanded && <div className="mix-option-list" id={`mix-options-${id}`}>
            {assetsByPart[id].map((asset) => <button type="button" aria-label={asset.title} key={asset.id} className={decision[id] === asset.id ? 'is-selected' : ''} onClick={() => decide(id, asset.id)}><i style={{ backgroundColor: asset.color }} /><span><strong>{asset.title}</strong><small>{asset.style} · {asset.source}</small></span>{decision[id] === asset.id && <Check size={14} />}</button>)}
          </div>}
        </section>;
      })}
    </div>
    <button className="primary-button mix-generate" type="button" onClick={generate}><WandSparkles size={18} />生成效果<ChevronRight size={17} /></button>
  </section>;
}
