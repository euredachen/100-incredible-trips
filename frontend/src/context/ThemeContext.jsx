import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('theme');
    if (stored) return stored === 'dark';
    return true; // 默认深色
  });

  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;

    if (dark) {
      root.classList.add('dark');
      body.classList.add('dark');
      body.classList.remove('light');
      root.style.setProperty('--color-bg', '#000000');
      root.style.setProperty('--color-text', '#F5F5F5');
      root.style.setProperty('--color-text-secondary', '#A0A0A0');
      root.style.setProperty('--color-card-bg', 'rgba(0, 0, 0, 0.5)');
      root.style.setProperty('--color-card-border', 'rgba(255, 255, 255, 0.1)');
      root.style.setProperty('--color-nav-bg', 'rgba(0, 0, 0, 0.6)');
      root.style.setProperty('--color-accent-warm', '#FF6B35');
      root.style.setProperty('--color-accent-cool', '#00D4FF');
      root.style.setProperty('--bg-image', 'url(/images/bg-aurora.jpg)');
      root.style.setProperty('--bg-overlay', 'rgba(0, 0, 0, 0.45)');
    } else {
      root.classList.remove('dark');
      body.classList.remove('dark');
      body.classList.add('light');
      root.style.setProperty('--color-bg', '#F5F5F5');
      root.style.setProperty('--color-text', '#1A1A1A');
      root.style.setProperty('--color-text-secondary', '#6B6B6B');
      root.style.setProperty('--color-card-bg', 'rgba(255, 255, 255, 0.85)');
      root.style.setProperty('--color-card-border', 'rgba(0, 0, 0, 0.08)');
      root.style.setProperty('--color-nav-bg', 'rgba(255, 255, 255, 0.85)');
      root.style.setProperty('--color-accent-warm', '#E55A2B');
      root.style.setProperty('--color-accent-cool', '#00B8D4');
      root.style.setProperty('--bg-image', 'url(/images/bg-ocean.jpg)');
      root.style.setProperty('--bg-overlay', 'rgba(255, 255, 255, 0.3)');
    }

    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  const toggle = useCallback(() => setDark((prev) => !prev), []);

  return (
    <ThemeContext.Provider value={{ dark, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
