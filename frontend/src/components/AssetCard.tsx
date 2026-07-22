import { Check, ChevronRight, Sparkles } from 'lucide-react';
import type { LibraryAsset } from '../types/learning';

interface AssetCardProps { asset: LibraryAsset; onSelect: (asset: LibraryAsset) => void; }

export function AssetCard({ asset, onSelect }: AssetCardProps) {
  return (
    <button className="asset-card" type="button" aria-label={`${asset.title}，选择资产`} onClick={() => onSelect(asset)}>
      <span className="asset-card__visual">
        <img src={asset.coverImage} alt={`${asset.title}视频封面`} />
        {asset.practiced && <i><Check size={10} /></i>}
      </span>
      <span className="asset-card__copy"><strong>{asset.title}</strong><small>{asset.style} · {asset.difficulty}</small><em><Sparkles size={11} />{asset.source}</em></span>
      <ChevronRight size={14} />
    </button>
  );
}
