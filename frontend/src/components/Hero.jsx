import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { getTrips } from '../services/api';

export default function Hero() {
  const [trips, setTrips] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  // 获取所有体验数据用于轮换
  useEffect(() => {
    getTrips({ limit: 5 })
      .then((res) => setTrips(res.items))
      .catch(() => {});
  }, []);

  // 每 5 秒轮换背景图和副标题
  useEffect(() => {
    if (trips.length === 0) return;
    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % trips.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [trips.length]);

  const currentTrip = trips[currentIndex];

  return (
    <section className="relative h-screen w-full overflow-hidden">
      {/* ── 轮换背景图（无暗化遮罩） ────────────────────────────── */}
      <AnimatePresence mode="wait">
        {currentTrip && (
          <motion.div
            key={currentTrip.id}
            className="absolute inset-0"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1.2, ease: 'easeInOut' }}
          >
            <img
              src={currentTrip.cover_image}
              alt={currentTrip.title}
              className="w-full h-full object-cover"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── 内容层（半透明毛玻璃） ───────────────────────────────── */}
      <div className="relative z-10 h-full flex flex-col items-center justify-center px-6">
        <motion.div
          className="w-full flex justify-center"
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <div
            className="text-center p-10 md:p-12"
            style={{
              maxWidth: '42rem',
              width: '90%',
              background: 'rgba(0,0,0,0.35)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              borderRadius: '20px',
              border: '1px solid rgba(255,255,255,0.12)',
            }}
          >
            {/* 标签 */}
            <motion.p
              className="tracking-[0.3em] uppercase mb-5 font-medium text-white/80"
              style={{ fontSize: '13px' }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.5 }}
            >
              飞猪 · 100种不可思议旅行
            </motion.p>

            {/* 大标题 */}
            <motion.h1
              className="font-display text-white mb-4 leading-[1.1]"
              style={{
                fontSize: 'clamp(36px, 7vw, 48px)',
                fontWeight: 600,
              }}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35, duration: 0.5 }}
            >
              <span className="text-gradient-warm">发现</span>
              <br />
              不可思议
            </motion.h1>

            {/* 轮换副标题 — 与背景图联动 */}
            <div className="h-14 mb-6 overflow-hidden">
              <AnimatePresence mode="wait">
                {currentTrip && (
                  <motion.p
                    key={currentTrip.id}
                    className="text-white/70"
                    style={{ fontSize: '18px', fontWeight: 400, lineHeight: 1.5 }}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.5 }}
                  >
                    {currentTrip.title}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>

            {/* CTA 按钮 */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              className="flex flex-col items-center gap-4"
            >
              <Link
                to="/trips"
                className="inline-flex items-center gap-2 px-6 py-2.5
                           rounded-full font-medium
                           bg-white/10 backdrop-blur-sm
                           border border-white/20
                           text-white
                           hover:bg-white hover:text-black
                           transition-all duration-300 ease-out"
                style={{ fontSize: '15px' }}
              >
                开始探索
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </Link>

              {/* 地点标注 */}
              {currentTrip && (
                <span
                  className="inline-flex items-center gap-1.5 px-3 py-1.5
                             rounded-full border text-sm"
                  style={{
                    fontSize: '13px',
                    color: 'rgba(255,255,255,0.7)',
                    borderColor: 'rgba(255,255,255,0.12)',
                    background: 'rgba(255,255,255,0.06)',
                  }}
                >
                  📍 {currentTrip.destination}，{currentTrip.country}
                </span>
              )}
            </motion.div>
          </div>
        </motion.div>

        {/* 底部轮播指示器 */}
        <div className="absolute bottom-8 flex items-center gap-2">
          {trips.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentIndex(idx)}
              className="w-2 h-2 rounded-full transition-all duration-300"
              style={{
                background: idx === currentIndex
                  ? 'rgba(255,255,255,0.8)'
                  : 'rgba(255,255,255,0.25)',
              }}
              aria-label={`切换到第 ${idx + 1} 张背景`}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
