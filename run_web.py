#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - AI JSON Generator Web Interface
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """启动Web应用"""
    # 确保在项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 AI JSON Generator Web Interface")
    print("=" * 50)
    print(f"项目目录: {project_root}")
    print(f"Web目录: {project_root / 'web'}")
    
    # 检查配置文件
    config_file = project_root / "config.json"
    if not config_file.exists():
        print("❌ 错误: 找不到 config.json 文件")
        print("请确保在项目根目录下有正确的配置文件")
        return 1
    
    # 检查web目录
    web_dir = project_root / "web"
    if not web_dir.exists():
        print("❌ 错误: 找不到 web 目录")
        return 1
    
    # 检查web资源
    web_resources = web_dir / "web_resources"
    if not web_resources.exists():
        print("❌ 错误: 找不到 web_resources 目录")
        return 1
    
    templates_dir = web_resources / "templates"
    csv_dir = web_resources / "csv_files"
    
    template_count = len(list(templates_dir.glob("*.txt"))) if templates_dir.exists() else 0
    csv_count = len(list(csv_dir.glob("*.csv"))) if csv_dir.exists() else 0
    
    print(f"📄 模板文件: {template_count} 个")
    print(f"📊 CSV文件: {csv_count} 个")
    
    # 更改到web目录
    os.chdir(web_dir)
    
    print("\n🌐 启动Web服务器...")
    print("访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    try:
        # 启动Flask应用
        import sys
        sys.path.insert(0, str(project_root))
        
        # 导入Web应用
        from web.app import app, socketio
        
        print("🔧 启动模式: WebSocket + HTTP (线程模式)")
        print("🌐 专为aitest环境优化")
        
        # 启动应用，使用线程模式避免SSL问题
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Web服务器已停止")
        return 0
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所需依赖:")
        print("cd web && pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
