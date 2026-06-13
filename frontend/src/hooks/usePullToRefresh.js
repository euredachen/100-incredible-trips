import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * 移动端下拉刷新 Hook
 *
 * 用法:
 *   const { ref, refreshing, pullDistance } = usePullToRefresh(onRefresh);
 *   <div ref={ref} style={{ transform: `translateY(${pullDistance}px)` }}>
 */
export default function usePullToRefresh(onRefresh, { threshold = 60, enabled = true } = {}) {
  const [refreshing, setRefreshing] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const startY = useRef(0);
  const containerRef = useRef(null);

  const handleTouchStart = useCallback((e) => {
    if (!enabled) return;
    // 仅当滚动到顶部时触发
    if (window.scrollY > 5) return;
    startY.current = e.touches[0].clientY;
  }, [enabled]);

  const handleTouchMove = useCallback((e) => {
    if (!enabled || startY.current === 0) return;
    const currentY = e.touches[0].clientY;
    const diff = currentY - startY.current;
    if (diff > 0 && window.scrollY <= 5) {
      // 阻尼效果：越拉越难拉
      setPullDistance(Math.min(diff * 0.4, threshold * 2));
    }
  }, [enabled, threshold]);

  const handleTouchEnd = useCallback(async () => {
    if (pullDistance >= threshold && !refreshing) {
      setRefreshing(true);
      try {
        await onRefresh();
      } catch {
        // ignore
      } finally {
        setRefreshing(false);
      }
    }
    setPullDistance(0);
    startY.current = 0;
  }, [pullDistance, threshold, refreshing, onRefresh]);

  useEffect(() => {
    const el = containerRef.current || document;
    el.addEventListener('touchstart', handleTouchStart, { passive: true });
    el.addEventListener('touchmove', handleTouchMove, { passive: true });
    el.addEventListener('touchend', handleTouchEnd);
    return () => {
      el.removeEventListener('touchstart', handleTouchStart);
      el.removeEventListener('touchmove', handleTouchMove);
      el.removeEventListener('touchend', handleTouchEnd);
    };
  }, [handleTouchStart, handleTouchMove, handleTouchEnd]);

  return { ref: containerRef, refreshing, pullDistance };
}
