#!/bin/bash

# AI Tools Web 生产环境部署脚本

echo "======================================"
echo "AI Tools Web 生产环境部署"
echo "======================================"

# 默认配置
DEFAULT_BACKEND_HOST="0.0.0.0"
DEFAULT_BACKEND_PORT="5000"
DEFAULT_FRONTEND_PORT="8080"

# 获取参数
BACKEND_HOST=${1:-$DEFAULT_BACKEND_HOST}
BACKEND_PORT=${2:-$DEFAULT_BACKEND_PORT}
FRONTEND_PORT=${3:-$DEFAULT_FRONTEND_PORT}

# 获取当前机器的IP地址
CURRENT_IP=$(hostname -I | awk '{print $1}')
if [ -z "$CURRENT_IP" ]; then
    CURRENT_IP=$(ip route get 8.8.8.8 | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}')
fi

echo "部署配置:"
echo "  后端监听地址: $BACKEND_HOST:$BACKEND_PORT"
echo "  前端端口: $FRONTEND_PORT"
echo "  机器IP地址: $CURRENT_IP"
echo "======================================"

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

# 创建生产环境配置文件
echo "创建生产环境配置文件..."
cat > frontend/config.json << EOF
{
    "backend": {
        "host": "$CURRENT_IP",
        "port": $BACKEND_PORT,
        "protocol": "http"
    },
    "frontend": {
        "host": "$CURRENT_IP",
        "port": $FRONTEND_PORT,
        "protocol": "http"
    }
}
EOF

echo "✓ 配置文件创建完成: frontend/config.json"

# 创建后端启动脚本
echo "创建后端启动脚本..."
cat > start_backend_production.sh << 'EOF'
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
echo "服务地址: http://$BACKEND_HOST:$BACKEND_PORT"
echo "按 Ctrl+C 停止服务"
echo "=========================="

python run.py
EOF

# 替换变量
sed -i "s/\$BACKEND_HOST/$BACKEND_HOST/g" start_backend_production.sh
sed -i "s/\$BACKEND_PORT/$BACKEND_PORT/g" start_backend_production.sh

chmod +x start_backend_production.sh
echo "✓ 后端启动脚本创建完成: start_backend_production.sh"

# 创建前端启动脚本
echo "创建前端启动脚本..."
cat > start_frontend_production.sh << EOF
#!/bin/bash

echo "启动生产环境前端服务..."

cd frontend

# 启动前端服务
echo "启动前端服务..."
echo "服务地址: http://$CURRENT_IP:$FRONTEND_PORT"
echo "按 Ctrl+C 停止服务"
echo "=========================="

python3 -m http.server $FRONTEND_PORT --bind $CURRENT_IP
EOF

chmod +x start_frontend_production.sh
echo "✓ 前端启动脚本创建完成: start_frontend_production.sh"

# 创建一键部署脚本
echo "创建一键部署脚本..."
cat > start_production.sh << EOF
#!/bin/bash

# AI Tools Web 生产环境一键启动脚本

echo "启动 AI Tools Web 生产环境..."

# 函数：停止所有服务
cleanup() {
    echo "正在停止服务..."
    kill \$BACKEND_PID 2>/dev/null
    kill \$FRONTEND_PID 2>/dev/null
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
BACKEND_PID=\$!

# 等待后端启动
echo "等待后端服务启动..."
sleep 5

# 检查后端是否启动成功
if kill -0 \$BACKEND_PID 2>/dev/null; then
    echo "✓ 后端服务启动成功 (PID: \$BACKEND_PID)"
else
    echo "✗ 后端服务启动失败"
    exit 1
fi

# 启动前端服务（后台运行）
echo "启动前端服务..."
./start_frontend_production.sh &
FRONTEND_PID=\$!

# 等待前端启动
sleep 3

# 检查前端是否启动成功
if kill -0 \$FRONTEND_PID 2>/dev/null; then
    echo "✓ 前端服务启动成功 (PID: \$FRONTEND_PID)"
else
    echo "✗ 前端服务启动失败"
    kill \$BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 AI Tools Web 生产环境启动成功！"
echo ""
echo "📊 服务信息:"
echo "  后端服务: http://$CURRENT_IP:$BACKEND_PORT"
echo "  前端服务: http://$CURRENT_IP:$FRONTEND_PORT"
echo ""
echo "🌐 其他机器访问地址: http://$CURRENT_IP:$FRONTEND_PORT"
echo ""
echo "⚠️  按 Ctrl+C 停止所有服务"
echo ""

# 等待用户中断
wait
EOF

chmod +x start_production.sh
echo "✓ 一键部署脚本创建完成: start_production.sh"

# 创建系统服务文件（可选）
echo "创建系统服务文件..."
cat > ai-tools-web.service << EOF
[Unit]
Description=AI Tools Web Backend
After=network.target

[Service]
Type=simple
User=\$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/start_backend_production.sh
Restart=always
RestartSec=5
Environment=FLASK_ENV=production
Environment=FLASK_DEBUG=False

[Install]
WantedBy=multi-user.target
EOF

echo "✓ 系统服务文件创建完成: ai-tools-web.service"

# 创建防火墙配置提示
echo "创建防火墙配置说明..."
cat > FIREWALL_SETUP.md << EOF
# 防火墙配置说明

为了让其他机器能够访问Web服务，需要开放相应的端口。

## Ubuntu/Debian 系统 (使用 ufw)

\`\`\`bash
# 开放前端端口
sudo ufw allow $FRONTEND_PORT

# 开放后端端口
sudo ufw allow $BACKEND_PORT

# 查看防火墙状态
sudo ufw status
\`\`\`

## CentOS/RHEL 系统 (使用 firewalld)

\`\`\`bash
# 开放前端端口
sudo firewall-cmd --permanent --add-port=$FRONTEND_PORT/tcp

# 开放后端端口
sudo firewall-cmd --permanent --add-port=$BACKEND_PORT/tcp

# 重新加载防火墙配置
sudo firewall-cmd --reload

# 查看开放的端口
sudo firewall-cmd --list-ports
\`\`\`

## 测试连接

从其他机器测试连接：
\`\`\`bash
# 测试后端连接
curl http://$CURRENT_IP:$BACKEND_PORT/api/health

# 在浏览器中访问前端
http://$CURRENT_IP:$FRONTEND_PORT
\`\`\`
EOF

echo "✓ 防火墙配置说明创建完成: FIREWALL_SETUP.md"

echo ""
echo "======================================"
echo "部署完成！"
echo "======================================"
echo ""
echo "下一步操作："
echo "1. 配置防火墙 (参考 FIREWALL_SETUP.md)"
echo "2. 运行部署脚本: ./start_production.sh"
echo "3. 从其他机器访问: http://$CURRENT_IP:$FRONTEND_PORT"
echo ""
echo "可选操作："
echo "- 安装系统服务: sudo cp ai-tools-web.service /etc/systemd/system/"
echo "- 启用系统服务: sudo systemctl enable ai-tools-web"
echo "- 启动系统服务: sudo systemctl start ai-tools-web"
echo ""
