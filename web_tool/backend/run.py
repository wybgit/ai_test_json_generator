#!/usr/bin/env python3
"""
AI Tools Web Interface - Backend Server
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, socketio

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'development')

# 创建应用
app = create_app()

if __name__ == '__main__':
    # 使用SocketIO运行应用
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        allow_unsafe_werkzeug=True  # 开发环境允许
    )
