# 核心 Prompt 记录 — 100种不可思议旅行

> 记录引导 AI（Claude Code + DeepSeek V4 Pro）开发的关键 Prompt，
> 体现 SDD → DDD → TDD → E2E 四阶段工程化拆解。

---

## 【SDD 阶段】数据建模与 API 契约

### Prompt 1：数据模型设计

```
[SDD阶段] 飞猪"100种不可思议旅行" - 数据建模与API契约

设计SQLite数据模型：
- Trip表：id, title, subtitle, cover_image, destination, country,
  experience_type(枚举6类), uniqueness_score(1-10), visual_style(枚举5类),
  content(富文本), story(情感故事), best_season, duration_hours, difficulty(3级),
  created_at, updated_at
- 5条不可思议体验样例数据（挪威极光、秘鲁死藤水、瓦努阿图火山、格陵兰雪橇、不丹寺庙）
- OpenAPI 3.0规范：GET /api/trips(分页+筛选), GET /api/trips/{id}, GET /api/trips/random
- Pydantic schemas + SQLAlchemy模型 + ER图(mermaid) + 初始化脚本
```

> **意图**：从业务文档直接推导数据模型，一次性锁定字段定义和 API 契约，避免后期返工。
> **挑战**：需要同时考虑 SQLite 约束、Pydantic 校验、OpenAPI 规范三者的字段一致性。
> **修正**：后续轮次中根据前端的实际需求补充了 `image_source` 和 `image_source_url` 字段。

### Prompt 2：API 契约修正

```
[SDD阶段 - 修正轮] 补全缺失的后端启动文件
- requirements.txt 缺少 fastapi 和 uvicorn
- 缺少 main.py 文件（FastAPI应用入口）
- openapi.yaml 未加载到应用中
```

> **意图**：第一轮 AI 生成有遗漏（依赖未声明、入口文件缺失），通过修正轮补全基础设施。
> **挑战**：AI 倾向生成"看起来完整"的代码，实际上缺少可运行的骨架。
> **修正**：明确要求输出可运行文件，并提供验证命令。

---

## 【DDD 阶段】前端组件与页面

### Prompt 3：前端商业化品质升级

```
[DDD阶段] 基于已验证 API 生成 React + TailwindCSS 前端（亮暗色模式）

设计要求：
- 配色：暗黑纯黑底 #000000 + 毛玻璃卡片 rgba(20,20,30,0.7)
- 字体：Inter + Playfair Display（Google Fonts）
- 亮暗切换：右上角太阳/月亮按钮
- Hero区 100vh：随机背景图 + 轮播副标题5秒切换
- 列表页：筛选栏吸顶 + 卡片3/2/1列 + 无限滚动 + 骨架屏
- 详情页：Hero 60vh + 故事区 text-xl italic + 同类推荐
- Framer Motion 入场动画
- 移动端响应式 + 随机探索按钮
```

> **意图**：从零生成17个前端文件，要求达到商业化视觉品质。
> **挑战**：亮暗模式切换需要全局 CSS 变量 + Tailwind darkMode 双重机制；无限滚动需要 IntersectionObserver 与 React 状态同步。
> **修正**：多轮迭代优化毛玻璃效果（backdrop-blur-xl + 0.5px 边框）、配色方案（ColorThief 从背景图提取色阶）。

### Prompt 4：图片资源 + 明暗模式修复

```
[DDD阶段 - 第3轮优化] 图片资源、明暗模式、卡片尺寸修复
- Pexels MCP 搜索真实旅行照片（巴哈马猪岛、极光雪原）
- ColorThief 提取主色+色阶生成 Tailwind 配置
- 亮暗模式背景图：明亮→海洋，暗黑→极光
- 卡片固定高度 + flex 布局 + hover 上浮效果
- 详情页文字全用 CSS 变量适配暗亮
```

> **意图**：解决 AI 生成的"假图"问题——用 Pexels API 下载真实照片并提取配色，体现 MCP 工具链集成。
> **挑战**：Pexels 搜索中文关键词无结果，需映射为英文搜索词；ColorThief 提取的色阶需转换为 Tailwind 50-900 格式。
> **修正**：发现 surface opacity 设为 10% 时背景图才可见，调整了毛玻璃透明度体系。

---

## 【TDD 阶段】测试用例编写与业务实现

### Prompt 5：后端 TDD 测试

```
[后端开发任务 - TDD + E2E 测试阶段]

编写测试文件，遵循红-绿-重构循环：
1. conftest.py：内存 SQLite + TestClient fixtures
2. test_models.py：17个模型测试（字段约束、枚举值、ORM查询）
3. test_services.py：18个服务测试（筛选组合、分页边界、空库处理）
4. test_api.py：27个API契约测试（响应结构、状态码、CORS、422校验）
5. E2E：Playwright 用户旅程
```

> **意图**：严格 TDD 流程——先写测试（红灯），再补服务层代码（绿灯），最后覆盖率检查（重构）。
> **挑战**：uniqueness_score 范围 1-10，测试中需验证 0/11/-1 被拒绝；created_at 和 updated_at 因 lambda 两次调用有微秒差，断言需用 <1s。
> **修正**：初始断言 `==` 失败，改为 `abs(delta) < 1.0`；multiple_trips fixture 数据有4条 ≥9分，断言从3改为4。

---

## 【E2E 阶段】系统级端到端测试

### Prompt 6：E2E + CI 配置

```
E2E 测试 - 前后端完整链路

Playwright 测试用例：
- 首页 → 列表页 → 详情页 完整流程
- 筛选功能验证
- 亮暗色模式切换验证
- API 契约测试（直接 HTTP 请求）
- 并发性能测试
```

> **意图**：验证前后端完整链路，确保用户操作路径可达。
> **挑战**：Playwright 需要同时启动前后端两个 webServer；API 测试使用 request fixture 绕过浏览器直接测 HTTP 层。
> **修正**：配置 reuseExistingServer 避免重复启动。

---

## 总结：AI 引导策略

| 阶段 | Prompt 数量 | 关键策略 |
|------|:---:|------|
| SDD | 2 | 业务文档 → 精确字段定义 → 补漏修正 |
| DDD | 2 | 设计规格 → 17文件生成 → 视觉细节迭代 |
| TDD | 1 | 红-绿-重构 → 93% 覆盖率 |
| E2E | 1 | 用户旅程 → Playwright 自动化 |
| **总计** | **6** | 每阶段一个核心 Prompt + 修正轮 |
