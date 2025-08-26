# Web工具跨机器部署问题修复总结

## 问题描述

web工具部署到另外一台机器后，其他机器访问时报错："无法连接到后端服务，请确保后端服务正在运行"。

## 根本原因

前端代码中硬编码了`localhost:5000`作为后端地址，导致：
1. 前端API请求指向`http://localhost:5000/api`
2. WebSocket连接指向`http://localhost:5000`
3. 文件下载URL指向`http://localhost:5000/api/download/...`

当部署到其他机器时，其他机器无法通过`localhost`访问到服务器上的后端服务。

## 修复方案

### 1. 创建配置管理系统

**文件**: `frontend/src/config/config.js`

- 支持多种配置方式：URL参数、localStorage、环境配置文件、智能检测
- 自动发现后端服务
- 提供统一的配置接口

### 2. 修改API服务

**文件**: `frontend/src/services/api.js`

- 使用动态配置替换硬编码地址
- 添加`updateBaseUrl()`方法自动更新地址
- 修复文件上传和下载URL

### 3. 修改WebSocket服务

**文件**: `frontend/src/services/websocket.js`

- 支持动态WebSocket连接地址
- 从配置系统获取连接URL

### 4. 修复文件下载

**文件**: `frontend/src/components/resultsManager.js`

- 使用动态配置构建下载URL
- 修复ONNX文件预览链接

### 5. 更新HTML引用

**文件**: `frontend/index.html`

- 添加配置脚本引用
- 确保配置在其他脚本之前加载

## 部署工具

### 1. 生产环境部署脚本

**文件**: `deploy_production.sh`

- 自动检测机器IP地址
- 生成配置文件和启动脚本
- 创建系统服务文件
- 提供防火墙配置说明

### 2. 测试脚本

**文件**: `test_deployment.sh`

- 测试本地和外部连接
- 检查端口占用情况
- 检查防火墙状态
- 提供故障排查信息

### 3. 部署指南

**文件**: `DEPLOYMENT_GUIDE.md`

- 详细的部署步骤
- 常见问题解决方案
- 生产环境优化建议

## 使用方法

### 快速部署

```bash
cd web_tool

# 1. 运行部署脚本
./deploy_production.sh

# 2. 启动服务
./start_production.sh

# 3. 测试部署
./test_deployment.sh
```

### 手动配置

如果需要自定义配置，可以手动编辑 `frontend/config.json`：

```json
{
    "backend": {
        "host": "YOUR_SERVER_IP",
        "port": 5000,
        "protocol": "http"
    }
}
```

## 配置优先级

1. **URL参数** - `?backend_host=IP&backend_port=PORT`
2. **localStorage** - 保存的用户配置
3. **智能检测** - 当前主机非localhost时自动使用当前主机IP
4. **配置文件** - `frontend/config.json`
5. **默认配置** - `localhost:5000`

## 防火墙配置

### Ubuntu/Debian
```bash
sudo ufw allow 5000  # 后端端口
sudo ufw allow 8080  # 前端端口
```

### CentOS/RHEL
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

## 验证部署

从其他机器访问：
- 前端: `http://SERVER_IP:8080`
- 后端健康检查: `http://SERVER_IP:5000/api/health`

## 修改文件列表

✅ **新增文件**:
- `frontend/src/config/config.js` - 配置管理模块
- `deploy_production.sh` - 生产环境部署脚本
- `test_deployment.sh` - 部署测试脚本
- `DEPLOYMENT_GUIDE.md` - 部署指南
- `CROSS_MACHINE_DEPLOYMENT_FIX.md` - 修复总结

✅ **修改文件**:
- `frontend/src/services/api.js` - 支持动态后端地址
- `frontend/src/services/websocket.js` - 支持动态WebSocket连接
- `frontend/src/components/resultsManager.js` - 修复文件下载URL
- `frontend/index.html` - 添加配置脚本引用

✅ **生成文件** (运行部署脚本后):
- `frontend/config.json` - 环境配置文件
- `start_backend_production.sh` - 后端启动脚本
- `start_frontend_production.sh` - 前端启动脚本
- `start_production.sh` - 一键启动脚本
- `ai-tools-web.service` - 系统服务文件
- `FIREWALL_SETUP.md` - 防火墙配置说明

## 技术特性

- ✅ 动态后端地址配置
- ✅ 多种配置方式支持
- ✅ 自动服务发现
- ✅ 跨机器访问支持
- ✅ 智能地址检测
- ✅ 生产环境部署脚本
- ✅ 完整的测试工具
- ✅ 防火墙配置指导
- ✅ 系统服务支持

## 总结

通过以上修改，web工具现在完全支持跨机器部署：

1. **解决了硬编码问题** - 所有localhost地址都已替换为动态配置
2. **提供了灵活的配置方式** - 支持多种配置方式，适应不同部署场景
3. **简化了部署流程** - 一键部署脚本自动完成所有配置
4. **提供了完整的工具链** - 包括测试、故障排查、系统服务等

现在可以安全地将web工具部署到任何机器，其他机器都能正常访问！
