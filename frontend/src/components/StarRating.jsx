import React from 'react';

// uniqueness_score 1-10 → 1-5 星，支持半星
// 填充颜色跟随 CSS 变量 --color-star（明亮=indigo, 暗黑=星光）

function StarIcon({ filled, half }) {
  const starColor = 'var(--color-star)';
  if (half) {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" className="inline-block">
        <defs>
          <linearGradient id="halfGrad">
            <stop offset="50%" stopColor={starColor} />
            <stop offset="50%" stopColor="currentColor" stopOpacity="0.25" />
          </linearGradient>
        </defs>
        <path
          d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
          fill="url(#halfGrad)"
          stroke="currentColor"
          strokeOpacity="0.25"
        />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" className="inline-block">
      <path
        d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
        fill={filled ? starColor : 'none'}
        stroke="currentColor"
        strokeOpacity={filled ? 0 : 0.25}
      />
    </svg>
  );
}

export default function StarRating({ score, maxScore = 10, maxStars = 5, size = 'md' }) {
  const stars = (score / maxScore) * maxStars;
  const fullStars = Math.floor(stars);
  const halfStar = stars - fullStars >= 0.5;
  const emptyStars = maxStars - fullStars - (halfStar ? 1 : 0);

  const sizeClasses = { sm: 'gap-0.5', md: 'gap-1', lg: 'gap-1.5' };

  return (
    <span className={`inline-flex items-center ${sizeClasses[size]}`} title={`${score}/10`}>
      {Array.from({ length: fullStars }).map((_, i) => (
        <StarIcon key={`full-${i}`} filled />
      ))}
      {halfStar && <StarIcon half />}
      {Array.from({ length: emptyStars }).map((_, i) => (
        <StarIcon key={`empty-${i}`} filled={false} />
      ))}
    </span>
  );
}
