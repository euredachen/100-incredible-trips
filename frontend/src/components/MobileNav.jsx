import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { to: '/', label: '首页' },
  { to: '/trips', label: '探索' },
  { to: '/trips/random', label: '随机' },
];

export default function MobileNav() {
  const location = useLocation();

  return (
    <nav className="mobile-bottom-nav sm:hidden" style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 50,
      background: 'var(--color-nav-bg)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderTop: '0.5px solid var(--color-border)',
      display: 'flex', justifyContent: 'space-around',
      padding: '6px 0 calc(6px + env(safe-area-inset-bottom))',
      height: '48px',
    }}>
      {navItems.map((item) => {
        const active = item.to === '/'
          ? location.pathname === '/'
          : location.pathname.startsWith(item.to);
        return (
          <Link
            key={item.to}
            to={item.to}
            className="flex items-center px-4 h-full transition-colors"
            style={{
              color: active ? 'var(--accent-warm)' : 'var(--color-text-secondary)',
              fontSize: '14px',
              fontWeight: active ? 600 : 400,
            }}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
