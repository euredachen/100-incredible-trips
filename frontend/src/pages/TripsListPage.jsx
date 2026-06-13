import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getTrips, getRandomTrip } from '../services/api';
import usePullToRefresh from '../hooks/usePullToRefresh';
import Card from '../components/Card';
import SkeletonCard from '../components/SkeletonCard';
import FilterBar from '../components/FilterBar';
import SubmitForm from '../components/SubmitForm';

export default function TripsListPage() {
  const navigate = useNavigate();

  // 列表状态
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState(null);

  // 筛选状态
  const [type, setType] = useState(null);
  const [landscape, setLandscape] = useState(null);
  const [minStars, setMinStars] = useState(0);

  // 无限滚动哨兵 & 返回顶部
  const sentinelRef = useRef(null);
  const [showBackTop, setShowBackTop] = useState(false);

  useEffect(() => {
    const onScroll = () => setShowBackTop(window.scrollY > 300);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // 构建 API 参数
  const buildParams = useCallback(
    (pageNum) => {
      const params = { page: pageNum, limit: 20 };
      if (type) params.type = type;
      if (landscape) params.visual_style = landscape;
      if (minStars > 0) params.min_uniqueness = minStars * 2;
      return params;
    },
    [type, landscape, minStars]
  );

  // 初次加载 / 筛选项变化 → 重置列表
  useEffect(() => {
    setTrips([]);
    setPage(1);
    setLoading(true);
    setError(null);

    getTrips(buildParams(1))
      .then((res) => {
        setTrips(res.items);
        setTotalPages(res.pages);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [type, landscape, minStars]);

  // 无限滚动 — 加载更多
  useEffect(() => {
    if (page <= 1) return;

    setLoadingMore(true);
    getTrips(buildParams(page))
      .then((res) => {
        setTrips((prev) => [...prev, ...res.items]);
        setTotalPages(res.pages);
      })
      .catch(() => {})
      .finally(() => setLoadingMore(false));
  }, [page]);

  // Intersection Observer
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loading && !loadingMore && page < totalPages) {
          setPage((p) => p + 1);
        }
      },
      { rootMargin: '200px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loading, loadingMore, page, totalPages]);

  // 下拉刷新
  const handleRefresh = useCallback(async () => {
    setPage(1);
    const res = await getTrips(buildParams(1));
    setTrips(res.items);
    setTotalPages(res.pages);
  }, [buildParams]);

  const { pullDistance, refreshing } = usePullToRefresh(handleRefresh);

  // 随机探索
  const handleRandom = async () => {
    try {
      const trip = await getRandomTrip();
      navigate(`/trips/${trip.id}`);
    } catch {
      // ignore
    }
  };

  return (
    <div style={{ backgroundColor: 'var(--color-surface)', minHeight: '100vh' }}>
      {/* 筛选栏 */}
      <FilterBar
        activeType={type}
        onTypeChange={setType}
        activeLandscape={landscape}
        onLandscapeChange={setLandscape}
        minStars={minStars}
        onStarsChange={setMinStars}
      />

      {/* 内容区 */}
      <div className="max-w-[1280px] mx-auto px-6 md:px-10 py-10">

        {/* 下拉刷新指示器 */}
        {pullDistance > 0 && (
          <div className="flex justify-center mb-4 transition-all"
               style={{ transform: `translateY(${Math.min(pullDistance, 40)}px)`, opacity: Math.min(pullDistance / 60, 1) }}>
            <div className={`w-8 h-8 border-2 rounded-full ${refreshing ? 'animate-spin' : ''}`}
                 style={{ borderColor: 'var(--color-border)', borderTopColor: 'var(--accent-warm)' }} />
          </div>
        )}

        {/* 提交新体验表单 */}
        <SubmitForm onCreated={() => { setPage(1); setLoading(true); getTrips(buildParams(1)).then(res => { setTrips(res.items); setTotalPages(res.pages); }).finally(() => setLoading(false)); }} />

        {/* 标题行 + 随机按钮 */}
        <div className="flex items-center justify-between mb-10">
          <motion.h2
            className="font-display font-semibold"
            style={{
              fontSize: 'clamp(28px, 5vw, 36px)',
              color: 'var(--color-text)',
            }}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            探索体验
          </motion.h2>

          {/* 随机探索按钮 — 60%不透明度 + 80px模糊 */}
          <motion.button
            onClick={handleRandom}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 px-4 py-2 rounded-full
                       border text-sm font-medium transition-all duration-200"
            style={{
              borderColor: 'var(--accent-warm)',
              color: 'var(--accent-warm)',
              opacity: 0.6,
              backdropFilter: 'blur(80px)',
              WebkitBackdropFilter: 'blur(80px)',
              backgroundColor: 'transparent',
            }}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16" />
            </svg>
            随机探索
          </motion.button>
        </div>

        {/* 错误状态 */}
        {error && (
          <div className="text-center py-20">
            <p style={{ color: 'var(--color-text-secondary)' }} className="mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 rounded-full text-white"
              style={{ backgroundColor: 'var(--color-accent-warm)' }}
            >
              重试
            </button>
          </div>
        )}

        {/* 卡片网格 — 桌面3列 / 平板2列 / 手机1列 */}
        {!error && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
            {/* 骨架屏 */}
            {loading &&
              Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={`sk-${i}`} />)}

            {/* 卡片 — 页面切换 fade + scale */}
            {trips.map((trip, idx) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: idx * 0.05, ease: 'easeOut' }}
              >
                <Card trip={trip} index={idx} />
              </motion.div>
            ))}
          </div>
        )}

        {/* 加载更多骨架 */}
        {loadingMore && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-6 items-stretch">
            {Array.from({ length: 3 }).map((_, i) => (
              <SkeletonCard key={`more-sk-${i}`} />
            ))}
          </div>
        )}

        {/* 空状态 */}
        {!loading && trips.length === 0 && !error && (
          <div className="text-center py-20">
            <p style={{ color: 'var(--color-text-secondary)' }} className="text-lg">
              没有找到匹配的体验
            </p>
            <p style={{ color: 'var(--color-text-secondary)', opacity: 0.5 }} className="text-sm mt-2">
              试试调整筛选条件
            </p>
          </div>
        )}

        {/* 无限滚动哨兵 */}
        {page < totalPages && (
          <div ref={sentinelRef} className="h-10" />
        )}

        {/* 已加载全部 */}
        {page >= totalPages && trips.length > 0 && (
          <p className="text-center text-sm mt-10 pb-10"
             style={{ color: 'var(--color-text-secondary)', opacity: 0.4 }}>
            — 已展示全部体验 —
          </p>
        )}
      </div>

      {/* 返回顶部 — banner 消失后出现 */}
      {showBackTop && (
        <motion.button
          onClick={scrollToTop}
          className="fixed bottom-20 sm:bottom-6 right-6 z-50 w-11 h-11 rounded-full
                     flex items-center justify-center shadow-lg"
          style={{ backgroundColor: 'var(--accent-warm)', color: '#fff' }}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          whileTap={{ scale: 0.9 }}
          aria-label="返回顶部"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M18 15l-6-6-6 6" />
          </svg>
        </motion.button>
      )}
    </div>
  );
}
