const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

async function request(path, params = {}) {
  const url = new URL(`${BASE_URL}${path}`, window.location.origin);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, value);
    }
  });

  const res = await fetch(url.toString());
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/** GET /api/trips — 分页列表 */
export function getTrips({ type, min_uniqueness, visual_style, search, page = 1, limit = 20 } = {}) {
  return request('/trips', { type, min_uniqueness, visual_style, search, page, limit });
}

/** GET /api/trips/{id} — 详情 */
export function getTripById(id) {
  return request(`/trips/${id}`);
}

/** GET /api/trips/random — 随机推荐 */
export function getRandomTrip() {
  return request('/trips/random');
}
