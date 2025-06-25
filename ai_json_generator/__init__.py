#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI JSON Generator - A tool for generating AI model JSON descriptions based on templates.
"""

import os
import sys
import importlib.util
import importlib.resources

from .generate_json import LLMJsonGenerator, parse_key_value_pairs
from .version import __version__, VERSION

# 尝试初始化包内子目录为模块
subdirectories = ['prompts', 'data_files']
package_path = os.path.dirname(__file__)

for subdir in subdirectories:
    subdir_path = os.path.join(package_path, subdir)
    
    # 如果子目录存在，确保它有一个__init__.py文件
    if os.path.exists(subdir_path) and os.path.isdir(subdir_path):
        init_path = os.path.join(subdir_path, '__init__.py')
        if not os.path.exists(init_path):
            try:
                with open(init_path, 'w') as f:
                    f.write("# Auto-generated __init__.py for package resources\n")
            except Exception:
                pass

__all__ = ['LLMJsonGenerator', 'parse_key_value_pairs', '__version__', 'VERSION'] 