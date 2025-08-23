from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
import subprocess
import threading
import queue
import os
import signal
from pathlib import Path

class BaseTool(ABC):
    """工具基类，定义工具的通用接口"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.process = None
        self.output_queue = queue.Queue()
        self.error_queue = queue.Queue()
        
    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数是否有效"""
        pass
    
    @abstractmethod
    def build_command(self, params: Dict[str, Any]) -> List[str]:
        """构建执行命令"""
        pass
    
    def execute(self, params: Dict[str, Any], log_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """执行工具命令"""
        try:
            # 验证参数
            if not self.validate_params(params):
                return {
                    'success': False,
                    'error': 'Invalid parameters',
                    'output': '',
                    'exit_code': -1
                }
            
            # 构建命令
            command = self.build_command(params)
            
            # 记录即将执行的命令
            if log_callback:
                log_callback("=" * 50)
                log_callback(f"执行工具: {self.name}")
                log_callback(f"执行命令: {' '.join(command)}")
                log_callback("=" * 50)
            
            # 执行命令
            result = self._run_command(command, log_callback)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '',
                'exit_code': -1
            }
    
    def _run_command(self, command: List[str], log_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """运行命令并捕获输出"""
        try:
            # 设置工作目录为ai_json_generator项目根目录
            from flask import current_app
            cwd = current_app.config['AI_JSON_GENERATOR_PATH']
            
            # 启动进程
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=str(cwd)
            )
            
            output_lines = []
            
            # 读取输出
            for line in iter(self.process.stdout.readline, ''):
                line = line.rstrip()
                if line:
                    output_lines.append(line)
                    if log_callback:
                        log_callback(line)
            
            # 等待进程结束
            self.process.wait()
            exit_code = self.process.returncode
            
            return {
                'success': exit_code == 0,
                'output': '\n'.join(output_lines),
                'exit_code': exit_code,
                'error': '' if exit_code == 0 else f'Command exited with code {exit_code}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': '\n'.join(output_lines) if 'output_lines' in locals() else '',
                'exit_code': -1
            }
        finally:
            self.process = None
    
    def stop(self):
        """停止当前执行的进程"""
        if self.process and self.process.poll() is None:
            try:
                # 发送SIGTERM信号
                self.process.terminate()
                # 等待3秒
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # 强制杀死进程
                self.process.kill()
                self.process.wait()
            except Exception:
                pass
            finally:
                self.process = None
    
    def is_running(self) -> bool:
        """检查工具是否正在运行"""
        return self.process is not None and self.process.poll() is None
    
    @abstractmethod
    def get_supported_templates(self) -> List[str]:
        """获取支持的模板列表"""
        pass
    
    @abstractmethod
    def get_output_files(self, output_dir: str) -> List[str]:
        """获取生成的输出文件列表"""
        pass
