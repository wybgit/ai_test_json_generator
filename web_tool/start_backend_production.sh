#!/bin/bash

echo "启动生产环境后端服务..."

cd backend

# 检查是否存在虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 安装依赖
echo "检查并安装依赖..."
pip install -r requirements.txt > /dev/null 2>&1

# 设置生产环境变量
export FLASK_ENV=production
export FLASK_DEBUG=False
export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 启动服务
echo "启动后端服务..."
echo "服务地址: http://0.0.0.0:5000"
echo "按 Ctrl+C 停止服务"
echo "=========================="

python run.py
