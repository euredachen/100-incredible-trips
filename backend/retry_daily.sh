#!/bin/bash
# 每日 2:00 自动重试失败的 enrich 任务
# crontab: 0 2 * * * /bin/bash /path/to/retry_daily.sh >> /path/to/retry.log 2>&1

API_BASE="http://localhost:8000"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始每日重试..."

RESPONSE=$(curl -s -X POST "$API_BASE/api/tasks/retry")
echo "$RESPONSE"

# 检查是否有人工需处理的永久失败任务
STUCK=$(echo "$RESPONSE" | python3 -c "
import json,sys
try:
    data = json.load(sys.stdin)
    stuck = [r for r in data.get('results', []) if '人工处理' in r]
    if stuck:
        print('⚠️  以下任务需人工处理:')
        for s in stuck:
            print(f'   {s}')
except: pass
" 2>/dev/null)

if [ -n "$STUCK" ]; then
    echo "$STUCK"
    # TODO: 发送通知给客服
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 完成"
