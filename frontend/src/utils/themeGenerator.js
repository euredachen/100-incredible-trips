/**
 * 双主题完整配色方案
 *
 * ☀️ 明亮 — indigo蓝 星级+景观高亮 + 巴哈马碧蓝海洋背景
 * 🌙 深色 — 星光色 星级 + 极地雪原极光背景 + 浅色文字
 */

export const themes = {
  light: {
    name: 'light',
    label: '☀️ 明亮',
    bgImage: '/images/ocean-bg.jpg',

    colors: {
      primary:          '#0D9EAD',
      primaryDark:      '#1C424D',
      primaryLight:     '#88B4B3',

      accentWarm:       '#E8734A',
      accentWarmLight:  'rgba(232, 115, 74, 0.12)',
      accentCool:       '#4F46E5',  // indigo蓝 — 景观按钮高亮 + 随机探索
      accentCoolLight:  'rgba(79, 70, 229, 0.10)',

      surface:          'rgba(255, 255, 255, 0.10)',
      card:             'rgba(255, 255, 255, 0.82)',
      cardHover:        'rgba(255, 255, 255, 0.92)',
      nav:              'rgba(255, 255, 255, 0.70)',  // 70% 不透明度

      text:             '#1A2E33',
      textSecondary:    '#374151',
      heading:          '#1A2E33',

      border:           'rgba(13, 158, 173, 0.12)',
      shadow:           'rgba(13, 158, 173, 0.08)',

      star:             '#4F46E5',  // indigo蓝 星级
    },
  },

  dark: {
    name: 'dark',
    label: '🌙 深色',
    bgImage: '/images/aurora-bg.jpg',

    colors: {
      primary:          '#10B981',
      primaryDark:      '#065F46',
      primaryLight:     '#6EE7B7',

      accentWarm:       '#FF6B35',
      accentWarmLight:  'rgba(255, 107, 53, 0.15)',
      accentCool:       '#00D4FF',  // 冰湖蓝 — 深色底重点突出
      accentCoolLight:  'rgba(0, 212, 255, 0.12)',

      surface:          'rgba(5, 15, 4, 0.10)',
      card:             'rgba(8, 22, 16, 0.65)',
      cardHover:        'rgba(8, 22, 16, 0.80)',
      nav:              'rgba(5, 15, 4, 0.70)',  // 70% 不透明度

      text:             '#FFFFFF',  // 纯白 — 正文高可读
      textSecondary:    '#E8D5A0',  // 米黄
      heading:          '#F5E6A0',  // 浅黄 — 章节标题

      border:           'rgba(16, 185, 129, 0.12)',
      shadow:           'rgba(0, 0, 0, 0.2)',

      star:             '#FDE68A',  // 星光琥珀金
    },
  },
};

export function applyTheme(theme) {
  const t = theme.colors;
  const r = document.documentElement;

  r.style.setProperty('--primary',             t.primary);
  r.style.setProperty('--primary-dark',        t.primaryDark);
  r.style.setProperty('--primary-light',       t.primaryLight);
  r.style.setProperty('--accent-warm',         t.accentWarm);
  r.style.setProperty('--accent-warm-light',   t.accentWarmLight);
  r.style.setProperty('--accent-cool',         t.accentCool);
  r.style.setProperty('--accent-cool-light',   t.accentCoolLight);
  r.style.setProperty('--color-surface',       t.surface);
  r.style.setProperty('--color-card-bg',       t.card);
  r.style.setProperty('--color-card-hover',    t.cardHover);
  r.style.setProperty('--color-nav-bg',        t.nav);
  r.style.setProperty('--color-text',          t.text);
  r.style.setProperty('--color-text-secondary',t.textSecondary);
  r.style.setProperty('--color-heading',       t.heading);
  r.style.setProperty('--color-border',        t.border);
  r.style.setProperty('--color-shadow',        t.shadow);
  r.style.setProperty('--color-star',          t.star);
  r.style.setProperty('--bg-image',            `url(${theme.bgImage})`);

  r.style.setProperty('--color-accent-warm',   t.accentWarm);
  r.style.setProperty('--color-accent-cool',   t.accentCool);

  document.body.classList.remove('light', 'dark');
  document.body.classList.add(theme.name);
}

export function getStoredTheme() {
  return localStorage.getItem('theme') === 'light' ? themes.light : themes.dark;
}

export function toggleTheme(currentName) {
  const next = currentName === 'dark' ? themes.light : themes.dark;
  localStorage.setItem('theme', next.name);
  applyTheme(next);
  return next;
}
