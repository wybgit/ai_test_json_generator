import os
from pathlib import Path

class Config:
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
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
    def init_app(app):
        """初始化应用配置"""
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
