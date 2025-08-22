#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v2 for AI JSON Generator
直接调用核心功能，与CLI命令行保持一致
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, session, send_file
import zipfile
import threading
import uuid

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from ai_json_generator.generate_json import (
    LLMJsonGenerator, 
    generate_testcase,
    generate_batch_testcases,
    setup_display
)
from ai_json_generator.cli_display import CLIDisplay

# 创建API Blueprint
api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

# 全局变量存储活动任务
active_tasks = {}
task_locks = {}


class WebAPIDisplay(CLIDisplay):
    """Web API版本的显示类，收集日志而不是直接显示"""
    
    def __init__(self, task_id: str):
        super().__init__(quiet=False, debug=True)
        self.task_id = task_id
        self.logs = []
        self.status = "running"
        
    def log_message(self, message: str, level: str = "info"):
        """收集日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        
        # 更新任务状态
        if self.task_id in active_tasks:
            active_tasks[self.task_id]['logs'] = self.logs
            active_tasks[self.task_id]['last_update'] = datetime.now()
        
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


def get_task_id():
    """获取或创建任务ID"""
    if 'task_id' not in session:
        session['task_id'] = str(uuid.uuid4())
    return session['task_id']


def create_task(task_type: str, parameters: Dict) -> str:
    """创建新任务"""
    task_id = str(uuid.uuid4())
    session['task_id'] = task_id
    
    active_tasks[task_id] = {
        'id': task_id,
        'type': task_type,
        'status': 'created',
        'parameters': parameters,
        'logs': [],
        'result': None,
        'error': None,
        'created_at': datetime.now(),
        'last_update': datetime.now(),
        'output_dir': None
    }
    
    task_locks[task_id] = threading.Lock()
    return task_id


@api_v2.route('/generate/single', methods=['POST'])
def generate_single_testcase():
    """
    生成单个测试用例
    对应CLI命令: ai-json-generator <operator> [options]
    """
    try:
        data = request.get_json()
        
        # 解析参数
        operator = data.get('operator', '')
        output_dir = data.get('output_dir', 'outputs')
        test_point = data.get('test_point')
        graph_pattern = data.get('graph_pattern')
        add_req = data.get('add_req')
        direct_prompt = data.get('direct_prompt')
        direct_request = data.get('direct_request')
        convert_to_onnx = data.get('convert_to_onnx', False)
        max_retries = data.get('max_retries', 1)
        debug = data.get('debug', True)
        quiet = data.get('quiet', False)
        
        # 验证参数
        if not operator and not direct_prompt and not direct_request:
            return jsonify({
                'success': False,
                'error': '必须指定operator、direct_prompt或direct_request之一'
            }), 400
        
        # 创建任务
        task_id = create_task('single_generation', {
            'operator': operator,
            'output_dir': output_dir,
            'test_point': test_point,
            'graph_pattern': graph_pattern,
            'add_req': add_req,
            'direct_prompt': direct_prompt,
            'direct_request': direct_request,
            'convert_to_onnx': convert_to_onnx,
            'max_retries': max_retries,
            'debug': debug,
            'quiet': quiet
        })
        
        # 创建输出目录
        session_output_dir = os.path.join(output_dir, f"session_{task_id}")
        os.makedirs(session_output_dir, exist_ok=True)
        active_tasks[task_id]['output_dir'] = session_output_dir
        
        # 在后台线程中执行生成任务
        def generate_task():
            try:
                active_tasks[task_id]['status'] = 'running'
                
                # 处理直接提示文件
                temp_prompt_file = None
                if direct_prompt and not os.path.exists(direct_prompt):
                    # 如果direct_prompt是内容而不是文件路径，创建临时文件
                    temp_prompt_file = os.path.join(session_output_dir, 'temp_prompt.txt')
                    with open(temp_prompt_file, 'w', encoding='utf-8') as f:
                        f.write(direct_prompt)
                    direct_prompt_path = temp_prompt_file
                else:
                    direct_prompt_path = direct_prompt
                
                # 处理直接请求文件
                temp_request_file = None
                if direct_request and not os.path.exists(direct_request):
                    # 如果direct_request是内容而不是文件路径，创建临时文件
                    temp_request_file = os.path.join(session_output_dir, 'temp_request.txt')
                    with open(temp_request_file, 'w', encoding='utf-8') as f:
                        f.write(direct_request)
                    direct_request_path = temp_request_file
                else:
                    direct_request_path = direct_request
                
                # 调用核心生成函数
                success = generate_testcase(
                    operator_string=operator,
                    output_dir=session_output_dir,
                    quiet=quiet,
                    test_point=test_point,
                    graph_pattern=graph_pattern,
                    add_req=add_req,
                    direct_prompt=direct_prompt_path,
                    direct_request=direct_request_path,
                    convert_to_onnx=convert_to_onnx,
                    max_retries=max_retries,
                    debug=debug
                )
                
                # 清理临时文件
                if temp_prompt_file and os.path.exists(temp_prompt_file):
                    os.unlink(temp_prompt_file)
                if temp_request_file and os.path.exists(temp_request_file):
                    os.unlink(temp_request_file)
                
                # 更新任务状态
                active_tasks[task_id]['status'] = 'completed' if success else 'failed'
                active_tasks[task_id]['result'] = {
                    'success': success,
                    'output_dir': session_output_dir,
                    'files': list_output_files(session_output_dir)
                }
                
            except Exception as e:
                active_tasks[task_id]['status'] = 'error'
                active_tasks[task_id]['error'] = str(e)
        
        # 启动后台任务
        thread = threading.Thread(target=generate_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '生成任务已启动',
            'status_url': f'/api/v2/tasks/{task_id}/status'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_v2.route('/generate/batch', methods=['POST'])
def generate_batch_testcases_api():
    """
    批量生成测试用例
    对应CLI命令: ai-json-generator --batch-csv <csv_file> --direct-prompt <prompt_file> [options]
    """
    try:
        data = request.get_json()
        
        # 解析参数
        csv_data = data.get('csv_data', [])
        prompt_template = data.get('prompt_template', '')
        output_dir = data.get('output_dir', 'outputs')
        convert_to_onnx = data.get('convert_to_onnx', False)
        max_retries = data.get('max_retries', 1)
        debug = data.get('debug', True)
        quiet = data.get('quiet', False)
        
        # 验证参数
        if not csv_data:
            return jsonify({
                'success': False,
                'error': 'csv_data不能为空'
            }), 400
        
        if not prompt_template:
            return jsonify({
                'success': False,
                'error': 'prompt_template不能为空'
            }), 400
        
        # 创建任务
        task_id = create_task('batch_generation', {
            'csv_data': csv_data,
            'prompt_template': prompt_template,
            'output_dir': output_dir,
            'convert_to_onnx': convert_to_onnx,
            'max_retries': max_retries,
            'debug': debug,
            'quiet': quiet
        })
        
        # 创建输出目录
        session_output_dir = os.path.join(output_dir, f"batch_{task_id}")
        os.makedirs(session_output_dir, exist_ok=True)
        active_tasks[task_id]['output_dir'] = session_output_dir
        
        # 在后台线程中执行批量生成任务
        def batch_generate_task():
            try:
                active_tasks[task_id]['status'] = 'running'
                
                # 创建临时CSV文件
                temp_csv_file = os.path.join(session_output_dir, 'temp_data.csv')
                if csv_data:
                    import csv
                    fieldnames = list(csv_data[0].keys()) if csv_data else []
                    with open(temp_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(csv_data)
                
                # 创建临时提示文件
                temp_prompt_file = os.path.join(session_output_dir, 'temp_prompt.txt')
                with open(temp_prompt_file, 'w', encoding='utf-8') as f:
                    f.write(prompt_template)
                
                # 调用核心批量生成函数
                success = generate_batch_testcases(
                    csv_file=temp_csv_file,
                    prompt_file=temp_prompt_file,
                    output_dir=session_output_dir,
                    convert_to_onnx=convert_to_onnx,
                    max_retries=max_retries,
                    debug=debug,
                    quiet=quiet
                )
                
                # 清理临时文件
                if os.path.exists(temp_csv_file):
                    os.unlink(temp_csv_file)
                if os.path.exists(temp_prompt_file):
                    os.unlink(temp_prompt_file)
                
                # 更新任务状态
                active_tasks[task_id]['status'] = 'completed' if success else 'failed'
                active_tasks[task_id]['result'] = {
                    'success': success,
                    'output_dir': session_output_dir,
                    'files': list_output_files(session_output_dir)
                }
                
            except Exception as e:
                active_tasks[task_id]['status'] = 'error'
                active_tasks[task_id]['error'] = str(e)
        
        # 启动后台任务
        thread = threading.Thread(target=batch_generate_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '批量生成任务已启动',
            'status_url': f'/api/v2/tasks/{task_id}/status'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_v2.route('/tasks/<task_id>/status', methods=['GET'])
def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in active_tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    task = active_tasks[task_id]
    
    return jsonify({
        'success': True,
        'task': {
            'id': task['id'],
            'type': task['type'],
            'status': task['status'],
            'logs': task['logs'][-50:],  # 只返回最近50条日志
            'result': task.get('result'),
            'error': task.get('error'),
            'created_at': task['created_at'].isoformat(),
            'last_update': task['last_update'].isoformat()
        }
    })


@api_v2.route('/tasks/<task_id>/logs', methods=['GET'])
def get_task_logs(task_id: str):
    """获取任务的完整日志"""
    if task_id not in active_tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    task = active_tasks[task_id]
    
    return jsonify({
        'success': True,
        'logs': task['logs']
    })


@api_v2.route('/tasks/<task_id>/files', methods=['GET'])
def get_task_files(task_id: str):
    """获取任务生成的文件列表"""
    if task_id not in active_tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    task = active_tasks[task_id]
    output_dir = task.get('output_dir')
    
    if not output_dir or not os.path.exists(output_dir):
        return jsonify({
            'success': False,
            'error': '输出目录不存在'
        }), 404
    
    files = list_output_files(output_dir)
    
    return jsonify({
        'success': True,
        'files': files
    })


@api_v2.route('/tasks/<task_id>/download', methods=['GET'])
def download_task_files(task_id: str):
    """下载任务生成的所有文件（ZIP格式）"""
    if task_id not in active_tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    task = active_tasks[task_id]
    output_dir = task.get('output_dir')
    
    if not output_dir or not os.path.exists(output_dir):
        return jsonify({
            'success': False,
            'error': '输出目录不存在'
        }), 404
    
    # 创建ZIP文件
    zip_path = os.path.join(output_dir, f'results_{task_id}.zip')
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file != f'results_{task_id}.zip':  # 不包含ZIP文件本身
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)
    
    return send_file(
        zip_path, 
        as_attachment=True, 
        download_name=f'ai_json_results_{task_id}.zip',
        mimetype='application/zip'
    )


@api_v2.route('/tasks', methods=['GET'])
def list_tasks():
    """列出当前会话的所有任务"""
    session_task_id = session.get('task_id')
    user_tasks = []
    
    for task_id, task in active_tasks.items():
        if task_id == session_task_id or not session_task_id:
            user_tasks.append({
                'id': task['id'],
                'type': task['type'],
                'status': task['status'],
                'created_at': task['created_at'].isoformat(),
                'last_update': task['last_update'].isoformat()
            })
    
    return jsonify({
        'success': True,
        'tasks': user_tasks
    })


@api_v2.route('/config', methods=['GET'])
def get_config():
    """获取当前配置信息"""
    try:
        config_path = os.path.join(project_root, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 隐藏敏感信息
            safe_config = {
                'model': config.get('model', 'Unknown'),
                'api_url': config.get('api_url', 'Unknown'),
                'max_tokens': config.get('max_tokens', 8192),
                'temperature': config.get('temperature', 0.6)
            }
            
            return jsonify({
                'success': True,
                'config': safe_config
            })
        else:
            return jsonify({
                'success': False,
                'error': '配置文件不存在'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def list_output_files(output_dir: str) -> List[Dict]:
    """列出输出目录中的文件"""
    files = []
    
    if not os.path.exists(output_dir):
        return files
    
    for root, dirs, filenames in os.walk(output_dir):
        for filename in filenames:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, output_dir)
            file_size = os.path.getsize(file_path)
            
            # 获取文件预览（仅对小文件）
            preview = None
            if filename.endswith('.json') and file_size < 10000:  # 小于10KB的JSON文件
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) > 500:
                            preview = content[:500] + "..."
                        else:
                            preview = content
                except:
                    preview = "无法预览"
            
            files.append({
                'name': filename,
                'path': rel_path,
                'size': file_size,
                'preview': preview,
                'type': get_file_type(filename)
            })
    
    return files


def get_file_type(filename: str) -> str:
    """根据文件扩展名判断文件类型"""
    ext = filename.split('.')[-1].lower()
    type_map = {
        'json': 'json',
        'onnx': 'onnx',
        'csv': 'csv',
        'txt': 'text',
        'log': 'log',
        'py': 'python'
    }
    return type_map.get(ext, 'unknown')
