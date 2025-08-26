#!/usr/bin/env python3
"""
AI Tools Frontend Server
支持配置绑定IP的前端服务器
"""

import json
import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

class ConfigurableHTTPRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        # 设置根目录为当前目录
        super().__init__(*args, directory=Path(__file__).parent, **kwargs)

def load_config():
    """加载配置文件"""
    config_file = Path(__file__).parent / 'config.json'
    default_config = {
        'frontend': {
            'host': '100.102.198.27',
            'port': 8080
        }
    }
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                # 如果有backend配置但没有frontend配置，使用backend的host
                if 'backend' in config_data and 'frontend' not in config_data:
                    default_config['frontend']['host'] = config_data['backend']['host']
                elif 'frontend' in config_data:
                    default_config['frontend'].update(config_data['frontend'])
                return default_config
    except Exception as e:
        print(f"加载配置文件失败，使用默认配置: {e}")
    
    return default_config

def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    # 从配置中获取绑定信息
    bind_ip = config['frontend']['host']
    bind_port = config['frontend']['port']
    
    # 支持命令行参数覆盖
    if len(sys.argv) > 1:
        bind_port = int(sys.argv[1])
    if len(sys.argv) > 2:
        bind_ip = sys.argv[2]
    
    print(f"启动前端服务:")
    print(f"  绑定IP: {bind_ip}")
    print(f"  绑定端口: {bind_port}")
    print(f"  访问地址: http://{bind_ip}:{bind_port}")
    print(f"  根目录: {Path(__file__).parent}")
    
    # 创建服务器
    try:
        server_address = (bind_ip, bind_port)
        httpd = HTTPServer(server_address, ConfigurableHTTPRequestHandler)
        
        print(f"\n服务器启动成功，监听 {bind_ip}:{bind_port}")
        print("按 Ctrl+C 停止服务器")
        
        # 启动服务器
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"错误: 端口 {bind_port} 已被占用")
        elif e.errno == 99:  # Cannot assign requested address
            print(f"错误: 无法绑定到 IP {bind_ip}")
        else:
            print(f"启动服务器时出错: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"启动服务器时出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
