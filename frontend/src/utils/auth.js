/**
 * 模拟用户登录系统 — localStorage 持久化
 *
 * MVP 阶段不接入真实 OAuth，用手机号模拟。
 * 数据结构向后兼容真实用户系统。
 */

const AUTH_KEY = 'feizhu_user';

const DEFAULT_USER = {
  phone: '',
  name: '',
  avatar: '',
  favorites: [],    // trip IDs
  wantToGo: [],     // trip IDs
  beenThere: [],    // trip IDs
  searchHistory: [], // {query, ts}[]
  createdAt: null,
};

export function getUser() {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isLoggedIn() {
  const u = getUser();
  return u && u.phone;
}

export function login(phone) {
  const existing = getUser();
  const user = {
    ...DEFAULT_USER,
    ...(existing || {}),
    phone,
    name: existing?.name || `旅行者${phone.slice(-4)}`,
    createdAt: existing?.createdAt || new Date().toISOString(),
  };
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
  return user;
}

export function logout() {
  localStorage.removeItem(AUTH_KEY);
}

export function updateProfile(patch) {
  const user = getUser();
  if (!user) return null;
  const updated = { ...user, ...patch };
  localStorage.setItem(AUTH_KEY, JSON.stringify(updated));
  return updated;
}

// ── 收藏 ──────────────────────────────────────────────────────────

export function toggleFavorite(tripId) {
  let user = getUser();
  if (!user) user = login('13800000000'); // 自动注册
  const idx = user.favorites.indexOf(tripId);
  idx > -1 ? user.favorites.splice(idx, 1) : user.favorites.push(tripId);
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
  return !idx; // true=已收藏, false=已取消
}

export function isFavorite(tripId) {
  const user = getUser();
  return user ? user.favorites.includes(tripId) : false;
}

// ── 想去/去过 ──────────────────────────────────────────────────────

export function toggleWantToGo(tripId) {
  let user = getUser();
  if (!user) user = login('13800000000');
  const idx = user.wantToGo.indexOf(tripId);
  idx > -1 ? user.wantToGo.splice(idx, 1) : user.wantToGo.push(tripId);
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

export function toggleBeenThere(tripId) {
  let user = getUser();
  if (!user) user = login('13800000000');
  const idx = user.beenThere.indexOf(tripId);
  idx > -1 ? user.beenThere.splice(idx, 1) : user.beenThere.push(tripId);
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

// ── 搜索历史 ──────────────────────────────────────────────────────

export function addSearchHistory(query) {
  const user = getUser();
  if (!user) return;
  user.searchHistory = [
    { query, ts: Date.now() },
    ...user.searchHistory.filter((h) => h.query !== query),
  ].slice(0, 10);
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

export function getSearchHistory() {
  const user = getUser();
  return user?.searchHistory || [];
}

export function clearSearchHistory() {
  const user = getUser();
  if (!user) return;
  user.searchHistory = [];
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}
