import { BookOpen, Home, Sparkles, UserRound } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const items = [
  { to: '/', label: '首页', icon: Home },
  { to: '/practice', label: '跟练', icon: Sparkles },
  { to: '/library', label: '知识库', icon: BookOpen },
  { to: '/profile', label: '我的', icon: UserRound },
];

export function BottomNav() {
  return (
    <nav className="bottom-nav" aria-label="主导航">
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} className={({ isActive }) => `bottom-nav__item${isActive ? ' is-active' : ''}`}>
          <Icon aria-hidden="true" size={21} strokeWidth={1.8} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
