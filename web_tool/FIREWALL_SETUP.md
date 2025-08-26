# 防火墙配置说明

为了让其他机器能够访问Web服务，需要开放相应的端口。

## Ubuntu/Debian 系统 (使用 ufw)

```bash
# 开放前端端口
sudo ufw allow 8080

# 开放后端端口
sudo ufw allow 5000

# 查看防火墙状态
sudo ufw status
```

## CentOS/RHEL 系统 (使用 firewalld)

```bash
# 开放前端端口
sudo firewall-cmd --permanent --add-port=8080/tcp

# 开放后端端口
sudo firewall-cmd --permanent --add-port=5000/tcp

# 重新加载防火墙配置
sudo firewall-cmd --reload

# 查看开放的端口
sudo firewall-cmd --list-ports
```

## 测试连接

从其他机器测试连接：
```bash
# 测试后端连接
curl http://172.28.51.238:5000/api/health

# 在浏览器中访问前端
http://172.28.51.238:8080
```
