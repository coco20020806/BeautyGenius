import { Home } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

const FLOW_SESSION_KEYS = [
  'makeupTask',
  'makeupProgress',
  'makeupTutorial',
  'makeupAdjustment',
  'makeupMixDecision',
  'makeupMixResult',
] as const;

function endCurrentFlow() {
  for (const key of FLOW_SESSION_KEYS) {
    sessionStorage.removeItem(key);
  }
}

export function HomeExitButton() {
  const location = useLocation();
  const navigate = useNavigate();

  if (location.pathname === '/') {
    return null;
  }

  return (
    <button
      className="home-exit-button"
      type="button"
      aria-label="回到首页，结束当前进程"
      title="回到首页（结束当前进程）"
      onClick={() => {
        endCurrentFlow();
        navigate('/', { replace: true });
      }}
    >
      <Home aria-hidden="true" size={16} strokeWidth={2} />
      <span>首页</span>
    </button>
  );
}
