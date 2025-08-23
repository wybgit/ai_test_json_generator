#!/bin/bash

# AI Tools Web Frontend 启动脚本

echo "启动 AI Tools Web Frontend..."

# 检查是否在正确的目录
if [ ! -f "frontend/index.html" ]; then
    echo "错误: 请在 web_tool 目录下运行此脚本"
    exit 1
fi

# 进入前端目录
cd frontend

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 启动简单的HTTP服务器
echo "启动前端服务..."
echo "服务地址: http://localhost:8080"
echo "按 Ctrl+C 停止服务"
echo "=========================="

python3 -m http.server 8080
