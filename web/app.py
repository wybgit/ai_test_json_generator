#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Interface for AI JSON Generator
提供 Web 界面用于远程调用 AI JSON 生成器工具
"""

import os
import sys
import json
import csv
import uuid
import shutil
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from io import StringIO

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from jinja2 import Template, Environment
import zipfile
import tempfile

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ai_json_generator import LLMJsonGenerator, parse_key_value_pairs
from ai_json_generator.cli_display import CLIDisplay

# 导入新的API v2
try:
    from .api_v2 import api_v2
    API_V2_AVAILABLE = True
except ImportError as e:
    print(f"API v2 导入失败: {e}")
    API_V2_AVAILABLE = False
    api_v2 = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-json-generator-web-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DOWNLOAD_FOLDER'] = 'static/downloads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 初始化SocketIO - 专为aitest环境优化
try:
    # 直接使用线程模式，避免eventlet问题
    socketio = SocketIO(app, 
                       cors_allowed_origins="*", 
                       async_mode='threading',
                       logger=False,
                       engineio_logger=False)
    print("✅ SocketIO initialized with threading mode")
except Exception as e:
    print(f"❌ SocketIO initialization failed: {e}")
    # 如果失败，创建基础实例
    socketio = SocketIO(app, cors_allowed_origins="*", logger=False)

# 全局变量存储活动会话
active_sessions = {}
session_locks = {}

class WebCLIDisplay(CLIDisplay):
    """Web版本的CLI显示类，通过WebSocket发送日志"""
    
    def __init__(self, session_id: str):
        super().__init__(quiet=False, debug=True)
        self.session_id = session_id
        
    def log_message(self, message: str, level: str = "info"):
        """发送日志消息到前端"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        socketio.emit('log_message', {
            'timestamp': timestamp,
            'level': level,
            'message': message,
            'session_id': self.session_id
        })
        
    def print_config_info(self, config: Dict[str, Any]):
        """显示配置信息"""
        config_str = f"LLM配置: {config.get('model', 'Unknown')} @ {config.get('api_url', 'Unknown')}"
        self.log_message(config_str, "info")
        
    def print_progress(self, message: str):
        """显示进度信息"""
        self.log_message(f"进度: {message}", "info")
        
    def print_error(self, message: str):
        """显示错误信息"""
        self.log_message(f"错误: {message}", "error")
        
    def print_success(self, message: str):
        """显示成功信息"""
        self.log_message(f"成功: {message}", "success")

def get_session_id():
    """获取或创建会话ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def cleanup_session_files(session_id: str):
    """清理会话相关的文件"""
    session_dir = os.path.join(app.config['DOWNLOAD_FOLDER'], session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
        
def get_session_output_dir(session_id: str) -> str:
    """获取会话输出目录"""
    session_dir = os.path.join(app.config['DOWNLOAD_FOLDER'], session_id)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/templates')
def get_templates():
    """获取可用的模板列表"""
    templates_dir = os.path.join('web_resources', 'templates')
    templates = []
    
    if os.path.exists(templates_dir):
        for file in os.listdir(templates_dir):
            if file.endswith('.txt') or file.endswith('.prompt'):
                file_path = os.path.join(templates_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                templates.append({
                    'name': file,
                    'content': content
                })
    
    return jsonify(templates)

@app.route('/api/csv_files')
def get_csv_files():
    """获取可用的CSV文件列表"""
    try:
        csv_dir = os.path.join('web_resources', 'csv_files')
        csv_files = []
        
        if os.path.exists(csv_dir):
            for file in os.listdir(csv_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join(csv_dir, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if not content:
                                # 空文件
                                csv_files.append({
                                    'name': file,
                                    'headers': [],
                                    'rows': []
                                })
                                continue
                                
                            f.seek(0)  # 重置文件指针
                            reader = csv.DictReader(f)
                            headers = reader.fieldnames or []
                            
                            # 安全地读取所有行
                            rows = []
                            for row_dict in reader:
                                # 清理每一行，确保所有值都是字符串
                                clean_row = {}
                                for key, value in row_dict.items():
                                    if key is None:
                                        continue
                                    if value is None:
                                        clean_row[key] = ''
                                    else:
                                        clean_row[key] = str(value).strip()
                                
                                # 只添加非空行
                                if any(clean_row.values()):
                                    rows.append(clean_row)
                        
                        csv_files.append({
                            'name': file,
                            'headers': [h for h in headers if h is not None],
                            'rows': rows
                        })
                    except Exception as e:
                        print(f"Error reading CSV file {file}: {e}")
                        # 添加错误文件的基本信息
                        csv_files.append({
                            'name': file,
                            'headers': [],
                            'rows': [],
                            'error': str(e)
                        })
        
        return jsonify(csv_files)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/parse_template', methods=['POST'])
def parse_template():
    """解析模板中的Jinja2变量"""
    try:
        data = request.get_json()
        template_content = data.get('template_content', '')
        
        # 使用Jinja2解析模板变量
        env = Environment()
        template = env.from_string(template_content)
        
        # 获取模板中的变量
        variables = []
        try:
            from jinja2 import meta
            ast = env.parse(template_content)
            undeclared_vars = meta.find_undeclared_variables(ast)
            variables = list(undeclared_vars)
        except Exception:
            # 备用方法：简单的正则表达式解析
            import re
            pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
            matches = re.findall(pattern, template_content)
            variables = list(set(matches))
        
        return jsonify({
            'success': True,
            'variables': variables
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/generate', methods=['POST'])
def generate_test_cases():
    """生成测试用例"""
    try:
        data = request.get_json()
        session_id = get_session_id()
        
        # 获取参数
        template_content = data.get('template_content', '')
        variables = data.get('variables', {})
        batch_mode = data.get('batch_mode', False)
        csv_data = data.get('csv_data', [])
        convert_to_onnx = data.get('convert_to_onnx', False)
        max_retries = data.get('max_retries', 3)
        debug = data.get('debug', True)
        temperature = data.get('temperature', 0.6)
        max_tokens = data.get('max_tokens', 8192)
        
        # 验证输入
        if not template_content:
            return jsonify({
                'success': False,
                'error': '模板内容不能为空'
            })
        
        # 创建会话输出目录
        output_dir = get_session_output_dir(session_id)
        
        # 创建Web版本的显示类
        display = WebCLIDisplay(session_id)
        
        # 在后台线程中执行生成任务
        def generate_task():
            try:
                # 初始化生成器
                config_path = os.path.join(project_root, 'config.json')
                generator = LLMJsonGenerator(config_path, display=display)
                
                # 更新生成器的配置参数
                if hasattr(generator, 'config'):
                    generator.config['temperature'] = temperature
                    generator.config['max_tokens'] = max_tokens
                
                if batch_mode and csv_data:
                    # 批量模式
                    display.log_message("开始批量生成测试用例...", "info")
                    
                    # 创建临时模板文件
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.prompt.txt', delete=False, encoding='utf-8') as temp_template:
                        temp_template.write(template_content)
                        template_path = temp_template.name
                    
                    # 创建临时CSV文件
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
                        if csv_data:
                            fieldnames = list(csv_data[0].keys()) if csv_data else []
                            writer = csv.DictWriter(temp_csv, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(csv_data)
                        csv_path = temp_csv.name
                    
                    try:
                        # 使用批量CSV处理功能
                        from ai_json_generator.generate_json import generate_batch_testcases
                        success = generate_batch_testcases(
                            csv_file=csv_path,
                            prompt_file=template_path,
                            output_dir=output_dir,
                            convert_to_onnx=convert_to_onnx,
                            max_retries=max_retries,
                            debug=debug,
                            quiet=False
                        )
                        
                        if success:
                            display.log_message("批量生成完成!", "success")
                            socketio.emit('generation_complete', {
                                'success': True,
                                'session_id': session_id,
                                'output_dir': output_dir
                            })
                        else:
                            display.log_message("批量生成失败", "error")
                            socketio.emit('generation_complete', {
                                'success': False,
                                'session_id': session_id,
                                'error': '批量生成失败'
                            })
                            
                    finally:
                        # 清理临时文件
                        os.unlink(template_path)
                        os.unlink(csv_path)
                        
                else:
                    # 单个变量模式
                    display.log_message("开始生成单个测试用例...", "info")
                    
                    # 渲染模板
                    env = Environment()
                    template = env.from_string(template_content)
                    rendered_content = template.render(variables)
                    
                    # 创建临时模板文件
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.prompt.txt', delete=False, encoding='utf-8') as temp_template:
                        temp_template.write(rendered_content)
                        template_path = temp_template.name
                    
                    try:
                        # 生成单个测试用例
                        success = generator.generate(
                            template_path=template_path,
                            replacements={},  # 已经在模板中渲染了变量
                            output_folder=output_dir,
                            output_filename="test_case",
                            output_ext="json",
                            max_retries=max_retries,
                            debug=debug,
                            direct_prompt_file=template_path
                        )
                        
                        if success:
                            display.log_message("生成完成!", "success")
                            socketio.emit('generation_complete', {
                                'success': True,
                                'session_id': session_id,
                                'output_dir': output_dir
                            })
                        else:
                            display.log_message("生成失败", "error")
                            socketio.emit('generation_complete', {
                                'success': False,
                                'session_id': session_id,
                                'error': '生成失败'
                            })
                            
                    finally:
                        # 清理临时文件
                        os.unlink(template_path)
                        
            except Exception as e:
                display.log_message(f"生成过程中发生错误: {str(e)}", "error")
                socketio.emit('generation_complete', {
                    'success': False,
                    'session_id': session_id,
                    'error': str(e)
                })
        
        # 在后台线程中启动生成任务
        thread = threading.Thread(target=generate_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '生成任务已启动',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/download/<session_id>')
def download_results(session_id):
    """下载生成结果"""
    try:
        session_dir = os.path.join(app.config['DOWNLOAD_FOLDER'], session_id)
        
        if not os.path.exists(session_dir):
            return jsonify({
                'success': False,
                'error': '会话文件不存在'
            })
        
        # 创建ZIP文件
        zip_path = os.path.join(session_dir, 'results.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(session_dir):
                for file in files:
                    if file != 'results.zip':  # 不包含ZIP文件本身
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, session_dir)
                        zipf.write(file_path, arcname)
        
        return send_file(zip_path, as_attachment=True, download_name=f'test_results_{session_id}.zip')
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/results/<session_id>')
def get_results(session_id):
    """获取生成结果列表"""
    try:
        session_dir = os.path.join(app.config['DOWNLOAD_FOLDER'], session_id)
        
        if not os.path.exists(session_dir):
            return jsonify({
                'success': False,
                'error': '会话文件不存在'
            })
        
        results = []
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                if file.endswith('.json') or file.endswith('.onnx') or file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, session_dir)
                    file_size = os.path.getsize(file_path)
                    
                    # 如果是JSON文件，尝试读取内容预览
                    preview = None
                    if file.endswith('.json'):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if len(content) > 500:
                                    preview = content[:500] + "..."
                                else:
                                    preview = content
                        except:
                            preview = "无法预览"
                    
                    results.append({
                        'name': file,
                        'path': rel_path,
                        'size': file_size,
                        'preview': preview
                    })
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/cleanup/<session_id>', methods=['POST'])
def cleanup_session(session_id):
    """清理会话文件"""
    try:
        cleanup_session_files(session_id)
        return jsonify({
            'success': True,
            'message': '会话文件已清理'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@socketio.on('connect')
def handle_connect():
    """WebSocket连接处理"""
    session_id = get_session_id()
    emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket断开连接处理"""
    session_id = get_session_id()
    # 可以选择在断开连接时清理文件，或者保留一段时间
    # cleanup_session_files(session_id)

# 注册新的API v2 Blueprint
if API_V2_AVAILABLE and api_v2:
    app.register_blueprint(api_v2)
    print("✅ API v2 已注册")
else:
    print("⚠️ API v2 不可用，仅使用v1功能")

if __name__ == '__main__':
    # 确保必要的目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
    
    # 启动应用
    try:
        # 尝试使用 eventlet
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Eventlet error: {e}")
        print("Falling back to threading mode...")
        # 回退到线程模式
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, async_mode='threading')
