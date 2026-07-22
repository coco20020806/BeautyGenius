import { Check, ChevronRight, Sparkles } from 'lucide-react';
import type { LibraryAsset } from '../types/learning';

interface AssetCardProps {
  asset: LibraryAsset;
  onSelect: (asset: LibraryAsset) => void;
  /** Empty-cover sample card: keep placeholder look but remain clickable. */
  placeholder?: boolean;
}

export function AssetCard({ asset, onSelect, placeholder = false }: AssetCardProps) {
  const hasCover = Boolean(asset.coverImage);

  return (
    <button
      className={`asset-card${placeholder ? ' is-placeholder' : ''}`}
      type="button"
      aria-label={placeholder ? `${asset.title}，打开示例教程详情` : `${asset.title}，选择资产`}
      onClick={() => onSelect(asset)}
    >
      <span className={`asset-card__visual${hasCover ? '' : ' is-empty'}`}>
        {hasCover ? (
          <img src={asset.coverImage} alt={`${asset.title}视频封面`} />
        ) : (
          <span className="asset-card__placeholder">待生成</span>
        )}
        {asset.practiced && (
          <i>
            <Check size={10} />
          </i>
        )}
      </span>
      <span className="asset-card__copy">
        <strong>{asset.title}</strong>
        <small>
          {asset.style} · {asset.difficulty}
        </small>
        <em>
          <Sparkles size={11} />
          {asset.source}
        </em>
      </span>
      <ChevronRight size={14} />
    </button>
  );
}
