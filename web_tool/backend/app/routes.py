import os
import json
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app, send_from_directory
from werkzeug.utils import secure_filename
import tempfile
import shutil

from tools import get_tool, list_available_tools
from utils.file_utils import (
    allowed_file, save_uploaded_file, read_csv_file, read_template_file,
    get_template_variables, create_zip_archive, list_template_files,
    list_csv_files, save_generated_content, clean_old_files
)

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@api_bp.route('/tools', methods=['GET'])
def get_tools():
    """获取所有可用的工具"""
    tools = []
    for tool_name in list_available_tools():
        tool_config = current_app.config['TOOLS_CONFIG'].get(tool_name, {})
        tools.append({
            'name': tool_name,
            'display_name': tool_config.get('name', tool_name),
            'description': tool_config.get('description', ''),
            'templates_supported': tool_config.get('templates_supported', False),
            'csv_supported': tool_config.get('csv_supported', False)
        })
    return jsonify({'tools': tools})

@api_bp.route('/templates', methods=['GET'])
def get_templates():
    """获取所有可用的模板"""
    templates = list_template_files()
    return jsonify({'templates': templates})

@api_bp.route('/templates/<template_name>', methods=['GET'])
def get_template_content(template_name):
    """获取特定模板的内容"""
    try:
        template_path = Path(current_app.config['TEMPLATE_FOLDER']) / template_name
        if not template_path.exists():
            return jsonify({'error': 'Template not found'}), 404
        
        content = read_template_file(str(template_path))
        variables = get_template_variables(content)
        
        return jsonify({
            'content': content,
            'variables': variables,
            'name': template_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/csv-files', methods=['GET'])
def get_csv_files():
    """获取所有可用的CSV文件"""
    csv_files = list_csv_files()
    return jsonify({'csv_files': csv_files})

@api_bp.route('/csv-files/<csv_name>', methods=['GET'])
def get_csv_content(csv_name):
    """获取特定CSV文件的内容"""
    try:
        csv_path = Path(current_app.config['TEMPLATE_FOLDER']) / csv_name
        if not csv_path.exists():
            return jsonify({'error': 'CSV file not found'}), 404
        
        data = read_csv_file(str(csv_path))
        return jsonify({
            'data': data,
            'columns': list(data[0].keys()) if data else [],
            'name': csv_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/upload/template', methods=['POST'])
def upload_template():
    """上传模板文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.txt'):
            return jsonify({'error': 'Only .txt files are allowed for templates'}), 400
        
        filepath = save_uploaded_file(file, 'TEMPLATE_FOLDER')
        filename = Path(filepath).name
        
        # 读取内容并提取变量
        content = read_template_file(filepath)
        variables = get_template_variables(content)
        
        return jsonify({
            'message': 'Template uploaded successfully',
            'filename': filename,
            'variables': variables
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/upload/csv', methods=['POST'])
def upload_csv():
    """上传CSV文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only .csv files are allowed'}), 400
        
        filepath = save_uploaded_file(file, 'TEMPLATE_FOLDER')
        filename = Path(filepath).name
        
        # 读取CSV数据
        data = read_csv_file(filepath)
        
        return jsonify({
            'message': 'CSV uploaded successfully',
            'filename': filename,
            'data': data,
            'columns': list(data[0].keys()) if data else []
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/tools/<tool_name>/execute', methods=['POST'])
def execute_tool(tool_name):
    """执行工具"""
    try:
        # 获取工具配置
        tool_config = current_app.config['TOOLS_CONFIG'].get(tool_name)
        if not tool_config:
            return jsonify({'error': f'Tool {tool_name} not found'}), 404
        
        # 获取请求参数
        params = request.json
        if not params:
            return jsonify({'error': 'No parameters provided'}), 400
        
        # 创建输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(current_app.config['OUTPUT_FOLDER']) / f"{tool_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加输出目录到参数
        params['output_dir'] = str(output_dir)
        
        # 获取工具实例并执行
        tool = get_tool(tool_name, tool_config)
        
        # 这里暂时同步执行，实际应该使用WebSocket异步执行
        result = tool.execute(params)
        
        # 获取生成的文件列表
        output_files = tool.get_output_files(str(output_dir))
        
        return jsonify({
            'success': result['success'],
            'output': result['output'],
            'error': result.get('error', ''),
            'exit_code': result['exit_code'],
            'output_dir': str(output_dir),
            'output_files': output_files,
            'execution_id': f"{tool_name}_{timestamp}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/template/preview', methods=['POST'])
def preview_template():
    """预览模板渲染结果"""
    try:
        data = request.json
        template_content = data.get('template_content', '')
        variables = data.get('variables', {})
        
        if not template_content:
            return jsonify({'error': 'Template content is required'}), 400
        
        # 使用AI JSON Generator工具进行预览
        tool_config = current_app.config['TOOLS_CONFIG']['ai_json_generator']
        tool = get_tool('ai_json_generator', tool_config)
        
        # 渲染预览
        preview = tool.render_template_preview(template_content, variables)
        
        # 验证变量
        validation = tool.validate_template_variables(template_content, variables)
        
        return jsonify({
            'preview': preview,
            'validation': validation
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/download/<path:filepath>')
def download_file(filepath):
    """下载文件"""
    try:
        # 安全检查：确保文件在输出目录中
        output_folder = Path(current_app.config['OUTPUT_FOLDER'])
        file_path = output_folder / filepath
        
        # 检查路径是否在允许的目录内
        if not str(file_path.resolve()).startswith(str(output_folder.resolve())):
            return jsonify({'error': 'Access denied'}), 403
        
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/download-zip/<execution_id>')
def download_execution_results(execution_id):
    """下载执行结果的ZIP包"""
    try:
        # 查找对应的输出目录
        output_folder = Path(current_app.config['OUTPUT_FOLDER'])
        execution_dirs = list(output_folder.glob(f"{execution_id}*"))
        
        if not execution_dirs:
            return jsonify({'error': 'Execution results not found'}), 404
        
        execution_dir = execution_dirs[0]
        
        # 创建ZIP文件
        zip_path = output_folder / f"{execution_id}_results.zip"
        create_zip_archive(str(execution_dir), str(zip_path))
        
        return send_file(zip_path, as_attachment=True, download_name=f"{execution_id}_results.zip")
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/outputs/<execution_id>')
def get_execution_outputs(execution_id):
    """获取执行结果的文件列表"""
    try:
        output_folder = Path(current_app.config['OUTPUT_FOLDER'])
        execution_dirs = list(output_folder.glob(f"{execution_id}*"))
        
        if not execution_dirs:
            return jsonify({'error': 'Execution results not found'}), 404
        
        execution_dir = execution_dirs[0]
        
        files = []
        for file_path in execution_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(execution_dir)
                files.append({
                    'name': file_path.name,
                    'path': str(relative_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return jsonify({'files': files, 'execution_dir': str(execution_dir)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/outputs/<execution_id>/<path:file_path>')
def view_output_file(execution_id, file_path):
    """查看输出文件内容"""
    try:
        current_app.logger.info(f"查看文件请求: execution_id={execution_id}, file_path={file_path}")
        
        output_folder = Path(current_app.config['OUTPUT_FOLDER'])
        current_app.logger.info(f"输出文件夹: {output_folder}")
        
        execution_dirs = list(output_folder.glob(f"{execution_id}*"))
        current_app.logger.info(f"找到的执行目录: {execution_dirs}")
        
        if not execution_dirs:
            current_app.logger.error(f"未找到执行结果目录: {execution_id}")
            return jsonify({'error': f'Execution results not found for {execution_id}'}), 404
        
        execution_dir = execution_dirs[0]
        target_file = execution_dir / file_path
        current_app.logger.info(f"目标文件路径: {target_file}")
        
        # 安全检查
        if not str(target_file.resolve()).startswith(str(execution_dir.resolve())):
            current_app.logger.error(f"路径安全检查失败: {target_file}")
            return jsonify({'error': 'Access denied'}), 403
        
        if not target_file.exists():
            current_app.logger.error(f"文件不存在: {target_file}")
            # 列出目录内容以便调试
            if execution_dir.exists():
                files_in_dir = list(execution_dir.rglob('*'))
                current_app.logger.info(f"目录中的文件: {files_in_dir}")
            return jsonify({'error': f'File not found: {file_path}'}), 404
        
        # 读取文件内容
        try:
            # 检查文件大小，避免读取过大文件
            file_size = target_file.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB限制
                return jsonify({
                    'content': '[文件过大，无法显示]',
                    'filename': target_file.name,
                    'size': file_size,
                    'is_binary': True
                })
            
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            current_app.logger.info(f"成功读取文件: {target_file.name}, 大小: {file_size}")
            return jsonify({
                'content': content,
                'filename': target_file.name,
                'size': file_size
            })
            
        except UnicodeDecodeError as e:
            current_app.logger.warning(f"文件编码错误: {e}")
            # 对于二进制文件，返回基本信息
            return jsonify({
                'content': '[Binary file - cannot display content]',
                'filename': target_file.name,
                'size': target_file.stat().st_size,
                'is_binary': True
            })
        
    except Exception as e:
        current_app.logger.error(f"查看文件时发生错误: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# 清理任务
@api_bp.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """清理旧文件"""
    try:
        # 清理上传文件夹
        clean_old_files(current_app.config['UPLOAD_FOLDER'], max_age_hours=24)
        # 清理输出文件夹
        clean_old_files(current_app.config['OUTPUT_FOLDER'], max_age_hours=72)
        
        return jsonify({'message': 'Cleanup completed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
