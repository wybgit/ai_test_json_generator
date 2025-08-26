#!/bin/bash

# AI Tools Web 生产环境一键启动脚本

echo "启动 AI Tools Web 生产环境..."

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

# 启动后端服务（后台运行）
echo "启动后端服务..."
./start_backend_production.sh &
BACKEND_PID=$!

# 等待后端启动
echo "等待后端服务启动..."
sleep 5

# 检查后端是否启动成功
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✓ 后端服务启动成功 (PID: $BACKEND_PID)"
else
    echo "✗ 后端服务启动失败"
    exit 1
fi

# 启动前端服务（后台运行）
echo "启动前端服务..."
./start_frontend_production.sh &
FRONTEND_PID=$!

# 等待前端启动
sleep 3

# 检查前端是否启动成功
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "✓ 前端服务启动成功 (PID: $FRONTEND_PID)"
else
    echo "✗ 前端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 AI Tools Web 生产环境启动成功！"
echo ""
echo "📊 服务信息:"
echo "  后端服务: http://172.28.51.238:5000"
echo "  前端服务: http://172.28.51.238:8080"
echo ""
echo "🌐 其他机器访问地址: http://172.28.51.238:8080"
echo ""
echo "⚠️  按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
wait
