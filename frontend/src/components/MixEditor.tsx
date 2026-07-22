import { Check, ChevronRight, Layers3 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { learningService } from '../services/learningService';
import type { LibraryAsset, MixDecision, MixPart } from '../types/learning';

const partLabels: Record<MixPart, string> = {
  base: '底妆', eyes: '眼妆', blush: '腮红', contour: '修容', lips: '唇妆',
};
const mixPartOrder: MixPart[] = ['base', 'eyes', 'blush', 'contour', 'lips'];
const initialDecision: MixDecision = { base: null, eyes: null, blush: null, contour: null, lips: null };

export function MixEditor() {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<LibraryAsset[]>([]);
  const [decision, setDecision] = useState<MixDecision>(initialDecision);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    // 混搭选项与知识库「部位」卡位同源，只展示库内已有部件
    void learningService.listAssets({ category: 'part', placement: 'library' }).then(setAssets);
  }, []);

  const mixParts = useMemo(
    () => mixPartOrder
      .map((id) => {
        const options = assets.filter((asset) => asset.part === id);
        return options.length ? { id, label: partLabels[id], asset: options[0]! } : null;
      })
      .filter((item): item is { id: MixPart; label: string; asset: LibraryAsset } => Boolean(item)),
    [assets],
  );

  const selectedCount = mixParts.filter(({ id }) => decision[id]).length;

  function togglePart(part: MixPart, assetId: string) {
    setDecision((current) => ({
      ...current,
      [part]: current[part] === assetId ? null : assetId,
    }));
  }

  async function generate() {
    if (!selectedCount || generating) return;
    setGenerating(true);
    try {
      const result = await learningService.generateMix(decision);
      navigate('/tutorial', { state: { from: '/library?tab=mix', tutorialId: result.tutorialId } });
    } finally {
      setGenerating(false);
    }
  }

  return (
    <section className="mix-editor" aria-label="混搭编辑">
      <div className="mix-progress">
        <div>
          <strong>部件勾选</strong>
          <span>勾选想要的部件，按顺序生成图示流程</span>
        </div>
      </div>
      <div className="mix-decision-list">
        {mixParts.map(({ id, label, asset }) => {
          const checked = decision[id] === asset.id;
          return (
            <button
              key={id}
              type="button"
              className={`mix-select-card${checked ? ' is-selected' : ''}`}
              aria-pressed={checked}
              aria-label={`${checked ? '取消勾选' : '勾选'}${label}`}
              onClick={() => togglePart(id, asset.id)}
            >
              <span className="mix-select-cover">
                {asset.coverImage
                  ? <img src={asset.coverImage} alt={`${asset.title}封面`} />
                  : <i style={{ backgroundColor: asset.color }} />}
              </span>
              <span className="mix-select-copy">
                <strong>{label}</strong>
                <small>{asset.title}</small>
                <em>{asset.style} · {asset.source}</em>
              </span>
              <span className={`mix-select-check${checked ? ' is-on' : ''}`} aria-hidden="true">
                {checked ? <Check size={14} /> : null}
              </span>
            </button>
          );
        })}
      </div>
      <button
        className="primary-button mix-generate"
        type="button"
        disabled={!selectedCount || generating}
        onClick={() => void generate()}
      >
        <Layers3 size={18} />
        {generating ? '生成中…' : '生成图示流程'}
        <ChevronRight size={17} />
      </button>
    </section>
  );
}
