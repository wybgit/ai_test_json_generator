# AI Tools Web Interface 部署说明

## 网络配置

本系统支持配置绑定IP，默认绑定IP为 `100.102.198.27`。

### 配置文件

主配置文件位于 `web_tool/config.json`：

```json
{
    "network": {
        "bind_ip": "100.102.198.27",
        "backend_port": 5000,
        "frontend_port": 8080
    },
    "backend": {
        "host": "100.102.198.27",
        "port": 5000,
        "protocol": "http"
    },
    "frontend": {
        "host": "100.102.198.27",
        "port": 8080,
        "protocol": "http"
    }
}
```

### 修改绑定IP

1. **修改主配置文件**：
   编辑 `web_tool/config.json`，将 `bind_ip` 改为你需要的IP地址。

2. **前端配置**：
   前端配置文件 `web_tool/frontend/config.json` 会自动使用主配置的IP。

3. **后端配置**：
   后端会自动从主配置文件加载IP设置。

## 启动方式

### 方式一：统一启动脚本（推荐）

```bash
cd web_tool
python start_services.py
```

这会同时启动前后端服务，并显示访问地址。

### 方式二：分别启动

**启动后端**：
```bash
cd web_tool/backend
python run.py
```

**启动前端**：
```bash
cd web_tool/frontend
python server.py
```

或使用npm脚本：
```bash
cd web_tool/frontend
npm run start
```

### 方式三：指定端口启动

**前端指定端口**：
```bash
cd web_tool/frontend
python server.py 8080 100.102.198.27
```

## 访问地址

- **前端界面**: `http://100.102.198.27:8080`
- **后端API**: `http://100.102.198.27:5000/api`

## 网络要求

- 确保指定的IP地址在当前机器上可用
- 确保防火墙允许相应端口的访问
- 如果需要外部访问，确保网络路由配置正确

## 故障排除

1. **端口被占用**：
   ```bash
   # 查看端口使用情况
   netstat -tlnp | grep :5000
   netstat -tlnp | grep :8080
   ```

2. **IP绑定失败**：
   - 检查IP地址是否在当前机器上存在
   - 确认没有权限问题

3. **服务无法启动**：
   - 检查Python环境和依赖
   - 查看详细错误日志

## 配置说明

### 后端配置 (backend/config/config.py)

- `BIND_IP`: 后端绑定的IP地址
- `BIND_PORT`: 后端绑定的端口

### 前端配置 (frontend/src/config/config.js)

- 前端JavaScript配置会自动从配置文件读取后端地址
- 支持动态配置和自动发现后端服务

### 主配置优先级

1. 主配置文件 `config.json`
2. 环境变量
3. 默认值 (100.102.198.27)
