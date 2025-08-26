import os
import json
from pathlib import Path

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # 网络配置
    BIND_IP = '100.102.198.27'  # 默认绑定IP
    BIND_PORT = 5000  # 默认绑定端口
    
    # 项目路径配置
    BASE_DIR = Path(__file__).parent.parent.parent
    AI_JSON_GENERATOR_PATH = BASE_DIR.parent  # ai_test_json_generator 项目根目录
    
    # 文件存储配置
    UPLOAD_FOLDER = BASE_DIR / 'shared' / 'uploads'
    OUTPUT_FOLDER = BASE_DIR / 'shared' / 'outputs'
    TEMPLATE_FOLDER = BASE_DIR / 'shared' / 'templates'
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'txt', 'csv', 'json'}
    
    # 文件大小限制 (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # WebSocket 配置
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # 工具配置
    TOOLS_CONFIG = {
        'ai_json_generator': {
            'name': 'AI JSON Generator',
            'description': 'ONNX模型NPU转换工具用例设计助手',
            'executable': 'ai-json-generator',
            'default_args': ['--convert-to-onnx', '--max-retries', '3'],
            'templates_supported': True,
            'csv_supported': True
        }
    }

    @staticmethod
    def load_network_config():
        """从配置文件加载网络配置"""
        config_file = Path(__file__).parent.parent / 'config.json'
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                # 更新网络配置
                if 'network' in config_data:
                    Config.BIND_IP = config_data['network'].get('bind_ip', Config.BIND_IP)
                    Config.BIND_PORT = config_data['network'].get('backend_port', Config.BIND_PORT)
                    
                print(f"网络配置已加载: IP={Config.BIND_IP}, Port={Config.BIND_PORT}")
        except Exception as e:
            print(f"加载网络配置失败，使用默认配置: {e}")

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 加载网络配置
        Config.load_network_config()
        
        # 确保目录存在
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
        Config.TEMPLATE_FOLDER.mkdir(parents=True, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
