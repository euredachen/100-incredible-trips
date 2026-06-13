import React, { useEffect, useState, useCallback, lazy, Suspense } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { themes, applyTheme, getStoredTheme } from './utils/themeGenerator';
import ThemeToggle from './components/ThemeToggle';
import MobileNav from './components/MobileNav';
import tracker from './utils/tracker';
import HomePage from './pages/HomePage';

// 代码分割 — 列表页和详情页按需加载
const TripsListPage = lazy(() => import('./pages/TripsListPage'));
const TripDetailPage = lazy(() => import('./pages/TripDetailPage'));

function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center"
         style={{ backgroundColor: 'var(--color-surface)' }}>
      <div className="w-10 h-10 border-2 rounded-full animate-spin"
           style={{ borderColor: 'var(--color-border)', borderTopColor: 'var(--accent-warm)' }} />
    </div>
  );
}

export default function App() {
  const location = useLocation();
  const [theme, setTheme] = useState(() => getStoredTheme());

  useEffect(() => {
    applyTheme(theme);
    tracker.pageView();
  }, []); // eslint-disable-line

  useEffect(() => {
    tracker.pageView();
  }, [location.pathname]);

  const handleToggle = useCallback(() => {
    setTheme((prev) => {
      const next = prev.name === 'dark' ? themes.light : themes.dark;
      localStorage.setItem('theme', next.name);
      applyTheme(next);
      tracker.themeToggle(next.name);
      return next;
    });
  }, []);

  return (
    <div
      className="min-h-screen transition-colors duration-700"
      style={{
        backgroundColor: 'var(--color-surface)',
        color: 'var(--color-text)',
      }}
    >
      <div
        className="fixed inset-0 -z-10 bg-cover bg-center bg-fixed transition-all duration-1000"
        style={{ backgroundImage: 'var(--bg-image)' }}
      />

      <ThemeToggle theme={theme} onToggle={handleToggle} />

      <Suspense fallback={<PageLoader />}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<HomePage />} />
            <Route path="/trips" element={<TripsListPage />} />
            <Route path="/trips/:id" element={<TripDetailPage />} />
          </Routes>
        </AnimatePresence>
      </Suspense>

      {/* 移动端底部导航栏 */}
      <MobileNav />
    </div>
  );
}
