# Web工具跨机器部署指南

## 问题描述

当web工具部署到另外一台机器后，其他机器访问时出现"无法连接到后端服务"的错误。这是因为前端代码中硬编码了`localhost`地址，导致跨机器访问失败。

## 解决方案

### 1. 问题原因

原始代码中存在以下硬编码地址：
- 前端API服务: `http://localhost:5000/api`
- WebSocket连接: `http://localhost:5000`
- 文件下载URL: `http://localhost:5000/api/download/...`

### 2. 修复内容

已修复的文件：
- `frontend/src/config/config.js` - 新增配置管理模块
- `frontend/src/services/api.js` - 支持动态后端地址
- `frontend/src/services/websocket.js` - 支持动态WebSocket连接
- `frontend/src/components/resultsManager.js` - 修复文件下载URL
- `frontend/index.html` - 添加配置脚本引用

### 3. 部署步骤

#### 快速部署（推荐）

```bash
cd web_tool

# 1. 运行部署脚本（自动配置）
./deploy_production.sh

# 2. 启动服务
./start_production.sh
```

#### 手动部署

```bash
cd web_tool

# 1. 创建前端配置文件
cat > frontend/config.json << EOF
{
    "backend": {
        "host": "YOUR_SERVER_IP",
        "port": 5000,
        "protocol": "http"
    }
}
EOF

# 2. 启动后端（绑定到所有网络接口）
cd backend
python run.py  # 已配置为 host='0.0.0.0'

# 3. 启动前端（绑定到所有网络接口）
cd ../frontend
python3 -m http.server 8080 --bind 0.0.0.0
```

### 4. 配置说明

#### 环境配置文件

在 `frontend/config.json` 中配置后端地址：

```json
{
    "backend": {
        "host": "192.168.1.100",  // 服务器IP地址
        "port": 5000,             // 后端端口
        "protocol": "http"        // 协议
    }
}
```

#### URL参数配置

也可以通过URL参数动态指定后端地址：

```
http://192.168.1.100:8080/?backend_host=192.168.1.100&backend_port=5000
```

#### 自动发现

配置系统会自动尝试：
1. URL参数配置
2. localStorage保存的配置
3. 智能检测（如果前端不在localhost运行，使用当前主机作为后端）
4. 环境配置文件

### 5. 防火墙配置

#### Ubuntu/Debian (ufw)

```bash
# 开放端口
sudo ufw allow 5000  # 后端端口
sudo ufw allow 8080  # 前端端口

# 查看状态
sudo ufw status
```

#### CentOS/RHEL (firewalld)

```bash
# 开放端口
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload

# 查看开放的端口
sudo firewall-cmd --list-ports
```

### 6. 测试部署

```bash
# 运行测试脚本
./test_deployment.sh

# 手动测试
curl http://YOUR_SERVER_IP:5000/api/health
```

### 7. 常见问题

#### 问题1: "网络连接失败，请检查服务器是否运行"

**原因**: 前端无法连接到后端API

**解决方案**:
1. 检查后端服务是否启动: `curl http://localhost:5000/api/health`
2. 检查防火墙是否开放端口 5000
3. 确认配置文件中的IP地址正确

#### 问题2: WebSocket连接失败

**原因**: WebSocket无法连接到后端

**解决方案**:
1. 检查WebSocket端口（通常与后端API同端口）
2. 确认防火墙允许WebSocket连接
3. 检查代理服务器配置（如使用Nginx）

#### 问题3: 文件下载失败

**原因**: 文件下载URL指向错误的地址

**解决方案**:
1. 检查配置文件是否正确加载
2. 确认后端文件服务正常
3. 检查文件路径和权限

### 8. 生产环境优化

#### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/web_tool/frontend;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket代理
    location /socket.io/ {
        proxy_pass http://localhost:5000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

#### 使用系统服务

```bash
# 复制服务文件
sudo cp ai-tools-web.service /etc/systemd/system/

# 启用并启动服务
sudo systemctl enable ai-tools-web
sudo systemctl start ai-tools-web

# 查看状态
sudo systemctl status ai-tools-web
```

### 9. 故障排查

#### 检查服务状态

```bash
# 检查端口占用
netstat -tlnp | grep :5000
netstat -tlnp | grep :8080

# 检查进程
ps aux | grep python | grep run.py
ps aux | grep python | grep http.server

# 检查日志
journalctl -u ai-tools-web -f
```

#### 网络连通性测试

```bash
# 从其他机器测试
curl -v http://SERVER_IP:5000/api/health
telnet SERVER_IP 5000
```

### 10. 安全注意事项

1. **生产环境**：使用HTTPS和WSS协议
2. **访问控制**：配置防火墙限制访问来源
3. **认证**：添加用户认证机制
4. **密钥管理**：使用环境变量管理敏感信息

## 总结

通过以上修改和配置，web工具现在支持：

1. ✅ 动态后端地址配置
2. ✅ 跨机器部署
3. ✅ 自动服务发现
4. ✅ 灵活的配置方式
5. ✅ 生产环境部署脚本
6. ✅ 完整的测试工具

使用 `./deploy_production.sh` 可以一键完成生产环境部署配置。
