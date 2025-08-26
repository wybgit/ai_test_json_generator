@echo off

echo ==================================================
echo AI Tools Web Interface
echo ==================================================
echo 绑定IP: 100.102.198.27
echo 前端端口: 8080
echo 后端端口: 5000
echo ==================================================
echo.

REM 检查Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python。请安装Python 3.7+
    pause
    exit /b 1
)

echo 使用Python: python
echo.

REM 启动服务
python start_services.py

pause
