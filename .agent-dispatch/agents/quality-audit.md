# Agent: quality-audit

## 描述
定时巡检所有旅行体验的内容质量：图片有效性、外部链接、文案质量、SEO meta。

## 工作目录
/Users/apple/Desktop/ClaudeCode/100-incredible-trips

## 允许的工具
Bash, Read, Write, Edit, WebSearch, WebFetch

## 触发方式
- 定时任务: 每天凌晨 2 点 (cron)
- 手动触发: "巡检内容质量"

## 巡检项目

### 1. 图片有效性
- 检查 cover_image 文件是否存在于 /frontend/public/images/
- 如为外部 URL，检查 HTTP 200
- 失效图片：自动搜索 Pexels 替换

### 2. 外部链接
- 检查 image_source_url 是否可访问
- 检查 external_sources 中的 URL 是否有效
- 失效链接：重新搜索最新来源

### 3. 文案质量
- content 长度 < 100 字符 → 标记"内容过短"
- story 为空 → 标记"缺少故事"
- subtitle 为空 → 标记"缺少副标题"

### 4. SEO meta
- title 是否在 20-60 字符范围内
- subtitle 是否存在且不重复 title
- content 是否包含 h2/h3 标题结构

## 输出
- /data/audit-report.json: 问题列表
- /data/auto-fix-log.json: 自动修复记录
- 控制台输出: 巡检摘要
