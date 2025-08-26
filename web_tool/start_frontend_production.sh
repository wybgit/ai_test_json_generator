#!/bin/bash

echo "启动生产环境前端服务..."

cd frontend

# 启动前端服务
echo "启动前端服务..."
echo "服务地址: http://172.28.51.238:8080"
echo "按 Ctrl+C 停止服务"
echo "=========================="

python3 -m http.server 8080 --bind 172.28.51.238
