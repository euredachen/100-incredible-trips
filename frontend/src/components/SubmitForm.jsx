import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const PLACEHOLDER_IMG = 'https://images.pexels.com/photos/33639953/pexels-photo-33639953.jpeg?auto=compress&cs=tinysrgb&w=800';

export default function SubmitForm({ onCreated }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [stage, setStage] = useState(-1);  // -1=idle, 0=searching/building, 1=countdown
  const [progress, setProgress] = useState(0);  // 0-100
  const [countdown, setCountdown] = useState(3);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);
  const countdownRef = useRef(null);

  useEffect(() => () => {
    if (pollRef.current) clearTimeout(pollRef.current);
    if (countdownRef.current) clearInterval(countdownRef.current);
  }, []);

  const startCountdown = () => {
    setStage(1);
    setCountdown(3);
    let n = 3;
    countdownRef.current = setInterval(() => {
      n--;
      setCountdown(n);
      if (n <= 0) {
        clearInterval(countdownRef.current);
        window.location.reload();
      }
    }, 1000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const query = name.trim();
    if (!query) return;

    setSubmitting(true);
    setError(null);
    setStage(0);
    setProgress(5);

    try {
      const res = await fetch('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: query,
          subtitle: '',
          destination: query,
          country: '',
          cover_image: PLACEHOLDER_IMG,
          experience_type: 'adventure',
          uniqueness_score: 8,
          visual_style: 'ocean',
          content: `## ${query}\n\n内容自动丰富中...`,
          story: '',
          best_season: '全年皆可',
          duration_hours: 8,
          difficulty: 'moderate',
          image_source: 'Pexels',
          image_source_url: 'https://www.pexels.com/',
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const trip = await res.json();
      setName('');
      if (onCreated) onCreated(trip);

      // 触发后台 enrichment
      fetch(`/api/trips/${trip.id}/enrich`, { method: 'POST' }).catch(() => {});

      // 轮询 enrichment 完成状态
      let prog = 10;
      const poll = async () => {
        try {
          const r = await fetch(`/api/trips/${trip.id}`);
          const t = await r.json();
          const done = t.cover_image
            && t.cover_image.startsWith('/images/')
            && !t.cover_image.includes('pexels-photo-33639953');
          if (done) {
            setProgress(100);
            setTimeout(startCountdown, 400);
          } else {
            prog = Math.min(prog + 8, 95);
            setProgress(prog);
            pollRef.current = setTimeout(poll, 1500);
          }
        } catch {
          pollRef.current = setTimeout(poll, 2000);
        }
      };
      pollRef.current = setTimeout(poll, 1200);
    } catch (err) {
      setError(err.message);
      setStage(-1);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mb-6">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 transition-all duration-200"
        style={{ color: 'var(--accent-warm)', fontSize: '15px', fontWeight: 500 }}
      >
        <span style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 26, height: 26, borderRadius: '50%',
          backgroundColor: open ? 'var(--accent-warm)' : 'var(--accent-warm-light)',
          color: open ? '#fff' : 'var(--accent-warm)',
          fontSize: '16px', fontWeight: 600, transition: 'all 0.2s',
          transform: open ? 'rotate(45deg)' : 'rotate(0)',
        }}>{open ? '−' : '+'}</span>
        <span style={{
          background: 'linear-gradient(135deg, var(--accent-warm), #FF8C5A)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          推荐不可思议的体验
        </span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.form
            onSubmit={handleSubmit}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 overflow-hidden"
          >
            <div className="glass-card p-4 flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="输入景点名称，如：冰岛火山内部徒步"
                disabled={submitting || stage >= 0}
                className="flex-1 px-4 py-2.5 rounded-full text-sm border outline-none"
                style={{
                  borderColor: stage >= 0 ? 'var(--accent-warm)' : 'var(--color-border)',
                  background: 'var(--color-card-bg)',
                  color: 'var(--color-text)',
                }}
              />
              <button
                type="submit"
                disabled={submitting || !name.trim() || stage === 0}
                className="px-6 py-2.5 rounded-full text-sm font-semibold text-white
                           transition-all disabled:opacity-40 shrink-0"
                style={{ backgroundColor: 'var(--accent-warm)' }}
              >
                {stage === 0 ? '处理中...' : '提交'}
              </button>
            </div>

            {/* 进度提示 */}
            {stage === 0 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="flex items-center gap-2 mt-3 glass-card p-3">
                <div className="w-4 h-4 border-2 rounded-full animate-spin shrink-0"
                     style={{ borderColor: 'var(--color-border)', borderTopColor: 'var(--color-text-secondary)' }} />
                <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                  {progress <= 33 ? '搜索中……' : '正在构建网页'}
                </p>
                <div className="flex-1 h-1 rounded-full overflow-hidden ml-2" style={{ background: 'var(--color-border)' }}>
                  <div className="h-full rounded-full transition-all duration-500" style={{
                    width: `${progress}%`,
                    background: 'var(--color-text-secondary)',
                  }} />
                </div>
              </motion.div>
            )}

            {/* 倒计时 */}
            {stage === 1 && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="mt-3 glass-card p-3 text-center">
                <p className="text-sm" style={{ color: 'var(--color-text)' }}>
                  全部完成，<span style={{ fontWeight: 600 }}>{countdown}</span> 秒后自动刷新
                </p>
              </motion.div>
            )}

            {error && (
              <p className="text-xs mt-2" style={{ color: '#EF4444' }}>{error}</p>
            )}
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}
