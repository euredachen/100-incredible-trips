#!/bin/bash
# 飞猪「100种不可思议旅行」— 一键启动前后端
# 用法: bash start.sh

echo "🛫 飞猪「100种不可思议旅行」启动中..."

# 确保脚本目录正确（无论从哪里调用都能找到项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# 后端
cd "$PROJECT_DIR/backend" || { echo "❌ 找不到 backend 目录"; exit 1; }
python main.py &
BACKEND_PID=$!

# 前端
cd "$PROJECT_DIR/frontend" || { echo "❌ 找不到 frontend 目录"; exit 1; }
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 后端: http://localhost:8000 (API 文档: http://localhost:8000/docs)"
echo "✅ 前端: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号，同时关闭前后端
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '👋 已停止所有服务'" EXIT

# 等待任一进程退出
wait
