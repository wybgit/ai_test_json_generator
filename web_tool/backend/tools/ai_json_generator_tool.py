import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Template, TemplateSyntaxError
from tools.base_tool import BaseTool
from utils.file_utils import read_template_file, read_csv_file, get_template_variables

class AIJsonGeneratorTool(BaseTool):
    """AI JSON Generator 工具实现"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__('ai_json_generator', config)
        self.executable = config.get('executable', 'ai-json-generator')
        self.default_args = config.get('default_args', [])
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        required_fields = ['template_content', 'output_dir']
        
        for field in required_fields:
            if field not in params or not params[field]:
                return False
        
        # 如果使用CSV模式，检查CSV数据
        if params.get('use_csv') and not params.get('csv_data'):
            return False
        
        # 如果使用手动模式，检查变量值
        if not params.get('use_csv') and not params.get('variable_values'):
            return False
            
        return True
    
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """构建执行命令"""
        # 创建临时模板文件
        template_file = self._create_temp_template(params['template_content'])
        
        # 基础命令
        command = [self.executable, '--direct-prompt', template_file]
        
        # 添加默认参数
        command.extend(self.default_args)
        
        # 输出目录
        command.extend(['-o', params['output_dir']])
        
        # 如果使用CSV
        if params.get('use_csv') and params.get('csv_data'):
            csv_file = self._create_temp_csv(params['csv_data'])
            command.extend(['--batch-csv', csv_file])
        else:
            # 手动变量模式 - 需要为每个变量组合创建CSV
            csv_file = self._create_csv_from_variables(params.get('variable_values', {}))
            command.extend(['--batch-csv', csv_file])
        
        # 额外参数
        if params.get('max_retries'):
            command.extend(['--max-retries', str(params['max_retries'])])
        
        return command
    
    def _create_temp_template(self, content: str) -> str:
        """创建临时模板文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.prompt.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            return f.name
    
    def _create_temp_csv(self, csv_data: List[Dict[str, Any]]) -> str:
        """创建临时CSV文件"""
        import csv
        
        if not csv_data:
            raise ValueError("CSV data is empty")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
            if csv_data:
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            return f.name
    
    def _create_csv_from_variables(self, variable_values: Dict[str, str]) -> str:
        """从变量值创建CSV文件"""
        import csv
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
            if variable_values:
                writer = csv.DictWriter(f, fieldnames=variable_values.keys())
                writer.writeheader()
                writer.writerow(variable_values)
            return f.name
    
    def get_supported_templates(self) -> List[str]:
        """获取支持的模板"""
        from flask import current_app
        template_folder = Path(current_app.config['TEMPLATE_FOLDER'])
        templates = []
        
        for template_file in template_folder.glob('*.prompt.txt'):
            templates.append(template_file.name)
        
        return templates
    
    def get_output_files(self, output_dir: str) -> List[str]:
        """获取生成的输出文件"""
        output_path = Path(output_dir)
        if not output_path.exists():
            return []
        
        files = []
        for file_path in output_path.rglob('*'):
            if file_path.is_file():
                files.append(str(file_path.relative_to(output_path)))
        
        return sorted(files)
    
    def render_template_preview(self, template_content: str, variables: Dict[str, str]) -> str:
        """渲染模板预览"""
        try:
            template = Template(template_content)
            return template.render(**variables)
        except TemplateSyntaxError as e:
            return f"模板语法错误: {str(e)}"
        except Exception as e:
            return f"渲染错误: {str(e)}"
    
    def validate_template_variables(self, template_content: str, variables: Dict[str, str]) -> Dict[str, Any]:
        """验证模板变量"""
        template_vars = get_template_variables(template_content)
        
        missing_vars = [var for var in template_vars if var not in variables]
        extra_vars = [var for var in variables.keys() if var not in template_vars]
        
        return {
            'template_variables': template_vars,
            'missing_variables': missing_vars,
            'extra_variables': extra_vars,
            'is_valid': len(missing_vars) == 0
        }
