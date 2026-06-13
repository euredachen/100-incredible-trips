import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { getTripById, getTrips } from '../services/api';
import StarRating from '../components/StarRating';
import Card from '../components/Card';

const typeLabels = {
  adventure: '探险',
  cultural: '人文',
  nature: '自然',
  food: '美食',
  art: '艺术',
  wellness: '康养',
};

const difficultyLabels = {
  easy: '轻松',
  moderate: '中等',
  hard: '挑战',
};

const landscapeLabels = {
  urban: '🏙️ 城市',
  ocean: '🌊 海洋',
  forest: '🌲 森林',
  mountain: '⛰️ 山峰',
  snow: '❄️ 雪原',
};

export default function TripDetailPage() {
  const { id } = useParams();
  const [trip, setTrip] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showBackTop, setShowBackTop] = useState(false);
  const [bgLoaded, setBgLoaded] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setBgLoaded(false);
    window.scrollTo(0, 0);

    getTripById(id)
      .then(async (data) => {
        setTrip(data);
        try {
          const res = await getTrips({ type: data.experience_type, limit: 4 });
          setRelated(res.items.filter((t) => t.id !== data.id).slice(0, 3));
        } catch {
          setRelated([]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    const onScroll = () => setShowBackTop(window.scrollY > window.innerHeight);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = useCallback(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // ── 加载状态 ──────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center"
           style={{ backgroundColor: 'var(--color-surface)' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-2 rounded-full animate-spin"
               style={{ borderColor: 'rgba(255,107,53,0.3)', borderTopColor: 'var(--color-accent-warm)' }} />
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>加载中...</p>
        </div>
      </div>
    );
  }

  // ── 错误状态 ──────────────────────────────────────────────────────────
  if (error || !trip) {
    return (
      <div className="min-h-screen flex items-center justify-center"
           style={{ backgroundColor: 'var(--color-surface)' }}>
        <div className="text-center">
          <p className="text-lg mb-4" style={{ color: 'var(--color-text-secondary)' }}>
            {error || '体验不存在'}
          </p>
          <Link to="/trips" className="px-6 py-2.5 rounded-full text-white"
                style={{ backgroundColor: 'var(--color-accent-warm)' }}>
            返回列表
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: 'var(--color-surface)', minHeight: '100vh' }}>
      {/* ── Hero 区 (60vh) ───────────────────────────────────────────── */}
      <section className="relative h-[60vh] min-h-[400px] overflow-hidden">
        <div className="absolute inset-0 bg-black">
          {trip.cover_image && (
            <img
              src={trip.cover_image}
              alt=""
              className={`w-full h-full object-cover transition-opacity duration-700
                          ${bgLoaded ? 'opacity-50' : 'opacity-0'}`}
              onLoad={() => setBgLoaded(true)}
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/60 to-black/40" />
        </div>

        <div className="relative z-10 h-full flex flex-col justify-end pb-12">
          <div className="max-w-[1280px] mx-auto px-6 md:px-10 w-full">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <div className="flex items-center gap-2 text-white/50 text-sm mb-4">
                <Link to="/trips" className="hover:text-white transition-colors">探索体验</Link>
                <span>/</span>
                <span className="text-white/70">{trip.destination}</span>
              </div>

              <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold
                            text-white mb-3 leading-tight">
                {trip.title}
              </h1>

              {trip.subtitle && (
                <p className="text-lg sm:text-xl text-white/60 font-light max-w-2xl">
                  {trip.subtitle}
                </p>
              )}

              <p className="text-white/40 text-sm mt-3">
                📍 {trip.destination}，{trip.country}
                {trip.best_season && ` · 🗓️ ${trip.best_season}`}
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── 信息卡片 ──────────────────────────────────────────────────── */}
      <section className="relative -mt-6 z-20">
        <div className="max-w-[1280px] mx-auto px-6 md:px-10">
          <motion.div
            className="glass-card p-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
          >
            <InfoItem label="体验类型" icon="🏷️"
              value={typeLabels[trip.experience_type] || trip.experience_type} />
            <InfoItem label="不可思议指数" icon="⭐"
              value={<StarRating score={trip.uniqueness_score} size="md" />}
              extra={`${trip.uniqueness_score}/10`} />
            <InfoItem label="体验时长" icon="⏱️"
              value={trip.duration_hours
                ? trip.duration_hours >= 24
                  ? `${Math.floor(trip.duration_hours / 24)}天${trip.duration_hours % 24 > 0 ? `${trip.duration_hours % 24}小时` : ''}`
                  : `${trip.duration_hours}小时`
                : '—'} />
            <InfoItem label="难度" icon="💪"
              value={difficultyLabels[trip.difficulty] || trip.difficulty} />
            <InfoItem label="最佳季节" icon="🌤️"
              value={trip.best_season || '全年皆可'} />
          </motion.div>
        </div>
      </section>

      {/* ── 内容区 ────────────────────────────────────────────────────── */}
      <section className="max-w-[1280px] mx-auto px-6 md:px-10 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 主内容 (2/3) */}
          <div className="lg:col-span-2 space-y-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="font-display text-2xl font-bold mb-5"
                  style={{ color: 'var(--color-heading)' }}>体验详情</h2>
              <div className="glass-card p-6 sm:p-8">
                <div className="prose max-w-none
                                prose-headings:font-display prose-p:leading-relaxed"
                     style={{ color: 'var(--color-text)' }}>
                  <ReactMarkdown>{trip.content}</ReactMarkdown>
                </div>
              </div>
            </motion.div>

            {trip.story && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.1 }}
              >
                <h2 className="font-display text-2xl font-bold mb-5"
                    style={{ color: 'var(--color-heading)' }}>背后的故事</h2>
                <div className="glass-card p-6 sm:p-8 border-l-4"
                     style={{ borderLeftColor: 'var(--color-accent-cool)' }}>
                  <div className="text-lg leading-relaxed italic font-light whitespace-pre-line"
                       style={{ color: 'var(--color-text)', opacity: 0.85 }}>
                    {trip.story}
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          {/* 侧边栏 (1/3) */}
          <aside className="space-y-6">
            <div className="glass-card p-5 sticky top-24">
              <h3 className="font-display text-lg font-semibold mb-4"
                  style={{ color: 'var(--color-heading)' }}>快速信息</h3>
              <dl className="space-y-3 text-sm">
                <InfoRow label="国家" value={trip.country} />
                <InfoRow label="目的地" value={trip.destination} />
                <InfoRow label="景观类型"
                  value={landscapeLabels[trip.visual_style] || trip.visual_style} />
              </dl>

              {/* ── 图片来源 ──────────────────────────────────────────── */}
              {trip.image_source && (
                <div className="mt-5 pt-4" style={{ borderTop: `0.5px solid var(--color-card-border)` }}>
                  <p className="text-xs mb-1" style={{ color: 'var(--color-text-secondary)' }}>
                    📷 图片来源
                  </p>
                  {trip.image_source_url ? (
                    <a
                      href={trip.image_source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs underline hover:no-underline transition-all"
                      style={{ color: 'var(--color-accent-cool)' }}
                    >
                      {trip.image_source}
                    </a>
                  ) : (
                    <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
                      {trip.image_source}
                    </span>
                  )}
                </div>
              )}

              {/* ── 飞猪预订按钮 ────────────────────────────────── */}
              <div className="mt-5 pt-4" style={{ borderTop: `0.5px solid var(--color-card-border)` }}>
                <a
                  href={`https://www.fliggy.com/search?q=${encodeURIComponent(trip.destination + ' ' + trip.country + ' 旅游')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full px-4 py-2.5
                             rounded-full text-sm font-medium
                             transition-all duration-200"
                  style={{
                    backgroundColor: 'var(--color-accent-warm)',
                    color: '#fff',
                  }}
                >
                  🎫 在飞猪预订
                </a>
              </div>

              {/* ── 外部来源 ────────────────────────────────────── */}
              <ExternalSources tripId={trip.id} />
            </div>
          </aside>
        </div>

        {/* ── 推荐同类体验 ──────────────────────────────────────────── */}
        {related.length > 0 && (
          <motion.section
            className="mt-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="font-display text-2xl font-bold mb-6"
                style={{ color: 'var(--color-heading)' }}>
              更多{typeLabels[trip.experience_type]}体验
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 items-stretch">
              {related.map((t) => (
                <Card key={t.id} trip={t} />
              ))}
            </div>
          </motion.section>
        )}
      </section>

      {/* ── 返回顶部按钮 ─────────────────────────────────────────────── */}
      {showBackTop && (
        <motion.button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 z-50 w-12 h-12 rounded-full
                     text-white shadow-lg flex items-center justify-center transition-colors"
          style={{ backgroundColor: 'var(--color-accent-warm)' }}
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

// ── 子组件 ──────────────────────────────────────────────────────────────────

function InfoItem({ label, value, extra, icon }) {
  return (
    <div className="flex flex-col items-center text-center gap-1">
      <span className="text-lg">{icon}</span>
      <span className="text-xs uppercase tracking-wide"
            style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
      <span className="text-sm font-semibold flex items-center gap-1"
            style={{ color: 'var(--color-text)' }}>{value}</span>
      {extra && (
        <span className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>{extra}</span>
      )}
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between">
      <dt style={{ color: 'var(--color-text-secondary)' }}>{label}</dt>
      <dd className="font-medium" style={{ color: 'var(--color-text)' }}>{value}</dd>
    </div>
  );
}

// ── 外部来源组件 ──────────────────────────────────────────────────────────

function ExternalSources({ tripId }) {
  const [sources, setSources] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [saving, setSaving] = useState(false);

  // 加载已有的外部来源
  useEffect(() => {
    fetch(`/api/trips/${tripId}/external-sources`)
      .then((r) => r.json())
      .then((d) => setSources(d.sources || []))
      .catch(() => {});
  }, [tripId]);

  const handleAdd = async () => {
    if (!url || !title) return;
    setSaving(true);
    try {
      const res = await fetch(`/api/trips/${tripId}/external-sources`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'external', url, title, snippet: '' }),
      });
      const data = await res.json();
      if (data.success) {
        setSources((prev) => [...prev, data.source]);
        setUrl('');
        setTitle('');
        setShowForm(false);
      }
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-5 pt-4" style={{ borderTop: `0.5px solid var(--color-card-border)` }}>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold" style={{ color: 'var(--color-text)' }}>
          🔗 外部来源
        </h4>
        <button
          onClick={() => setShowForm(!showForm)}
          className="text-xs px-2 py-1 rounded-full transition-colors"
          style={{
            color: 'var(--color-accent-cool)',
            border: `0.5px solid var(--color-accent-cool)`,
          }}
        >
          {showForm ? '取消' : '+ 添加'}
        </button>
      </div>

      {/* 已有来源列表 */}
      {sources.length > 0 && (
        <div className="space-y-2 mb-3">
          {sources.map((src, idx) => (
            <a
              key={idx}
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-xs p-2 rounded-lg transition-colors hover:underline"
              style={{
                color: 'var(--color-text)',
                background: 'var(--color-card-bg)',
              }}
            >
              {src.title}
            </a>
          ))}
        </div>
      )}

      {/* 添加表单 */}
      {showForm && (
        <div className="space-y-2">
          <input
            type="text"
            placeholder="来源标题（如 Wikipedia）"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-3 py-1.5 rounded-lg text-sm border"
            style={{
              borderColor: 'var(--color-card-border)',
              background: 'var(--color-card-bg)',
              color: 'var(--color-text)',
            }}
          />
          <input
            type="url"
            placeholder="https://..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full px-3 py-1.5 rounded-lg text-sm border"
            style={{
              borderColor: 'var(--color-card-border)',
              background: 'var(--color-card-bg)',
              color: 'var(--color-text)',
            }}
          />
          <button
            onClick={handleAdd}
            disabled={saving || !url || !title}
            className="w-full px-4 py-1.5 rounded-full text-sm font-medium text-white
                       transition-all disabled:opacity-40"
            style={{ backgroundColor: 'var(--color-accent-warm)' }}
          >
            {saving ? '保存中...' : '保存来源'}
          </button>
        </div>
      )}

      {/* ── 社区共建邀请 ──────────────────────────────────── */}
      <p
        className="text-xs mt-4 leading-relaxed"
        style={{ color: 'var(--color-text-secondary)', opacity: 0.5 }}
      >
        有网页推荐？添加到此页面，与大家一起共建网站～
      </p>
    </div>
  );
}
