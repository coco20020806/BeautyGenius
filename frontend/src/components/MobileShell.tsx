import type { ReactNode } from 'react';

interface MobileShellProps {
  children: ReactNode;
  withNav?: boolean;
  className?: string;
}

export function MobileShell({ children, withNav = false, className = '' }: MobileShellProps) {
  return (
    <div className="app-stage">
      <main className={`mobile-shell ${withNav ? 'mobile-shell--with-nav' : ''} ${className}`.trim()}>
        {children}
      </main>
    </div>
  );
}
