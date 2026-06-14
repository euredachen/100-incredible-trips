# Agent: trip-ingest

## 描述
自动入库新旅行体验。输入景点名称，并行搜索 Wikipedia/National Geographic/Pexels/中文攻略，
串行生成 Markdown 内容 + 故事文案 + 配色方案，写入数据库。

## 工作目录
/Users/apple/Desktop/ClaudeCode/100-incredible-trips

## 允许的工具
Bash, Read, Write, Edit, WebSearch, WebFetch

## 触发方式
- 用户输入 "加一条 [景点] 的体验"
- agent-dispatch test trip-ingest "冰岛火山内部徒步"

## 工作流程

### Phase 1: 并行搜索 (parallel)
同时执行 4 个搜索任务：

1. **Wikipedia 搜索**: `curl -s 'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&origin=*'`
2. **Pexels 图片搜索**: `curl -s -H 'Authorization: {PEXELS_KEY}' 'https://api.pexels.com/v1/search?query={query}&orientation=landscape&per_page=5'`
3. **中文攻略搜索**: 使用 WebSearch 搜索 "{景点} 旅行攻略 体验"
4. **NatGeo 搜索**: 返回 `https://www.nationalgeographic.com/search?q={query}`

### Phase 2: 串行加工 (pipeline)
1. LLM 生成 content(Markdown) + story(情感故事)
2. ColorThief 提取主色: `python3 -c "from colorthief import ColorThief; ..."`
3. 下载图片到 `/frontend/public/images/`
4. 事实校验: 交叉验证 Wikipedia 摘要 vs 中文攻略

### Phase 3: 入库
调用 `POST /api/trips` 创建记录，关联外部来源 URL

## 依赖
- Pexels API Key: 已配置在 ~/.claude.json
- ColorThief: `pip install colorthief` (已安装)
- 后端 API: http://localhost:8000
