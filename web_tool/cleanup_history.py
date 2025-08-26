#!/usr/bin/env python3
"""
清理历史执行结果脚本

这个脚本用于清理Web工具的历史执行结果，包括：
1. 删除旧的输出文件和目录
2. 清理临时文件
3. 压缩或删除过期的日志文件
4. 优化存储空间

使用方法:
    python cleanup_history.py [选项]

选项:
    --dry-run       只显示将要删除的文件，不实际删除
    --days N        删除N天前的文件 (默认: 7天)
    --force         强制删除，不询问确认
    --verbose       显示详细信息
    --help          显示帮助信息
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import json
import tempfile


class HistoryCleanup:
    def __init__(self, web_tool_dir=None):
        """初始化清理工具"""
        if web_tool_dir:
            self.web_tool_dir = Path(web_tool_dir)
        else:
            # 自动检测web_tool目录
            script_dir = Path(__file__).parent
            self.web_tool_dir = script_dir
            
        self.shared_dir = self.web_tool_dir / 'shared'
        self.outputs_dir = self.shared_dir / 'outputs'
        self.uploads_dir = self.shared_dir / 'uploads'
        self.logs_dir = self.web_tool_dir / 'logs'
        
        self.deleted_files = []
        self.deleted_dirs = []
        self.freed_space = 0
        
    def get_dir_size(self, directory):
        """计算目录大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        pass
        except (OSError, FileNotFoundError):
            pass
        return total_size
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.2f} {units[unit_index]}"
    
    def is_old_file(self, file_path, days_threshold):
        """检查文件是否过期"""
        try:
            mtime = os.path.getmtime(file_path)
            file_date = datetime.fromtimestamp(mtime)
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            return file_date < threshold_date
        except (OSError, FileNotFoundError):
            return True  # 如果无法获取时间，认为是过期文件
    
    def clean_outputs(self, days_threshold, dry_run=False, verbose=False):
        """清理输出目录"""
        print(f"\n🗂️  清理输出目录: {self.outputs_dir}")
        
        if not self.outputs_dir.exists():
            print("   输出目录不存在，跳过")
            return
        
        cleaned_count = 0
        cleaned_size = 0
        
        for item in self.outputs_dir.iterdir():
            if item.is_dir():
                if self.is_old_file(item, days_threshold):
                    dir_size = self.get_dir_size(item)
                    
                    if verbose:
                        print(f"   📁 {item.name} ({self.format_size(dir_size)}) - {datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
                    
                    if not dry_run:
                        try:
                            shutil.rmtree(item)
                            self.deleted_dirs.append(str(item))
                            cleaned_size += dir_size
                            cleaned_count += 1
                        except Exception as e:
                            print(f"   ❌ 删除失败: {item.name} - {e}")
                    else:
                        cleaned_size += dir_size
                        cleaned_count += 1
        
        self.freed_space += cleaned_size
        action = "将删除" if dry_run else "已删除"
        print(f"   ✅ {action} {cleaned_count} 个目录，释放 {self.format_size(cleaned_size)} 空间")
    
    def clean_uploads(self, days_threshold, dry_run=False, verbose=False):
        """清理上传目录"""
        print(f"\n📤 清理上传目录: {self.uploads_dir}")
        
        if not self.uploads_dir.exists():
            print("   上传目录不存在，跳过")
            return
        
        cleaned_count = 0
        cleaned_size = 0
        
        for item in self.uploads_dir.iterdir():
            if item.is_file() and self.is_old_file(item, days_threshold):
                file_size = item.stat().st_size
                
                if verbose:
                    print(f"   📄 {item.name} ({self.format_size(file_size)}) - {datetime.fromtimestamp(item.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
                
                if not dry_run:
                    try:
                        item.unlink()
                        self.deleted_files.append(str(item))
                        cleaned_size += file_size
                        cleaned_count += 1
                    except Exception as e:
                        print(f"   ❌ 删除失败: {item.name} - {e}")
                else:
                    cleaned_size += file_size
                    cleaned_count += 1
        
        self.freed_space += cleaned_size
        action = "将删除" if dry_run else "已删除"
        print(f"   ✅ {action} {cleaned_count} 个文件，释放 {self.format_size(cleaned_size)} 空间")
    
    def clean_temp_files(self, dry_run=False, verbose=False):
        """清理临时文件"""
        print(f"\n🗑️  清理临时文件")
        
        temp_patterns = [
            '/tmp/tmp*csv',
            '/tmp/tmp*txt',
            '/tmp/tmp*prompt*',
        ]
        
        cleaned_count = 0
        cleaned_size = 0
        
        import glob
        for pattern in temp_patterns:
            for temp_file in glob.glob(pattern):
                temp_path = Path(temp_file)
                if temp_path.exists() and temp_path.is_file():
                    # 检查文件是否超过1小时未修改
                    if self.is_old_file(temp_path, 0.04):  # 0.04天 ≈ 1小时
                        file_size = temp_path.stat().st_size
                        
                        if verbose:
                            print(f"   🗑️  {temp_path.name} ({self.format_size(file_size)})")
                        
                        if not dry_run:
                            try:
                                temp_path.unlink()
                                cleaned_size += file_size
                                cleaned_count += 1
                            except Exception as e:
                                if verbose:
                                    print(f"   ❌ 删除失败: {temp_path.name} - {e}")
                        else:
                            cleaned_size += file_size
                            cleaned_count += 1
        
        self.freed_space += cleaned_size
        action = "将删除" if dry_run else "已删除"
        print(f"   ✅ {action} {cleaned_count} 个临时文件，释放 {self.format_size(cleaned_size)} 空间")
    
    def clean_logs(self, days_threshold, dry_run=False, verbose=False):
        """清理日志文件"""
        print(f"\n📋 清理日志文件: {self.logs_dir}")
        
        if not self.logs_dir.exists():
            print("   日志目录不存在，跳过")
            return
        
        cleaned_count = 0
        cleaned_size = 0
        
        for log_file in self.logs_dir.glob('*.log'):
            if self.is_old_file(log_file, days_threshold):
                file_size = log_file.stat().st_size
                
                if verbose:
                    print(f"   📋 {log_file.name} ({self.format_size(file_size)}) - {datetime.fromtimestamp(log_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")
                
                if not dry_run:
                    try:
                        log_file.unlink()
                        cleaned_size += file_size
                        cleaned_count += 1
                    except Exception as e:
                        print(f"   ❌ 删除失败: {log_file.name} - {e}")
                else:
                    cleaned_size += file_size
                    cleaned_count += 1
        
        self.freed_space += cleaned_size
        action = "将删除" if dry_run else "已删除"
        print(f"   ✅ {action} {cleaned_count} 个日志文件，释放 {self.format_size(cleaned_size)} 空间")
    
    def show_summary(self, dry_run=False):
        """显示清理摘要"""
        print(f"\n{'='*60}")
        print(f"🧹 清理摘要")
        print(f"{'='*60}")
        
        if dry_run:
            print(f"🔍 预览模式 - 将要清理:")
        else:
            print(f"✅ 清理完成:")
        
        print(f"   📁 删除目录: {len(self.deleted_dirs)}")
        print(f"   📄 删除文件: {len(self.deleted_files)}")
        print(f"   💾 释放空间: {self.format_size(self.freed_space)}")
        
        if not dry_run and self.freed_space > 0:
            print(f"\n🎉 清理成功！释放了 {self.format_size(self.freed_space)} 的存储空间")
        elif dry_run and self.freed_space > 0:
            print(f"\n📊 预计可释放 {self.format_size(self.freed_space)} 的存储空间")
        else:
            print(f"\n✨ 没有找到需要清理的文件")
    
    def run_cleanup(self, days_threshold=7, dry_run=False, force=False, verbose=False):
        """运行清理任务"""
        print(f"🧹 AI Web工具历史清理")
        print(f"{'='*60}")
        print(f"📂 工作目录: {self.web_tool_dir}")
        print(f"📅 清理阈值: {days_threshold} 天前的文件")
        print(f"🔍 模式: {'预览模式' if dry_run else '清理模式'}")
        
        if not force and not dry_run:
            response = input(f"\n⚠️  确定要删除 {days_threshold} 天前的历史文件吗? (y/N): ")
            if response.lower() != 'y':
                print("❌ 取消清理操作")
                return
        
        # 执行清理任务
        self.clean_outputs(days_threshold, dry_run, verbose)
        self.clean_uploads(days_threshold, dry_run, verbose)
        self.clean_temp_files(dry_run, verbose)
        self.clean_logs(days_threshold, dry_run, verbose)
        
        # 显示摘要
        self.show_summary(dry_run)


def main():
    parser = argparse.ArgumentParser(
        description="清理AI Web工具的历史执行结果",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
    python cleanup_history.py --dry-run              # 预览将要删除的文件
    python cleanup_history.py --days 3 --verbose    # 删除3天前的文件，显示详细信息
    python cleanup_history.py --force               # 强制清理，不询问确认
        """
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='只显示将要删除的文件，不实际删除'
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=7,
        help='删除N天前的文件 (默认: 7天)'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='强制删除，不询问确认'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细信息'
    )
    
    parser.add_argument(
        '--web-tool-dir',
        type=str,
        help='指定web_tool目录路径'
    )
    
    args = parser.parse_args()
    
    # 验证参数
    if args.days < 0:
        print("❌ 错误: --days 参数必须是非负数")
        sys.exit(1)
    
    try:
        # 创建清理工具实例
        cleanup = HistoryCleanup(args.web_tool_dir)
        
        # 运行清理
        cleanup.run_cleanup(
            days_threshold=args.days,
            dry_run=args.dry_run,
            force=args.force,
            verbose=args.verbose
        )
        
    except KeyboardInterrupt:
        print(f"\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 清理过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
