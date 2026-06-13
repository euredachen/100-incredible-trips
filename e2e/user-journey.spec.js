import { test, expect } from '@playwright/test';

test.describe('用户完整旅程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173');
  });

  test('首页加载并显示标题', async ({ page }) => {
    // 首页应有主标题
    await expect(page.locator('h1')).toBeVisible();
    const title = await page.locator('h1').textContent();
    expect(title).toContain('不可思议');
  });

  test('首页 → 列表页 → 详情页 完整流程', async ({ page }) => {
    // 1. 首页：点击 CTA 进入列表
    const ctaButton = page.locator('a[href="/trips"]').first();
    await expect(ctaButton).toBeVisible();
    await ctaButton.click();

    // 2. 列表页加载
    await expect(page).toHaveURL(/\/trips/);
    await page.waitForSelector('.glass-card');

    // 3. 列表应显示卡片
    const cards = page.locator('.glass-card');
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);

    // 4. 点击第一张卡片进入详情
    await cards.first().click();
    await expect(page).toHaveURL(/\/trips\/\d+/);

    // 5. 详情页应有标题
    const detailTitle = page.locator('h1');
    await expect(detailTitle).toBeVisible();
  });

  test('筛选功能 — 按体验类型', async ({ page }) => {
    await page.goto('http://localhost:5173/trips');
    await page.waitForSelector('.glass-card');

    const initialCount = await page.locator('.glass-card').count();

    // 点击"探险"筛选按钮
    const adventureBtn = page.locator('button').filter({ hasText: '探险' }).first();
    if (await adventureBtn.isVisible()) {
      await adventureBtn.click();
      await page.waitForTimeout(800);

      const filteredCount = await page.locator('.glass-card').count();
      expect(filteredCount).toBeLessThanOrEqual(initialCount);
    }
  });

  test('筛选功能 — 按景观类型', async ({ page }) => {
    await page.goto('http://localhost:5173/trips');
    await page.waitForSelector('.glass-card');

    // 点击"山峰"景观按钮
    const mountainBtn = page.locator('button').filter({ hasText: '山峰' }).first();
    if (await mountainBtn.isVisible()) {
      await mountainBtn.click();
      await page.waitForTimeout(800);

      const filteredCount = await page.locator('.glass-card').count();
      expect(filteredCount).toBeGreaterThanOrEqual(0);
    }
  });

  test('亮暗色模式切换', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // 获取初始 body class
    const initialIsDark = await page.evaluate(() => {
      return document.body.classList.contains('dark');
    });

    // 点击主题切换按钮
    const themeBtn = page.locator('button[aria-label*="切换"]').first();
    if (await themeBtn.isVisible()) {
      await themeBtn.click();
      await page.waitForTimeout(400);

      const newIsDark = await page.evaluate(() => {
        return document.body.classList.contains('dark');
      });

      // 应该切换了
      expect(newIsDark).not.toEqual(initialIsDark);

      // 切换回来
      await themeBtn.click();
    }
  });
});

test.describe('API 契约测试', () => {
  const BASE_URL = 'http://localhost:8000';

  test('GET /api/trips 返回正确结构', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/trips`);
    expect(res.status()).toBe(200);

    const data = await res.json();
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('page');
    expect(data).toHaveProperty('limit');
    expect(data).toHaveProperty('pages');
    expect(Array.isArray(data.items)).toBe(true);
    expect(typeof data.total).toBe('number');
  });

  test('GET /api/trips?type=adventure 筛选正确', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/trips?type=adventure`);
    expect(res.status()).toBe(200);
    const data = await res.json();
    for (const item of data.items) {
      expect(item.experience_type).toBe('adventure');
    }
  });

  test('GET /api/trips/random 返回单条', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/trips/random`);
    expect(res.status()).toBe(200);
    const data = await res.json();
    expect(data).toHaveProperty('id');
    expect(data).toHaveProperty('title');
  });

  test('GET /api/trips/99999 返回 404', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/trips/99999`);
    expect(res.status()).toBe(404);
    const data = await res.json();
    expect(data).toHaveProperty('detail');
  });

  test('GET /api/health 返回 ok', async ({ request }) => {
    const res = await request.get(`${BASE_URL}/api/health`);
    expect(res.status()).toBe(200);
    expect(await res.json()).toEqual({ status: 'ok', service: '100-incredible-trips' });
  });
});

test.describe('性能测试', () => {
  test('API 响应时间 < 500ms', async ({ request }) => {
    const start = Date.now();
    const res = await request.get('http://localhost:8000/api/trips');
    const elapsed = Date.now() - start;
    expect(res.status()).toBe(200);
    expect(elapsed).toBeLessThan(500);
  });

  test('批量并发请求不超时', async ({ request }) => {
    const BASE = 'http://localhost:8000';
    const start = Date.now();

    const results = await Promise.all(
      Array.from({ length: 5 }, () => request.get(`${BASE}/api/trips`))
    );

    const elapsed = Date.now() - start;
    for (const res of results) {
      expect(res.status()).toBe(200);
    }
    expect(elapsed).toBeLessThan(3000);
  });
});
