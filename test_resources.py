#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本，用于检查资源文件是否能被正确找到
"""

import os
import sys
from ai_json_generator.generate_operator_testcase import find_resource_path

if __name__ == "__main__":
    # 测试关键资源文件
    resources_to_test = [
        "prompts/op_testcase.prompt",
        "data_files/onnx_operators.csv",
        "data_files/test_point.txt",
        "data_files/IR_JSON_FORMAT.md"
    ]
    
    print("测试资源文件查找:")
    all_found = True
    
    for resource in resources_to_test:
        path = find_resource_path(resource)
        if path:
            print(f"✓ 找到资源: {resource} -> {path}")
        else:
            print(f"✗ 未找到资源: {resource}")
            all_found = False
    
    if all_found:
        print("\n所有资源文件都能被正确找到!")
        sys.exit(0)
    else:
        print("\n警告: 有些资源文件未找到，可能会导致程序运行失败。")
        sys.exit(1) 