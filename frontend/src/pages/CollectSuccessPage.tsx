import { ArrowLeft, BookOpenCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MobileShell } from '../components/MobileShell';

export function CollectSuccessPage() {
  const navigate = useNavigate();

  return (
    <MobileShell className="practice-page collect-success-page">
      <header className="detail-header">
        <button
          className="icon-button"
          type="button"
          aria-label="返回"
          onClick={() => navigate('/practice/examples')}
        >
          <ArrowLeft size={21} />
        </button>
        <div>
          <span className="page-kicker">LIBRARY</span>
          <h1>收藏结果</h1>
        </div>
        <span className="header-spacer" />
      </header>

      <div className="collect-success">
        <BookOpenCheck size={36} aria-hidden />
        <h2>收藏成功！</h2>
        <button
          className="primary-button practice-footer__cta"
          type="button"
          onClick={() => navigate('/practice/examples')}
        >
          返回示例图
        </button>
      </div>
    </MobileShell>
  );
}
