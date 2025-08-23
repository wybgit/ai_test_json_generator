import os
import csv
import json
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from werkzeug.utils import secure_filename
from flask import current_app
import pandas as pd

def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file, folder: str) -> str:
    """保存上传的文件"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 添加时间戳避免文件名冲突
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        
        filepath = Path(current_app.config[folder]) / filename
        file.save(filepath)
        return str(filepath)
    raise ValueError("Invalid file or file type not allowed")

def read_csv_file(filepath: str) -> List[Dict[str, Any]]:
    """读取CSV文件并返回数据"""
    try:
        df = pd.read_csv(filepath)
        return df.to_dict('records')
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")

def read_template_file(filepath: str) -> str:
    """读取模板文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Error reading template file: {str(e)}")

def get_template_variables(template_content: str) -> List[str]:
    """从模板内容中提取Jinja2变量"""
    import re
    # 匹配 {{ variable_name }} 格式的变量
    pattern = r'\{\{\s*([^}]+)\s*\}\}'
    variables = re.findall(pattern, template_content)
    # 清理变量名，去除空格
    return [var.strip() for var in variables]

def create_zip_archive(folder_path: str, zip_path: str) -> str:
    """创建文件夹的ZIP压缩包"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        folder = Path(folder_path)
        for file_path in folder.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(folder)
                zipf.write(file_path, arcname)
    return zip_path

def list_template_files() -> List[Dict[str, str]]:
    """列出所有可用的模板文件"""
    template_folder = Path(current_app.config['TEMPLATE_FOLDER'])
    templates = []
    
    for file_path in template_folder.glob('*.txt'):
        if file_path.name.endswith('.prompt.txt'):
            templates.append({
                'name': file_path.name,
                'path': str(file_path),
                'display_name': file_path.stem.replace('_', ' ').title()
            })
    
    return templates

def list_csv_files() -> List[Dict[str, str]]:
    """列出所有可用的CSV文件"""
    template_folder = Path(current_app.config['TEMPLATE_FOLDER'])
    csv_files = []
    
    for file_path in template_folder.glob('*.csv'):
        csv_files.append({
            'name': file_path.name,
            'path': str(file_path),
            'display_name': file_path.stem.replace('_', ' ').title()
        })
    
    return csv_files

def save_generated_content(content: str, filename: str, output_dir: str) -> str:
    """保存生成的内容到文件"""
    output_path = Path(output_dir) / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return str(output_path)

def clean_old_files(folder_path: str, max_age_hours: int = 24):
    """清理超过指定时间的旧文件"""
    import time
    current_time = time.time()
    folder = Path(folder_path)
    
    for file_path in folder.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_hours * 3600:  # 转换为秒
                try:
                    file_path.unlink()
                except OSError:
                    pass  # 忽略删除失败的文件
