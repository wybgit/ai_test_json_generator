from flask import current_app, request
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
import threading
import uuid

from app import socketio
from tools import get_tool

# 存储活动的执行任务
active_executions = {}

@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_execution')
def handle_join_execution(data):
    """加入执行任务房间"""
    execution_id = data.get('execution_id')
    if execution_id:
        join_room(execution_id)
        emit('joined_execution', {'execution_id': execution_id})

@socketio.on('leave_execution')
def handle_leave_execution(data):
    """离开执行任务房间"""
    execution_id = data.get('execution_id')
    if execution_id:
        leave_room(execution_id)
        emit('left_execution', {'execution_id': execution_id})

@socketio.on('execute_tool_async')
def handle_execute_tool_async(data):
    """异步执行工具"""
    try:
        tool_name = data.get('tool_name')
        params = data.get('params', {})
        
        # 创建输出目录并生成执行ID
        from pathlib import Path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        execution_id = f"{tool_name}_{timestamp}"
        
        # 获取工具配置
        tool_config = current_app.config['TOOLS_CONFIG'].get(tool_name)
        if not tool_config:
            emit('execution_error', {
                'execution_id': execution_id,
                'error': f'Tool {tool_name} not found'
            })
            return
        
        # 创建输出目录
        output_dir = Path(current_app.config['OUTPUT_FOLDER']) / execution_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加输出目录到参数
        params['output_dir'] = str(output_dir)
        
        # 加入房间
        join_room(execution_id)
        
        # 发送执行开始事件
        emit('execution_started', {
            'execution_id': execution_id,
            'tool_name': tool_name,
            'output_dir': str(output_dir),
            'timestamp': datetime.now().isoformat()
        }, room=execution_id)
        
        # 在后台线程执行工具，需要传递Flask应用实例
        thread = threading.Thread(
            target=_execute_tool_in_background,
            args=(tool_name, tool_config, params, execution_id, current_app._get_current_object())
        )
        thread.daemon = True
        
        # 存储执行信息
        active_executions[execution_id] = {
            'thread': thread,
            'tool_name': tool_name,
            'params': params,
            'start_time': datetime.now(),
            'status': 'running'
        }
        
        thread.start()
        
    except Exception as e:
        emit('execution_error', {
            'execution_id': execution_id if 'execution_id' in locals() else 'unknown',
            'error': str(e)
        })

def _execute_tool_in_background(tool_name, tool_config, params, execution_id, app):
    """在后台执行工具"""
    try:
        # 在新线程中需要创建应用上下文
        with app.app_context():
            # 获取工具实例
            tool = get_tool(tool_name, tool_config)
            
            # 定义日志回调函数
            def log_callback(line):
                socketio.emit('execution_log', {
                    'execution_id': execution_id,
                    'log': line,
                    'timestamp': datetime.now().isoformat()
                }, room=execution_id)
            
            # 执行工具
            result = tool.execute(params, log_callback)
            
            # 获取生成的文件列表
            output_files = tool.get_output_files(params['output_dir'])
            
            # 更新执行状态
            if execution_id in active_executions:
                active_executions[execution_id]['status'] = 'completed'
                active_executions[execution_id]['end_time'] = datetime.now()
            
            # 发送执行完成事件
            socketio.emit('execution_completed', {
                'execution_id': execution_id,
                'success': result['success'],
                'output': result['output'],
                'error': result.get('error', ''),
                'exit_code': result['exit_code'],
                'output_files': output_files,
                'timestamp': datetime.now().isoformat()
            }, room=execution_id)
        
    except Exception as e:
        # 更新执行状态
        if execution_id in active_executions:
            active_executions[execution_id]['status'] = 'failed'
            active_executions[execution_id]['end_time'] = datetime.now()
        
        # 发送执行错误事件
        socketio.emit('execution_error', {
            'execution_id': execution_id,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, room=execution_id)

@socketio.on('stop_execution')
def handle_stop_execution(data):
    """停止执行"""
    execution_id = data.get('execution_id')
    
    if execution_id not in active_executions:
        emit('execution_error', {
            'execution_id': execution_id,
            'error': 'Execution not found'
        })
        return
    
    try:
        execution_info = active_executions[execution_id]
        
        # 停止工具执行
        tool_name = execution_info['tool_name']
        tool_config = current_app.config['TOOLS_CONFIG'].get(tool_name)
        
        if tool_config:
            tool = get_tool(tool_name, tool_config)
            tool.stop()
        
        # 更新状态
        execution_info['status'] = 'stopped'
        execution_info['end_time'] = datetime.now()
        
        emit('execution_stopped', {
            'execution_id': execution_id,
            'timestamp': datetime.now().isoformat()
        }, room=execution_id)
        
    except Exception as e:
        emit('execution_error', {
            'execution_id': execution_id,
            'error': f'Error stopping execution: {str(e)}'
        })

@socketio.on('get_execution_status')
def handle_get_execution_status(data):
    """获取执行状态"""
    execution_id = data.get('execution_id')
    
    if execution_id in active_executions:
        execution_info = active_executions[execution_id]
        emit('execution_status', {
            'execution_id': execution_id,
            'status': execution_info['status'],
            'tool_name': execution_info['tool_name'],
            'start_time': execution_info['start_time'].isoformat(),
            'end_time': execution_info.get('end_time', '').isoformat() if execution_info.get('end_time') else None
        })
    else:
        emit('execution_error', {
            'execution_id': execution_id,
            'error': 'Execution not found'
        })

@socketio.on('list_active_executions')
def handle_list_active_executions():
    """列出活动的执行"""
    executions = []
    for execution_id, info in active_executions.items():
        executions.append({
            'execution_id': execution_id,
            'tool_name': info['tool_name'],
            'status': info['status'],
            'start_time': info['start_time'].isoformat(),
            'end_time': info.get('end_time', '').isoformat() if info.get('end_time') else None
        })
    
    emit('active_executions', {'executions': executions})
