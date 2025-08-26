#!/usr/bin/env python3
"""
AI Tools Web Interface - Backend Server
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, socketio
from config.config import Config

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'development')

# 创建应用
app = create_app()

if __name__ == '__main__':
    # 加载网络配置
    Config.load_network_config()
    
    print(f"启动后端服务:")
    print(f"  绑定IP: {Config.BIND_IP}")
    print(f"  绑定端口: {Config.BIND_PORT}")
    print(f"  调试模式: {app.config['DEBUG']}")
    
    # 使用SocketIO运行应用
    socketio.run(
        app,
        host=Config.BIND_IP,
        port=Config.BIND_PORT,
        debug=app.config['DEBUG'],
        allow_unsafe_werkzeug=True  # 开发环境允许
    )
