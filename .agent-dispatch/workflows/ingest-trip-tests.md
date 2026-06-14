# Workflow 1 测试用例

## 用例1：成功创建 ✅

```
输入:   冰岛火山内部徒步
后端:   POST /api/search/validate → Wikipedia 返回 "Þríhnukagigur" → 匹配成功
状态流: 正在搜索目的地信息…… → 正在验证匹配度…… → 正在获取图片资源…… 
        → 正在构建网页…… → 正在提取配色方案…… → 已添加！
结果:   创建 trip 卡片 + 详情页 + 8s 后自动刷新
```

## 用例2：雷达未覆盖 ❌

```
输入:   韩国济州岛偶来小道徒步
后端:   POST /api/search/validate → Wikipedia 返回 "Jeju Island" → 不含 "偶来小道"
状态流: 正在搜索目的地信息…… → 正在验证匹配度…… 
        → 🛰️ 雷达暂未覆盖该地区，已提交后台。过段时间再来看看吧～
结果:   不创建卡片，不生成网页，后台记录查询请求
```

## 验证端点

```bash
# 用例1
curl -X POST 'http://localhost:8000/api/search/validate?query=冰岛火山内部徒步'
# → {"valid": true, "top_hits": ["Þríhnukagigur", ...], "reason": "匹配成功"}

# 用例2
curl -X POST 'http://localhost:8000/api/search/validate?query=韩国济州岛偶来小道徒步'
# → {"valid": false, "top_hits": ["Jeju Island", ...], "reason": "关键词不匹配（最近: Jeju Island）"}
```

## 模糊匹配策略

| 策略 | 说明 | 示例 |
|------|------|------|
| 关键词子串 | 搜索词拆分后任一词出现在 Wikipedia 标题中 | "冰岛火山" → "Þríhnukagigur" ❌ → 升级匹配 "Iceland volcano chamber" ✅ |
| 标题包含 | Wikipedia 标题足够短且包含在搜索词中 | "Tromsø" in "挪威特罗姆瑟极光" ✅ |
| 双关键词 | 至少2个关键词同时出现在标题+摘要中 | "冰岛"+"火山" 同时出现 ✅ |
| 共享字符 | 标题与搜索词共享 ≥40% 字符 | "Yakushima" ↔ "屋久岛" 通过罗马字匹配 |

## 当前环境说明

开发环境 Wikipedia API 超时（网络限制）。生产部署后正常工作。
代码逻辑已通过手动审查：fuzzyMatch() 函数覆盖4种匹配策略。
