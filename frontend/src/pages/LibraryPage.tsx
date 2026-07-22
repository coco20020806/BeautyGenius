import { Blend, BookOpen, Boxes, Filter, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AssetCard } from '../components/AssetCard';
import { BottomNav } from '../components/BottomNav';
import { MobileShell } from '../components/MobileShell';
import { MixEditor } from '../components/MixEditor';
import { learningService } from '../services/learningService';
import type { AssetCategory, LibraryAsset, LibraryPartFilter } from '../types/learning';

type LibraryTab = Exclude<AssetCategory, 'product'> | 'mix';
type PartFilter = LibraryPartFilter | '全部';

const tabs: Array<{ id: LibraryTab; label: string; icon: typeof BookOpen }> = [
  { id: 'tutorial', label: '收藏教程', icon: BookOpen },
  { id: 'part', label: '部位', icon: Boxes },
  { id: 'mix', label: '混搭', icon: Blend },
];
const styles = ['全部', '清透', '甜美', '冷感', '自然'];
const parts: Array<{ id: PartFilter; label: string }> = [
  { id: '全部', label: '全部' },
  { id: 'base', label: '底妆' },
  { id: 'eyes', label: '眼妆' },
  { id: 'blush', label: '腮红' },
  { id: 'contour', label: '修容' },
  { id: 'lips', label: '唇妆' },
  { id: 'full-face', label: '全脸' },
];
const occasions = ['全部', '日常', '通勤', '约会', '聚会'];
const difficulties = ['全部', '新手', '进阶'];

function isPlaceholderAsset(asset: LibraryAsset) {
  return !asset.coverImage;
}

export function LibraryPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const category: LibraryTab = params.get('tab') === 'mix' ? 'mix' : params.get('tab') === 'part' ? 'part' : 'tutorial';
  const [style, setStyle] = useState('全部');
  const [part, setPart] = useState<PartFilter>('全部');
  const [occasion, setOccasion] = useState('全部');
  const [difficulty, setDifficulty] = useState('全部');
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [assets, setAssets] = useState<LibraryAsset[]>([]);

  useEffect(() => {
    if (category === 'mix') return;
    void learningService
      .listAssets({
        category,
        placement: category === 'part' ? 'library' : undefined,
        style: category === 'tutorial' ? style : '全部',
        part: category === 'part' && part !== '全部' ? part : undefined,
        occasion,
        difficulty,
      })
      .then(setAssets);
  }, [category, style, part, occasion, difficulty]);

  function selectAsset(asset: LibraryAsset) {
    if (isPlaceholderAsset(asset)) {
      navigate(`/library/collected/${asset.id}`);
      return;
    }
    navigate('/tutorial', { state: { from: `/library?tab=${category}`, tutorialId: asset.tutorialId } });
  }

  return (
    <MobileShell withNav className="learning-page library-page">
      <header className="library-heading">
        <span className="page-kicker">MY BEAUTY ARCHIVE</span>
      </header>
      <div className="library-tab-row" role="group" aria-label="知识库分类与筛选">
        <div className="library-tabs" role="tablist" aria-label="知识库分类">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={category === id}
              className={category === id ? 'is-active' : ''}
              onClick={() => setParams(id === 'tutorial' ? {} : { tab: id })}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>
        {category !== 'mix' && (
          <button
            className="library-filter-button"
            type="button"
            aria-label="筛选"
            aria-expanded={filtersOpen}
            onClick={() => setFiltersOpen((open) => !open)}
          >
            <Filter size={17} />
          </button>
        )}
      </div>
      {category === 'mix' ? (
        <MixEditor />
      ) : (
        <>
          {category === 'part' ? (
            <div className="filter-scroll" aria-label="部位筛选">
              {parts.map((item) => (
                <button
                  type="button"
                  key={item.id}
                  className={`${part === item.id ? 'is-active' : ''}${item.id === 'full-face' ? ' is-full-face' : ''}`}
                  onClick={() => setPart(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          ) : (
            <div className="filter-scroll" aria-label="风格筛选">
              {styles.map((item) => (
                <button type="button" key={item} className={style === item ? 'is-active' : ''} onClick={() => setStyle(item)}>
                  {item}
                </button>
              ))}
            </div>
          )}
          {filtersOpen && (
            <section className="advanced-filters" aria-label="更多筛选">
              <label>
                <span>场合</span>
                <select aria-label="场合筛选" value={occasion} onChange={(event) => setOccasion(event.target.value)}>
                  {occasions.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>难度</span>
                <select aria-label="难度筛选" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}>
                  {difficulties.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
              </label>
            </section>
          )}
          <section className="asset-section" aria-live="polite">
            {assets.length ? (
              <div className="asset-grid">
                {assets.map((asset) => (
                  <AssetCard key={asset.id} asset={asset} onSelect={selectAsset} placeholder={isPlaceholderAsset(asset)} />
                ))}
              </div>
            ) : (
              <div className="empty-library">
                <Search size={25} />
                <p>没有找到匹配的素材</p>
                <button
                  type="button"
                  onClick={() => {
                    setStyle('全部');
                    setPart('全部');
                    setOccasion('全部');
                    setDifficulty('全部');
                  }}
                >
                  清除筛选
                </button>
              </div>
            )}
          </section>
        </>
      )}
      <BottomNav />
    </MobileShell>
  );
}
