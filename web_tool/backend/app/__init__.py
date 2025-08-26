from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import sys
import os
# 添加后端目录到Python路径以支持绝对导入
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
from config.config import config

socketio = SocketIO()

def create_app(config_name='default'):
    """应用工厂函数"""
    # 获取frontend目录的绝对路径
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    web_tool_dir = os.path.dirname(backend_dir)
    frontend_dir = os.path.join(web_tool_dir, 'frontend')
    
    app = Flask(__name__, 
                static_folder=frontend_dir,
                static_url_path='')
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    
    # 注册蓝图
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 添加主页路由
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    # 注册WebSocket事件
    from app import socket_events
    
    return app
