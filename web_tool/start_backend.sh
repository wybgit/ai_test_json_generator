#!/bin/bash

# AI Tools Web Backend 启动脚本

echo "启动 AI Tools Web Backend..."

# 检查是否在正确的目录
if [ ! -f "backend/run.py" ]; then
    echo "错误: 请在 web_tool 目录下运行此脚本"
    exit 1
fi

# 进入后端目录
cd backend

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查是否存在虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 安装依赖
echo "检查并安装依赖..."
pip install -r requirements.txt

# 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=True

# 启动服务
echo "启动后端服务..."
echo "服务地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo "=========================="

python run.py
