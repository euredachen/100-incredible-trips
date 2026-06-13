import React from 'react';

export default function SkeletonCard() {
  return (
    <div className="glass-card overflow-hidden">
      {/* 封面图骨架 */}
      <div className="aspect-video skeleton-shimmer" />

      {/* 内容骨架 */}
      <div className="p-6 space-y-3">
        {/* 标签 */}
        <div className="flex gap-2">
          <div className="h-5 w-14 rounded-full skeleton-shimmer" />
          <div className="h-5 w-12 rounded-full skeleton-shimmer" />
        </div>

        {/* 标题 */}
        <div className="space-y-2">
          <div className="h-5 w-3/4 rounded skeleton-shimmer" />
          <div className="h-5 w-1/2 rounded skeleton-shimmer" />
        </div>

        {/* 目的地 */}
        <div className="h-4 w-2/5 rounded skeleton-shimmer" />

        {/* 星级 */}
        <div className="flex gap-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="w-4 h-4 rounded skeleton-shimmer" />
          ))}
        </div>
      </div>
    </div>
  );
}
