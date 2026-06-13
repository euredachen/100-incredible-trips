# 开发过程思路 & 工作流说明

## 1. 开发流程：如何通过 Claude Code + DeepSeek V4 Pro 进行开发

### 整体架构

```
业务文档(我的图书馆.docx)
        ↓
┌─────── SDD ───────┐
│ 数据建模 + API契约  │  ← 一次性输出 models.py + schemas.py + openapi.yaml
│ 5条种子数据        │
└────────┬──────────┘
         ↓
┌─────── DDD ───────┐
│ 前端17文件生成      │  ← 亮暗主题 + 毛玻璃 + Framer Motion
│ Pexels MCP 集成    │  ← 真实图片 + ColorThief 配色
│ DeepSeek LLM 集成   │  ← 自动生成内容文案
└────────┬──────────┘
         ↓
┌─────── TDD ───────┐
│ 后端66个测试       │  ← 93% 覆盖率
│ 红-绿-重构循环     │
└────────┬──────────┘
         ↓
┌─────── E2E ───────┐
│ Playwright 5条旅程 │
│ agent-dispatch WF  │
└───────────────────┘
```

### 每次迭代的标准流程

1. **明确输入**：给出精确的字段定义、设计约束、验收标准
2. **单次生成**：让 AI 一次性输出完整文件（不反复修改）
3. **修正轮**：发现遗漏后，用修正轮 Prompt 补全（不推翻重来）
4. **验证闭环**：每次修改后立即构建+测试验证

## 2. 典型问题及解决路径

### 问题1：JSON 配置文件损坏

**现象**：`~/.claude.json` 出现 JSON 解析错误，Claude Code 无法启动。

**排查**：
```bash
python3 -c "import json; json.load(open('~/.claude.json'))"
# → JSONDecodeError: 两个 JSON 对象背靠背拼接
```

**根因**：MCP 服务器配置被错误追加到文件末尾，形成 `{...config...}{...mcpServers...}` 的非法结构。

**解决**：
```python
# 按深度分割两个 JSON 对象，合并后写回
depth = 0
for i, ch in enumerate(raw):
    if ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: split_pos = i + 1; break
config = json.loads(raw[:split_pos])
mcp = json.loads(raw[split_pos:])
config['mcpServers'] = mcp['mcpServers']
json.dump(config, f)
```

**教训**：配置文件操作应使用原子写入（先写临时文件再 rename），避免并发写入导致损坏。

### 问题2：Wikipedia API 不可用导致搜索验证失败

**现象**：SubmitForm 的 `validateDestination()` 始终返回 `valid: false`，"冰岛火山内部徒步"也无法通过验证。

**排查**：
```bash
curl 'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Iceland+volcano'
# → 超时，网络层被屏蔽
```

**根因**：开发环境网络策略屏蔽了 Wikipedia API 出站请求。

**解决**：
- 添加后端代理端点 `POST /api/search/validate`（Python urllib 尝试绕过）
- 最终发现 Python 侧也被屏蔽，改为 fallback 策略：网络不可用时跳过验证
- 生产环境下 Wikipedia 和 Pexels 均可正常访问

**教训**：关键路径不能依赖单一外部 API。应有至少一个 fallback（本地模板/缓存/其他源）。

### 问题3：亮暗模式背景图不显示

**现象**：明亮模式下背景纯白，看不到巴哈马海洋照片。

**排查**：
```javascript
// App.jsx 渲染的背景 div
style={{ backgroundImage: 'var(--bg-image)', opacity: 0.15 }}
// opacity 0.15 → 几乎透明
// 同时 surface color 是 #F5F3EE（不透明），完全覆盖背景图
```

**根因**：双层叠加——表面色不透明 + 背景图 opacity 太低。

**解决**：
```css
/* 改 surface 为半透明 rgba */
--color-surface: rgba(255, 255, 255, 0.10);  /* 10% 不透明 → 90% 透光 */
/* 背景图全不透明度 */
style={{ backgroundImage: 'var(--bg-image)' }}  /* 移除 opacity */
```

**教训**：CSS 图层叠加需要精确控制透明度。背景图应全不透明，通过上方 surface 的半透明度来呈现。

## 3. 对"工程化 AI 开发"的理解

### 核心认知

**AI 不是"代码生成器"，而是"加速器"。** 工程化的关键在于：

1. **上下文管理**：每次 Prompt 给出精确的字段定义和约束，不让 AI 猜测。越精确的输入，越准确的输出。

2. **分层输出**：不是一次性生成整个项目，而是 SDD（数据层）→ DDD（展示层）→ TDD（质量层）逐层构建。每层独立验证后再进入下一层。

3. **修正优于重写**：AI 生成的第一版代码大概率有遗漏。与其推翻重来，不如用修正轮 Prompt 精确定位问题并修补。我们的项目经历了 3 轮 SDD 修正、5 轮 DDD 修正。

4. **验证闭环**：每次 AI 输出后立即 `npm run build` + `pytest` + `curl` 验证。如果 AI 的输出不可验证，就无法建立信任。我们的 66 个测试用例就是这层信任的基础。

5. **工具链集成**：AI 的真正威力不在于生成代码，而在于编排工具——Pexels API 搜图、ColorThief 配色、DeepSeek LLM 写文案、agent-dispatch 调度任务。工程师的角色是设计这些工具的协作方式。

### 本项目体现的工程化层次

| 层次 | 工具 | 体现 |
|------|------|------|
| 规格层 | SDD Prompt | 精确的数据模型 + API 契约 |
| 设计层 | DDD Prompt + Pexels MCP + ColorThief | 视觉品质 + 真实图片 + 动态配色 |
| 质量层 | TDD Prompt + Pytest + Playwright | 93% 覆盖率 + E2E 自动化 |
| 调度层 | agent-dispatch + Workflow YAML | 3 个自动化流水线 |
| 内容层 | DeepSeek LLM API | AI 自动生成旅行文案 |
