#!/bin/bash

# AI Tools Web 一键启动脚本

echo "启动 AI Tools Web 应用..."

# 检查是否在正确的目录
if [ ! -f "backend/run.py" ] || [ ! -f "frontend/index.html" ]; then
    echo "错误: 请在 web_tool 目录下运行此脚本"
    exit 1
fi

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 函数：停止所有服务
cleanup() {
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait
    echo "所有服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 清理可能占用端口的进程
echo "清理可能占用的端口..."
pkill -f "python.*run.py" 2>/dev/null || true
pkill -f "python.*http.server" 2>/dev/null || true
sleep 1

# 启动后端服务
echo "启动后端服务..."
cd backend

# 检查是否存在虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 安装依赖
echo "检查并安装后端依赖..."
pip install -r requirements.txt > /dev/null 2>&1

# 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=True

# 启动后端（后台运行）
python run.py &
BACKEND_PID=$!

# 等待后端启动
echo "等待后端服务启动..."
sleep 3

# 检查后端是否启动成功
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✓ 后端服务启动成功 (PID: $BACKEND_PID)"
else
    echo "✗ 后端服务启动失败"
    exit 1
fi

# 启动前端服务
echo "启动前端服务..."
cd ../frontend

# 启动前端（后台运行）
python3 -m http.server 8080 > /dev/null 2>&1 &
FRONTEND_PID=$!

# 等待前端启动
sleep 2

# 检查前端是否启动成功
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "✓ 前端服务启动成功 (PID: $FRONTEND_PID)"
else
    echo "✗ 前端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 AI Tools Web 应用启动成功！"
echo ""
echo "📊 服务信息:"
echo "  后端服务: http://localhost:5000"
echo "  前端服务: http://localhost:8080"
echo ""
echo "🌐 请访问: http://localhost:8080"
echo ""
echo "⚠️  按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
wait
