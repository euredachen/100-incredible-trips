/**
 * 轻量级数据埋点 — MVP 阶段 console.log，生产可切换 sendBeacon
 */
const tracker = {
  _queue: [],
  _sessionId: Date.now().toString(36),

  event(name, data = {}) {
    const payload = {
      event: name,
      data,
      ts: Date.now(),
      session: this._sessionId,
      page: typeof location !== 'undefined' ? location.pathname : '',
    };
    console.log('[📊]', payload.event, payload.data);

    // 生产：navigator.sendBeacon
    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      this._queue.push(payload);
      if (this._queue.length >= 5) this.flush();
    }
  },

  flush() {
    if (this._queue.length === 0) return;
    const batch = this._queue.splice(0);
    navigator.sendBeacon('/api/analytics/event', JSON.stringify(batch));
  },

  pageView() { this.event('page_view'); },
  filterUse(type, value) { this.event('filter_use', { type, value }); },
  cardClick(tripId) { this.event('card_click', { tripId }); },
  bookingClick(tripId) { this.event('booking_click', { tripId }); },
  shareClick(tripId) { this.event('share_click', { tripId }); },
  themeToggle(mode) { this.event('theme_toggle', { mode }); },
  externalSourceClick(tripId, sourceType) { this.event('external_source_click', { tripId, sourceType }); },
  searchUse(query) { this.event('search_use', { query }); },
  starFilter(minStars) { this.event('star_filter', { minStars }); },
  scrollDepth(pct) { this.event('scroll_depth', { pct }); },
};

export default tracker;
