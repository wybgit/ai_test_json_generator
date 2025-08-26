#!/usr/bin/env python3
"""
AI Tools Web Services Launcher
启动前后端服务的统一脚本
"""

import json
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def load_config():
    """加载配置文件"""
    config_file = Path(__file__).parent / 'config.json'
    default_config = {
        'network': {
            'bind_ip': '100.102.198.27',
            'backend_port': 5000,
            'frontend_port': 8080
        }
    }
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if 'network' in config_data:
                    default_config['network'].update(config_data['network'])
                return default_config
    except Exception as e:
        print(f"加载配置文件失败，使用默认配置: {e}")
    
    return default_config

def start_backend(config):
    """启动后端服务"""
    backend_dir = Path(__file__).parent / 'backend'
    print(f"启动后端服务 (IP: {config['network']['bind_ip']}, Port: {config['network']['backend_port']})...")
    
    # 切换到后端目录并启动
    cmd = [sys.executable, 'run.py']
    process = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    return process

def start_frontend(config):
    """启动前端服务"""
    frontend_dir = Path(__file__).parent / 'frontend'
    print(f"启动前端服务 (IP: {config['network']['bind_ip']}, Port: {config['network']['frontend_port']})...")
    
    # 切换到前端目录并启动
    cmd = [sys.executable, 'server.py']
    process = subprocess.Popen(
        cmd,
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    return process

def main():
    """主函数"""
    print("=" * 60)
    print("AI Tools Web Services Launcher")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    bind_ip = config['network']['bind_ip']
    backend_port = config['network']['backend_port']
    frontend_port = config['network']['frontend_port']
    
    print(f"配置信息:")
    print(f"  绑定IP: {bind_ip}")
    print(f"  后端端口: {backend_port}")
    print(f"  前端端口: {frontend_port}")
    print(f"  访问地址: http://{bind_ip}:{frontend_port}")
    print()
    
    # 启动服务
    backend_process = None
    frontend_process = None
    
    try:
        # 启动后端
        backend_process = start_backend(config)
        time.sleep(2)  # 等待后端启动
        
        # 检查后端是否启动成功
        if backend_process.poll() is not None:
            print("后端启动失败!")
            return
        
        # 启动前端
        frontend_process = start_frontend(config)
        time.sleep(2)  # 等待前端启动
        
        # 检查前端是否启动成功
        if frontend_process.poll() is not None:
            print("前端启动失败!")
            return
        
        print("\n" + "=" * 60)
        print("服务启动成功!")
        print(f"前端访问地址: http://{bind_ip}:{frontend_port}")
        print(f"后端API地址: http://{bind_ip}:{backend_port}/api")
        print("按 Ctrl+C 停止所有服务")
        print("=" * 60)
        
        # 监控进程输出
        while True:
            # 检查进程是否还在运行
            if backend_process.poll() is not None:
                print("后端服务意外停止")
                break
            if frontend_process.poll() is not None:
                print("前端服务意外停止")
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n正在停止服务...")
        
    except Exception as e:
        print(f"启动服务时出错: {e}")
        
    finally:
        # 清理进程
        if backend_process:
            try:
                backend_process.terminate()
                backend_process.wait(timeout=5)
            except:
                backend_process.kill()
                
        if frontend_process:
            try:
                frontend_process.terminate()
                frontend_process.wait(timeout=5)
            except:
                frontend_process.kill()
                
        print("所有服务已停止")

if __name__ == '__main__':
    main()
