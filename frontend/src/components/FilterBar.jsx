import React from 'react';
import { motion } from 'framer-motion';

const experienceTypes = [
  { key: 'adventure', label: '🏔️ 探险' },
  { key: 'cultural', label: '🏛️ 人文' },
  { key: 'nature', label: '🌿 自然' },
  { key: 'food', label: '🍜 美食' },
  { key: 'art', label: '🎨 艺术' },
  { key: 'wellness', label: '🧘 康养' },
];

const landscapeTypes = [
  { key: 'urban', label: '🏙️ 城市' },
  { key: 'ocean', label: '🌊 海洋' },
  { key: 'forest', label: '🌲 森林' },
  { key: 'mountain', label: '⛰️ 山峰' },
  { key: 'snow', label: '❄️ 雪原' },
];

export default function FilterBar({
  activeType,
  onTypeChange,
  activeLandscape,
  onLandscapeChange,
  minStars,
  onStarsChange,
}) {
  return (
    <div className="glass-nav">
      <div className="max-w-[1280px] mx-auto px-6 md:px-10 py-3 space-y-3">
        {/* 第一行：体验类型 — 暖色强调 */}
        <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none pb-1">
          <span className="text-xs shrink-0" style={{ color: 'var(--color-text-secondary)' }}>
            类型
          </span>
          <button
            onClick={() => onTypeChange(null)}
            className="capsule border transition-all duration-200"
            style={{
              backgroundColor: !activeType ? 'var(--accent-warm)' : 'transparent',
              color: !activeType ? '#fff' : 'var(--color-text-secondary)',
              borderColor: !activeType ? 'var(--accent-warm)' : 'var(--color-border)',
            }}
          >
            全部
          </button>
          {experienceTypes.map((t) => (
            <motion.button
              key={t.key}
              onClick={() => onTypeChange(activeType === t.key ? null : t.key)}
              whileTap={{ scale: 0.95 }}
              className="capsule border transition-all duration-200"
              style={{
                backgroundColor: activeType === t.key
                  ? 'var(--accent-warm)' : 'transparent',
                color: activeType === t.key ? '#fff' : 'var(--color-text-secondary)',
                borderColor: activeType === t.key
                  ? 'var(--accent-warm)' : 'var(--color-border)',
              }}
            >
              {t.label}
            </motion.button>
          ))}
        </div>

        {/* 第二行：景观类型 — 冷色强调 + 星级 */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none">
            <span className="text-xs shrink-0" style={{ color: 'var(--color-text-secondary)' }}>
              景观
            </span>
            <button
              onClick={() => onLandscapeChange(null)}
              className="capsule border transition-all duration-200"
              style={{
                backgroundColor: !activeLandscape ? 'var(--accent-cool)' : 'transparent',
                color: !activeLandscape ? '#fff' : 'var(--color-text-secondary)',
                borderColor: !activeLandscape ? 'var(--accent-cool)' : 'var(--color-border)',
              }}
            >
              全部
            </button>
            {landscapeTypes.map((s) => (
              <button
                key={s.key}
                onClick={() => onLandscapeChange(activeLandscape === s.key ? null : s.key)}
                className="capsule border transition-all duration-200"
                style={{
                  backgroundColor: activeLandscape === s.key
                    ? 'var(--accent-cool)' : 'transparent',
                  color: activeLandscape === s.key ? '#fff' : 'var(--color-text-secondary)',
                  borderColor: activeLandscape === s.key
                    ? 'var(--accent-cool)' : 'var(--color-border)',
                }}
              >
                {s.label}
              </button>
            ))}
          </div>

          {/* 不可思议指数 — 星级 */}
          <div className="flex items-center gap-1.5 ml-auto sm:ml-0">
            <span className="text-xs shrink-0" style={{ color: 'var(--color-text-secondary)' }}>
              不可思议
            </span>
            <div className="flex items-center gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => onStarsChange(minStars === star ? 0 : star)}
                  className="transition-colors"
                  title={`≥ ${star} 星 (≥${star * 2}/10)`}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24">
                    <path
                      d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                      fill={star <= minStars ? 'var(--color-star)' : 'none'}
                      stroke={star <= minStars ? 'var(--color-star)' : 'var(--color-text-secondary)'}
                      strokeOpacity={star <= minStars ? 1 : 0.2}
                    />
                  </svg>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
