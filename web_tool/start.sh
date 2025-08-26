#!/bin/bash

# AI Tools Web Interface 启动脚本

echo "=================================================="
echo "AI Tools Web Interface"
echo "=================================================="
echo "绑定IP: 100.102.198.27"
echo "前端端口: 8080"
echo "后端端口: 5000"
echo "=================================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "错误: 未找到Python。请安装Python 3.7+"
    exit 1
fi

# 优先使用python3
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo "使用Python: $PYTHON_CMD"
echo ""

# 启动服务
$PYTHON_CMD start_services.py
