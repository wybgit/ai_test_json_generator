#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Example script demonstrating usage of the generate_json.py tool
with the new features: file-based replacements and debug mode
"""

import os
import subprocess
import sys

def create_example_files():
    """Create example files for replacements"""
    
    # Create a directory for example files
    os.makedirs("example_files", exist_ok=True)
    
    # Create a file with operator parameters
    params_content = """输入A和B，输出C。
属性：
- axis: 用于指定广播的轴，默认为None
- broadcast: 是否启用广播，默认为1"""
    
    with open("example_files/params.txt", "w", encoding="utf-8") as f:
        f.write(params_content)
    print(f"Created example_files/params.txt with {len(params_content)} characters")
    
    # Create a file with test requirements
    requirements_content = """测试基本的Add算子，要求：
1. 测试两个不同shape的tensor相加，需要支持广播
2. 验证输出tensor的shape符合广播规则
3. 包含至少3个不同的测试用例
4. 每个用例应有合理的name和purpose描述"""
    
    with open("example_files/requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements_content)
    print(f"Created example_files/requirements.txt with {len(requirements_content)} characters")
    
    # Create a file with IR JSON requirements
    ir_json_content = """IR模型描述应包含以下内容：
- opset_import至少指定为13
- graph部分需包含inputs、outputs完整定义
- 每个节点需要有明确的node_name
- 需要定义node_inputs和node_outputs
- 属性设置需符合ONNX规范"""
    
    with open("example_files/ir_json_req.txt", "w", encoding="utf-8") as f:
        f.write(ir_json_content)
    print(f"Created example_files/ir_json_req.txt with {len(ir_json_content)} characters")

def run_basic_example():
    """Run a basic example of generating a test case for the Add operator"""
    
    # Create the output directory
    os.makedirs("example_output", exist_ok=True)
    
    # Define the command
    cmd = [
        sys.executable,
        "generate_json.py",
        "--template", "prompts/op_testcase.prompt",
        "--replacements", "算子名=Add,算子参数=输入A和B，输出C。无特殊属性,用例要求=测试基本的Add算子，支持广播,IR_JSON要求=包含inputs、outputs、node_name、node_inputs、node_outputs",
        "--output-folder", "example_output",
        "--output-name", "add_basic",
        "--output-ext", "json"
    ]
    
    # Print the command for reference
    print("\nRunning basic example:")
    print(" ".join(cmd))
    print("-" * 40)
    
    # Execute the command
    try:
        subprocess.run(cmd, check=True)
        print("\nBasic example completed")
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return

def run_file_replacements_example():
    """Run an example using file-based replacements"""
    
    # Create the output directory
    os.makedirs("example_output", exist_ok=True)
    
    # Define the command
    cmd = [
        sys.executable,
        "generate_json.py",
        "--template", "prompts/op_testcase.prompt",
        "--replacements", f"算子名=Add,算子参数=example_files/params.txt,用例要求=example_files/requirements.txt,IR_JSON要求=example_files/ir_json_req.txt",
        "--output-folder", "example_output",
        "--output-name", "add_with_file_replacements",
        "--output-ext", "json"
    ]
    
    # Print the command for reference
    print("\nRunning file-based replacements example:")
    print(" ".join(cmd))
    print("-" * 40)
    
    # Execute the command
    try:
        subprocess.run(cmd, check=True)
        print("\nFile-based replacements example completed")
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return

def run_debug_mode_example():
    """Run an example with debug mode enabled"""
    
    # Create the output directory
    os.makedirs("example_output", exist_ok=True)
    
    # Define the command
    cmd = [
        sys.executable,
        "generate_json.py",
        "--template", "prompts/op_testcase.prompt",
        "--replacements", "算子名=Conv,算子参数=输入X和W，输出Y。属性：kernel_size, strides, pads",
        "--output-folder", "example_output",
        "--output-name", "conv_with_debug",
        "--output-ext", "json",
        "--debug"
    ]
    
    # Print the command for reference
    print("\nRunning debug mode example:")
    print(" ".join(cmd))
    print("-" * 40)
    
    # Execute the command
    try:
        subprocess.run(cmd, check=True)
        print("\nDebug mode example completed")
        
        # List the debug files created
        debug_files = [f for f in os.listdir("example_output") if f.startswith("conv_with_debug")]
        print(f"\nDebug files created:")
        for file in debug_files:
            path = os.path.join("example_output", file)
            print(f"- {file} ({os.path.getsize(path)} bytes)")
            
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return

if __name__ == "__main__":
    print("AI JSON Generator Example Usage")
    print("=" * 40)
    
    # Create example files for replacements
    create_example_files()
    
    # Run the examples
    run_basic_example()
    run_file_replacements_example()
    run_debug_mode_example()
    
    print("\nAll examples completed. Check the example_output directory for results.") 