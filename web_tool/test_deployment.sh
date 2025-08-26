#!/bin/bash

# AI Tools Web 部署测试脚本

echo "======================================"
echo "AI Tools Web 部署测试"
echo "======================================"

# 获取当前机器的IP地址
CURRENT_IP=$(hostname -I | awk '{print $1}')
if [ -z "$CURRENT_IP" ]; then
    CURRENT_IP=$(ip route get 8.8.8.8 | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}')
fi

BACKEND_PORT=5000
FRONTEND_PORT=8080

echo "测试配置:"
echo "  机器IP地址: $CURRENT_IP"
echo "  后端端口: $BACKEND_PORT"
echo "  前端端口: $FRONTEND_PORT"
echo "======================================"

# 测试后端健康检查
echo "测试后端健康检查..."
if curl -s "http://localhost:$BACKEND_PORT/api/health" > /dev/null; then
    echo "✓ 本地后端连接正常"
    
    # 测试外部访问
    if curl -s "http://$CURRENT_IP:$BACKEND_PORT/api/health" > /dev/null; then
        echo "✓ 外部后端连接正常"
    else
        echo "✗ 外部后端连接失败"
        echo "  可能原因: 防火墙阻止了端口 $BACKEND_PORT"
    fi
else
    echo "✗ 本地后端连接失败"
    echo "  请确保后端服务正在运行"
fi

# 测试前端服务
echo ""
echo "测试前端服务..."
if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
    echo "✓ 本地前端连接正常"
    
    # 测试外部访问
    if curl -s "http://$CURRENT_IP:$FRONTEND_PORT" > /dev/null; then
        echo "✓ 外部前端连接正常"
    else
        echo "✗ 外部前端连接失败"
        echo "  可能原因: 防火墙阻止了端口 $FRONTEND_PORT"
    fi
else
    echo "✗ 本地前端连接失败"
    echo "  请确保前端服务正在运行"
fi

# 检查端口占用情况
echo ""
echo "端口占用情况:"
echo "后端端口 $BACKEND_PORT:"
netstat -tlnp 2>/dev/null | grep ":$BACKEND_PORT " || echo "  端口未被占用"

echo "前端端口 $FRONTEND_PORT:"
netstat -tlnp 2>/dev/null | grep ":$FRONTEND_PORT " || echo "  端口未被占用"

# 检查防火墙状态
echo ""
echo "防火墙状态检查:"
if command -v ufw &> /dev/null; then
    echo "UFW 防火墙状态:"
    sudo ufw status 2>/dev/null || echo "  无法检查 UFW 状态"
elif command -v firewall-cmd &> /dev/null; then
    echo "Firewalld 防火墙状态:"
    sudo firewall-cmd --list-ports 2>/dev/null || echo "  无法检查 Firewalld 状态"
else
    echo "  未检测到常见的防火墙工具"
fi

echo ""
echo "======================================"
echo "测试完成"
echo "======================================"
echo ""
echo "如果外部连接失败，请执行以下操作："
echo "1. 检查防火墙设置 (参考 FIREWALL_SETUP.md)"
echo "2. 确保服务绑定到 0.0.0.0 而不是 127.0.0.1"
echo "3. 检查网络配置和路由"
echo ""
echo "外部访问地址:"
echo "  前端: http://$CURRENT_IP:$FRONTEND_PORT"
echo "  后端API: http://$CURRENT_IP:$BACKEND_PORT/api/health"
echo ""
