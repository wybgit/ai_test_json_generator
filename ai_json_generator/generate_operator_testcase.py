#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script that generates operator test cases using data from external files.
Takes operator names as input and fetches parameters from data files.
Supports multiple operators and various graph connection patterns.
"""

import os
import sys
import argparse
import csv
import subprocess
import logging
import tempfile
import shutil
import json
import time
import requests
import re
from typing import Dict, Any, List, Tuple, Optional
# 导入资源查找相关模块
import site
import importlib
from importlib import import_module
import importlib.resources as pkg_resources

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('operator_testcase_generator')

def read_csv_to_dict(csv_path):
    """
    Read a CSV file and convert it to a dictionary where the first column is the key.
    
    Args:
        csv_path: Path to the CSV file
    
    Returns:
        Dictionary with first column values as keys and the rest of the row as a dictionary
    """
    result = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            headers = next(csv_reader)
            
            key_column = headers[0]
            
            for row in csv_reader:
                if not row:  # Skip empty rows
                    continue
                    
                key = row[0]
                values = {}
                for i in range(1, len(headers)):
                    if i < len(row):
                        values[headers[i]] = row[i]
                    else:
                        values[headers[i]] = ""
                        
                result[key] = values
                
        return result
    except Exception as e:
        logger.error(f"Error reading CSV file {csv_path}: {e}")
        return {}

def find_operator_params(operator_name, csv_path):
    """
    Find the parameters for a specific operator in the CSV file.
    Case-insensitive matching is used to support different capitalizations.
    
    Args:
        operator_name: Name of the ONNX operator
        csv_path: Path to the CSV file with operator specifications
    
    Returns:
        String containing operator parameters or None if not found
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            
            # Read headers
            headers = next(csv_reader)
            
            # Find name column index (it should be 'operator_name')
            name_idx = -1
            for i, header in enumerate(headers):
                if header.lower() == 'operator_name':
                    name_idx = i
                    break
            
            if name_idx == -1:
                logger.error(f"Could not find operator_name column in CSV: {headers}")
                return None
            
            # Convert operator_name to lower case for case-insensitive matching
            op_name_lower = operator_name.lower()
            
            # Search for the operator
            for row in csv_reader:
                if len(row) > name_idx and row[name_idx].strip().lower() == op_name_lower:
                    # Found the operator, now extract all parameters
                    params = {}
                    for i, header in enumerate(headers):
                        if i < len(row) and row[i]:
                            params[header] = row[i]
                    
                    # Format the parameters as a string
                    formatted_params = format_operator_params(params, headers)
                    logger.info(f"Found parameters for {operator_name}: {formatted_params[:100]}...")
                    return formatted_params
            
            logger.warning(f"Operator '{operator_name}' not found in CSV file")
            return None
    
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return None

def format_operator_params(params, headers):
    """
    Format the operator parameters into a structured string.
    
    Args:
        params: Dictionary of parameter key-value pairs
        headers: Original CSV headers for column order
    
    Returns:
        Formatted string with operator information
    """
    formatted = []
    
    # Add description if available
    if 'description' in params:
        formatted.append(f"描述: {params['description']}")
    
    # Add versions if available
    if 'versions' in params:
        formatted.append(f"支持版本: {params['versions']}")
    
    # Format inputs
    inputs = []
    if 'input_name' in params:
        input_names = params['input_name'].split(',')
        input_types = params.get('input_type', '').split(',')
        input_descriptions = params.get('input_description', '').split(';')
        
        for i in range(len(input_names)):
            input_info = f"{input_names[i].strip()}"
            
            if i < len(input_types) and input_types[i].strip():
                input_info += f" (类型: {input_types[i].strip()})"
            
            if i < len(input_descriptions) and input_descriptions[i].strip():
                input_info += f" - {input_descriptions[i].strip()}"
            
            inputs.append(input_info)
        
        if inputs:
            formatted.append("输入:")
            formatted.extend([f"  - {input_item}" for input_item in inputs])
    
    # Format outputs
    outputs = []
    if 'output_name' in params:
        output_names = params['output_name'].split(',')
        output_types = params.get('output_type', '').split(',')
        output_descriptions = params.get('output_description', '').split(';')
        
        for i in range(len(output_names)):
            output_info = f"{output_names[i].strip()}"
            
            if i < len(output_types) and output_types[i].strip():
                output_info += f" (类型: {output_types[i].strip()})"
            
            if i < len(output_descriptions) and output_descriptions[i].strip():
                output_info += f" - {output_descriptions[i].strip()}"
            
            outputs.append(output_info)
        
        if outputs:
            formatted.append("输出:")
            formatted.extend([f"  - {output_item}" for output_item in outputs])
    
    # Format attributes
    attributes = []
    if 'attribute_name' in params and params['attribute_name']:
        attr_names = params['attribute_name'].split(',')
        attr_types = params.get('attribute_type', '').split(',')
        attr_descriptions = params.get('attribute_description', '').split(';')
        
        for i in range(len(attr_names)):
            if not attr_names[i].strip():
                continue
                
            attr_info = f"{attr_names[i].strip()}"
            
            if i < len(attr_types) and attr_types[i].strip():
                attr_info += f" (类型: {attr_types[i].strip()})"
            
            if i < len(attr_descriptions) and attr_descriptions[i].strip():
                attr_info += f" - {attr_descriptions[i].strip()}"
            
            attributes.append(attr_info)
        
        if attributes:
            formatted.append("属性:")
            formatted.extend([f"  - {attr_item}" for attr_item in attributes])
    
    # Add execution unit if available
    if 'npu_unit' in params and params['npu_unit']:
        formatted.append(f"执行单元: {params['npu_unit']}")
    
    return "\n".join(formatted)

def format_test_point_info(test_point_data):
    """
    Format test point information into a structured string.
    
    Args:
        test_point_data: Dictionary of test point information
    
    Returns:
        Formatted string with test point information
    """
    formatted = []
    
    # Extract basic information
    for key in ['name', 'description', 'purpose']:
        if key in test_point_data and test_point_data[key]:
            formatted.append(f"{key.capitalize()}: {test_point_data[key]}")
    
    # Extract test cases
    if 'test_cases' in test_point_data and test_point_data['test_cases']:
        formatted.append("Test Cases:")
        for case in test_point_data['test_cases']:
            formatted.append(f"  - {case}")
    
    # Extract input requirements
    if 'input_requirements' in test_point_data and test_point_data['input_requirements']:
        formatted.append("Input Requirements:")
        for req in test_point_data['input_requirements']:
            formatted.append(f"  - {req}")
    
    # Extract output expectations
    if 'output_expectations' in test_point_data and test_point_data['output_expectations']:
        formatted.append("Output Expectations:")
        for exp in test_point_data['output_expectations']:
            formatted.append(f"  - {exp}")
    
    return "\n".join(formatted)

def read_file_content(file_path):
    "Read content from a file."
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""

def create_temp_file(content, prefix="tmp_", suffix=".txt"):
    "Create a temporary file with the given content."
    try:
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
            tmp.write(content)
        return path
    except Exception as e:
        logger.error(f"Error creating temporary file: {e}")
        return None

def find_resource_path(relative_path):
    """
    Find the path to a resource file within the package.
    
    Args:
        relative_path: Path relative to the package root
        
    Returns:
        Absolute path to the resource file, or None if not found
    """
    try:
        # Get the package directory
        import os
        
        # Try to determine which part is the package name and which is the relative path
        parts = relative_path.split('/')
        
        # For standard locations, try direct imports first
        if relative_path.startswith('prompts/'):
            try:
                # Try to treat 'prompts' as a subpackage
                file_name = os.path.basename(relative_path)
                try:
                    # Try to import the prompts module directly
                    prompts_module = import_module('ai_json_generator.prompts')
                    spec_path = os.path.join(os.path.dirname(prompts_module.__file__), file_name)
                    if os.path.exists(spec_path):
                        logger.info(f"Found resource through module import: {spec_path}")
                        return spec_path
                except (ImportError, ModuleNotFoundError):
                    pass
                
                # Try to get it as a resource using importlib.resources
                try:
                    with importlib.resources.path('ai_json_generator.prompts', file_name) as p:
                        resource_path = str(p)
                        if os.path.exists(resource_path):
                            logger.info(f"Found resource through importlib.resources: {resource_path}")
                            return resource_path
                except (ImportError, ModuleNotFoundError, FileNotFoundError):
                    pass
                    
                # Try to get it using pkg_resources
                try:
                    import pkg_resources as old_pkg_resources
                    resource_path = old_pkg_resources.resource_filename('ai_json_generator.prompts', file_name)
                    if os.path.exists(resource_path):
                        logger.info(f"Found resource through pkg_resources: {resource_path}")
                        return resource_path
                except (ImportError, Exception):
                    pass
                    
            except Exception as e:
                logger.warning(f"Error trying to find prompts module: {e}")
                
        elif relative_path.startswith('data_files/'):
            try:
                # Try to treat 'data_files' as a subpackage
                file_name = os.path.basename(relative_path)
                try:
                    # Try to import the data_files module directly
                    data_files_module = import_module('ai_json_generator.data_files')
                    spec_path = os.path.join(os.path.dirname(data_files_module.__file__), file_name)
                    if os.path.exists(spec_path):
                        logger.info(f"Found resource through module import: {spec_path}")
                        return spec_path
                except (ImportError, ModuleNotFoundError):
                    pass
                
                # Try to get it as a resource using importlib.resources
                try:
                    with importlib.resources.path('ai_json_generator.data_files', file_name) as p:
                        resource_path = str(p)
                        if os.path.exists(resource_path):
                            logger.info(f"Found resource through importlib.resources: {resource_path}")
                            return resource_path
                except (ImportError, ModuleNotFoundError, FileNotFoundError):
                    pass
                    
                # Try to get it using pkg_resources
                try:
                    import pkg_resources as old_pkg_resources
                    resource_path = old_pkg_resources.resource_filename('ai_json_generator.data_files', file_name)
                    if os.path.exists(resource_path):
                        logger.info(f"Found resource through pkg_resources: {resource_path}")
                        return resource_path
                except (ImportError, Exception):
                    pass
                    
            except Exception as e:
                logger.warning(f"Error trying to find data_files module: {e}")
        
        # Fall back to looking for absolute paths within the package
        package_path = os.path.abspath(os.path.dirname(__file__))
        
        # Form all possible paths
        search_paths = [
            # Absolute path in the package
            os.path.join(package_path, relative_path),
            # Relative to package root
            os.path.join(package_path, os.path.basename(relative_path)),
            # Special cases for known locations
            os.path.join(package_path, 'prompts', os.path.basename(relative_path)),
            os.path.join(package_path, 'data_files', os.path.basename(relative_path))
        ]
        
        # Check all paths
        for path in search_paths:
            if os.path.exists(path):
                logger.info(f"Found resource at: {path}")
                return path
        
        # If we haven't returned by now, look in parent directories
        # (this is for development mode)
        parent_dir = os.path.dirname(package_path)
        
        # Try parent package
        parent_paths = [
            os.path.join(parent_dir, relative_path),
            os.path.join(parent_dir, 'ai_json_generator', relative_path)
        ]
        
        for path in parent_paths:
            if os.path.exists(path):
                logger.info(f"Found resource in parent directory: {path}")
                return path
        
        # If still not found, let's look at some typical installation paths
        # Get list of all site-packages directories
        site_packages_dirs = site.getsitepackages()
        
        if 'VIRTUAL_ENV' in os.environ:
            venv_path = os.environ['VIRTUAL_ENV']
            site_packages_dirs.extend([
                os.path.join(venv_path, 'lib', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages'),
                os.path.join(venv_path, 'lib64', f'python{sys.version_info.major}.{sys.version_info.minor}', 'site-packages')
            ])
        
        for site_dir in site_packages_dirs:
            site_paths = [
                os.path.join(site_dir, 'ai_json_generator', relative_path)
            ]
            
            for path in site_paths:
                if os.path.exists(path):
                    logger.info(f"Found resource in site-packages: {path}")
                    return path
        
        # Handle development symlinks
        # In development mode, packages might be installed with -e flag
        cwd = os.getcwd()
        dev_paths = [
            os.path.join(cwd, relative_path),
            os.path.join(cwd, 'ai_json_generator', relative_path)
        ]
        
        for path in dev_paths:
            if os.path.exists(path):
                logger.info(f"Found resource in development directory: {path}")
                return path
        
        # Special case for op_testcase.prompt
        if os.path.basename(relative_path) == 'op_testcase.prompt':
            # Look for op_testcase.prompt specifically in various locations
            for site_dir in site_packages_dirs + [package_path, parent_dir, os.getcwd()]:
                special_paths = [
                    os.path.join(site_dir, 'prompts', 'op_testcase.prompt'),
                    os.path.join(site_dir, 'ai_json_generator', 'prompts', 'op_testcase.prompt')
                ]
                
                for path in special_paths:
                    if os.path.exists(path):
                        logger.info(f"Found op_testcase.prompt at: {path}")
                        return path
        
        # Not found anywhere
        logger.error(f"Resource file not found: {relative_path}")
        return None
    except Exception as e:
        logger.error(f"Error finding resource {relative_path}: {str(e)}")
        return None

def run_irjson_convert(json_file: str, output_dir: str) -> Tuple[bool, Optional[str]]:
    """
    Run irjson-convert command to convert JSON to ONNX model.
    
    Args:
        json_file: Path to the JSON file
        output_dir: Output directory for the ONNX model
        
    Returns:
        Tuple[bool, Optional[str]]: A tuple containing a boolean for success
                                     and the path to the output model directory if successful.
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Create log file path in the same directory as the JSON file
        log_file = os.path.join(os.path.dirname(json_file), 'irjson_convert.log')
        
        # Prepare the command
        cmd = f"irjson-convert {json_file} -o {output_dir}"
        
        # To store the actual output directory from the command's stdout
        actual_model_dir = None
        
        # Run the command and capture output
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8'
        )
        
        # Open log file for writing
        with open(log_file, 'w', encoding='utf-8') as f:
            # Process and handle output in real-time
            for output in process.stdout:
                # Write to log file
                f.write(output)
                f.flush()
                # Print to screen
                print(output.strip())
                sys.stdout.flush()
                
                # Look for the output directory line
                if "输出目录:" in output:
                    # Extract the path, which is the part after the colon
                    path_match = output.split("输出目录:", 1)
                    if len(path_match) > 1:
                        actual_model_dir = path_match[1].strip()
                        logger.info(f"Detected model output directory: {actual_model_dir}")

        # Wait for the process to complete and get the return code
        return_code = process.wait()
        
        if return_code == 0:
            logger.info(f"Successfully converted {json_file} to ONNX model")
            logger.info(f"Conversion log saved to {log_file}")
            return True, actual_model_dir
        else:
            logger.error(f"Failed to convert {json_file} to ONNX model (return code: {return_code})")
            logger.info(f"Check {log_file} for details")
            return False, None
            
    except Exception as e:
        logger.error(f"Error running irjson-convert: {str(e)}")
        return False, None

def generate_testcase(operator_string: str, output_dir: str, quiet: bool = False,
                     test_point: Optional[str] = None, graph_pattern: Optional[str] = None,
                     add_req: Optional[str] = None, direct_prompt: Optional[str] = None,
                     direct_request: Optional[str] = None,
                     convert_to_onnx: bool = False, max_retries: int = 1) -> bool:
    "Generate test case for the specified operator(s)."
    # Ensure the base output directory exists first.
    os.makedirs(output_dir, exist_ok=True)

    process_dir = None
    if convert_to_onnx:
        # Use a fixed-name directory for processing.
        process_dir = os.path.join(output_dir, "llm_process")
        # Clean up previous failed runs if it exists
        if os.path.exists(process_dir):
            shutil.rmtree(process_dir)
        os.makedirs(process_dir)
        current_output_dir = process_dir
        logger.info(f"Using process directory for intermediate files: {process_dir}")
    else:
        current_output_dir = output_dir

    try:
        # Import LLMJsonGenerator at the beginning
        from .generate_json import LLMJsonGenerator
        
        # Create the actual output/process directory
        os.makedirs(current_output_dir, exist_ok=True)
        
        # Initialize generator
        generator = LLMJsonGenerator()
        
        # Track the current retry attempt
        current_retry = 0
        last_json_file = None
        last_prompt = None
        last_json_content = None
        last_error_content = None
        
        # Determine base_output_name before the loop
        base_output_name = ""
        if direct_prompt:
            base_output_name = "operator_testcase"
        elif operator_string:
            is_multi_operator = ' ' in operator_string
            if is_multi_operator:
                base_output_name = f"{'_'.join(operator_string.split())}_composite_testcase"
            else:
                base_output_name = f"{operator_string}_testcase"
        else:
            base_output_name = "custom_testcase"

        while current_retry <= max_retries:
            attempt_prefix = f"attempt_{current_retry}_"
            
            # If using direct prompt, we can skip all the template processing
            if direct_prompt:
                logger.info(f"Using direct prompt file: {direct_prompt}")
                
                # Save the original prompt content for potential retry
                if current_retry == 0:
                    with open(direct_prompt, 'r', encoding='utf-8') as f:
                        last_prompt = f.read()
                    # Save initial prompt
                    with open(os.path.join(current_output_dir, f"initial_prompt.txt"), 'w', encoding='utf-8') as f:
                        f.write(last_prompt)

                # If this is a retry attempt, use the retry template
                if current_retry > 0 and last_json_content and last_error_content:
                    # Create retry prompt using retry_testcase.prompt
                    retry_template = find_resource_path(os.path.join('prompts', 'retry_testcase.prompt'))
                    if not retry_template:
                        logger.error("Could not find retry_testcase.prompt template")
                        return False
                    
                    with open(retry_template, 'r', encoding='utf-8') as f:
                        retry_prompt_content = f.read()
                    
                    # Fill in the retry template
                    retry_prompt_content = retry_prompt_content.replace("{prompt内容}", last_prompt if last_prompt else "")
                    retry_prompt_content = retry_prompt_content.replace("{IR_JSON内容}", last_json_content)
                    retry_prompt_content = retry_prompt_content.replace("{报错内容}", last_error_content)
                    
                    # Save the retry prompt to a temporary file
                    temp_prompt_file = os.path.join(current_output_dir, f"retry_prompt.txt")
                    with open(temp_prompt_file, 'w', encoding='utf-8') as f:
                        f.write(retry_prompt_content)
                    
                    direct_prompt = temp_prompt_file
                
                success = generator.generate(
                    "",  # Empty template path since we're using direct prompt
                    {},
                    current_output_dir,
                    base_output_name,
                    "json",
                    max_retries=3,
                    debug=True,
                    show_output=not quiet,
                    direct_prompt_file=direct_prompt
                )
            else:
                # Define paths to data files
                data_dir = 'data_files'
                operators_csv = find_resource_path(os.path.join(data_dir, 'onnx_operators.csv'))
                test_point_path = find_resource_path(os.path.join(data_dir, 'test_point.txt'))
                ir_json_format_path = find_resource_path(os.path.join(data_dir, 'IR_JSON_FORMAT.md'))
                test_points_csv = find_resource_path(os.path.join(data_dir, 'test_points.csv'))
                graph_patterns_csv = find_resource_path(os.path.join(data_dir, 'graph_patterns.csv'))
                
                # Initialize variables
                operator_params = ""
                op_type = "others"
                
                # Only check operators CSV if we have an operator string and not using direct_request only
                if operator_string and not (direct_request and not operator_string):
                    if not operators_csv:
                        logger.error("Could not find operators CSV file")
                        return False
                    
                    operators_list = operator_string.split()
                    
                    # Process each operator to get their parameters
                    all_operator_params = []
                    for op in operators_list:
                        op_params = find_operator_params(op, operators_csv)
                        if not op_params:
                            logger.error(f"Could not find parameters for operator: {op}")
                            return False
                        all_operator_params.append(op_params)
                    
                    # Combine all operator parameters for multi-operator cases
                    if len(operators_list) > 1:
                        combined_params = "\n\n".join([f"算子: {op}\n{params}" for op, params in zip(operators_list, all_operator_params)])
                        operator_params = combined_params
                        op_type = "composite"
                    else:
                        operator_params = all_operator_params[0]
                        # Determine operator type for single operator
                        if "输入:" in operator_params and "输出:" in operator_params:
                            input_lines = [line for line in operator_params.split('\n') if line.strip().startswith("  - ") and "输入:" in operator_params.split('\n')[operator_params.split('\n').index(line)-1]]
                            output_lines = [line for line in operator_params.split('\n') if line.strip().startswith("  - ") and "输出:" in operator_params.split('\n')[operator_params.split('\n').index(line)-1]]
                            
                            if len(input_lines) == 2 and len(output_lines) == 1:
                                op_type = "binary arithmetic"
                            elif len(input_lines) == 1 and len(output_lines) == 1:
                                op_type = "unary"
                
                # Get test point information
                test_point_content = ""
                if direct_request:
                    # Use content from direct-request file
                    logger.info(f"Using direct request file: {direct_request}")
                    with open(direct_request, 'r', encoding='utf-8') as f:
                        test_point_content = f.read()
                elif test_points_csv and test_point:
                    test_points_dict = read_csv_to_dict(test_points_csv)
                    if test_point in test_points_dict:
                        test_point_data = test_points_dict[test_point]
                        test_point_content = f"测试点: {test_point}\n"
                        for key, value in test_point_data.items():
                            if value:  # Only include non-empty values
                                test_point_content += f"{key}: {value}\n"
                        logger.info(f"Using specified test point: {test_point}")
                elif test_point_path:
                    test_point_content = read_file_content(test_point_path)
                if not test_point_content:
                    test_point_content = "测试基本功能，确保算子能正确处理输入并生成预期的输出"
                
                # Get graph pattern information
                graph_pattern_content = ""
                if graph_patterns_csv:
                    graph_patterns_dict = read_csv_to_dict(graph_patterns_csv)
                    if graph_pattern and graph_pattern in graph_patterns_dict:
                        # Use specified graph pattern
                        graph_pattern_data = graph_patterns_dict[graph_pattern]
                        graph_pattern_content = f"构图模式: {graph_pattern}\n"
                        for key, value in graph_pattern_data.items():
                            if value:  # Only include non-empty values
                                graph_pattern_content += f"{key}: {value}\n"
                        logger.info(f"Using specified graph pattern: {graph_pattern}")
                    elif graph_patterns_dict:  # Use default (first) graph pattern if none specified
                        first_key = next(iter(graph_patterns_dict))
                        graph_pattern_data = graph_patterns_dict[first_key]
                        graph_pattern_content = f"构图模式: {first_key}\n"
                        for key, value in graph_pattern_data.items():
                            if value:  # Only include non-empty values
                                graph_pattern_content += f"{key}: {value}\n"
                        logger.info(f"Using default graph pattern: {first_key}")
                
                # Read IR JSON format requirements
                ir_json_format = ""
                if ir_json_format_path:
                    ir_json_format = read_file_content(ir_json_format_path)
                if not ir_json_format:
                    ir_json_format = "IR JSON应包含模型的inputs、outputs和nodes信息，确保算子的连接和属性正确"
                
                additional_requirements = ""
                if add_req:
                    additional_requirements = add_req
                if not additional_requirements:
                    additional_requirements = "无"
                
                # Create replacements
                replacements = {
                    "算子名": operator_string if operator_string else "",
                    "算子参数": operator_params if operator_string else "",
                    "算子类型": op_type,
                    "用例要求": test_point_content,
                    "IR_JSON要求": ir_json_format,
                    "附加要求": additional_requirements
                }
                
                if graph_pattern_content:
                    replacements["构图模式"] = graph_pattern_content
                
                # If this is a retry attempt, use the retry template
                if current_retry > 0 and last_json_content and last_error_content:
                    # Create retry prompt using retry_testcase.prompt
                    retry_template = find_resource_path(os.path.join('prompts', 'retry_testcase.prompt'))
                    if not retry_template:
                        logger.error("Could not find retry_testcase.prompt template")
                        return False
                    
                    with open(retry_template, 'r', encoding='utf-8') as f:
                        retry_prompt_content = f.read()
                    
                    # Fill in the retry template
                    retry_prompt_content = retry_prompt_content.replace("{prompt内容}", last_prompt if last_prompt else "")
                    retry_prompt_content = retry_prompt_content.replace("{IR_JSON内容}", last_json_content)
                    retry_prompt_content = retry_prompt_content.replace("{报错内容}", last_error_content)
                    
                    # Save the retry prompt to a temporary file
                    temp_prompt_file = os.path.join(current_output_dir, f"retry_prompt.txt")
                    with open(temp_prompt_file, 'w', encoding='utf-8') as f:
                        f.write(retry_prompt_content)
                    
                    direct_prompt = temp_prompt_file
                    template_path = ""
                else:
                    # Find template
                    template_path = find_resource_path(os.path.join('prompts', 'op_testcase.prompt'))
                    if not template_path:
                        logger.error("Could not find op_testcase.prompt template")
                        return False
                    
                    logger.info(f"Using template: {template_path}")
                
                if operator_string:
                    logger.info(f"Generating test case for {operator_string}")
                else:
                    logger.info("Generating test case with custom requirements")
                
                # Save the current prompt for potential retry
                if template_path and current_retry == 0:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        current_prompt = f.read()
                    for key, value in replacements.items():
                        current_prompt = current_prompt.replace(f"{{{key}}}", value)
                    last_prompt = current_prompt
                    with open(os.path.join(current_output_dir, f"initial_prompt.txt"), 'w', encoding='utf-8') as f:
                        f.write(last_prompt)

                success = generator.generate(
                    template_path,
                    replacements,
                    current_output_dir,
                    base_output_name,
                    "json",
                    max_retries=3,
                    debug=True,
                    show_output=not quiet,
                    direct_prompt_file=direct_prompt
                )
            
            if success:
                if operator_string:
                    logger.info(f"Successfully generated test case for {operator_string}")
                else:
                    logger.info("Successfully generated test case with custom requirements")

                original_json_path = os.path.join(current_output_dir, f"{base_output_name}.json")
                json_file = original_json_path  # Default in case of error
                case_name = base_output_name

                try:
                    with open(original_json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)

                    case_name = json_data.get("Case_Name", base_output_name)
                    case_name = re.sub(r'[\\/:*?"<>|]', '_', case_name)  # Sanitize for filename
                    
                    new_json_path = os.path.join(current_output_dir, f"{case_name}.json")
                    if original_json_path != new_json_path:
                        if os.path.exists(new_json_path):
                            os.remove(new_json_path)
                        os.rename(original_json_path, new_json_path)
                        logger.info(f"Renamed output file to: {new_json_path}")
                    json_file = new_json_path

                except (IOError, json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Failed to process generated JSON for renaming: {e}. Proceeding with original filename.")
                
                # If convert_to_onnx is True, run irjson-convert
                if convert_to_onnx:
                    # Save the current JSON content for potential retry
                    with open(json_file, 'r', encoding='utf-8') as f:
                        last_json_content = f.read()
                    
                    conversion_success, model_path = run_irjson_convert(json_file, current_output_dir)
                    if conversion_success:
                        # Find the generated model directory
                        try:
                            # The actual model path is returned by run_irjson_convert
                            src_path = model_path
                            
                            if src_path and os.path.isdir(src_path):
                                model_dir_name = os.path.basename(src_path)
                                dest_path = os.path.join(output_dir, model_dir_name)
                                
                                if os.path.exists(dest_path):
                                    shutil.rmtree(dest_path)
                                    logger.warning(f"Removed existing directory at destination: {dest_path}")

                                shutil.move(src_path, dest_path)
                                logger.info(f"Successfully moved model to {dest_path}")
                                logger.info(f"Process files are kept in {process_dir}")
                            elif src_path:
                                logger.error(f"The detected model path is not a directory: '{src_path}'.")
                                return False
                            else:
                                logger.error(f"Could not detect the converted model directory from converter output.")
                                return False
                        except Exception as e:
                            logger.error(f"Error moving converted model: {e}")
                            return False
                        
                        return True
                    else:
                        # This attempt failed, so we rename all related files with the attempt prefix.
                        
                        # Save error log content for retry
                        log_file = os.path.join(current_output_dir, 'irjson_convert.log')
                        if os.path.exists(log_file):
                            with open(log_file, 'r', encoding='utf-8') as f:
                                last_error_content = f.read()
                            # Rename the log file for this attempt
                            renamed_log_path = os.path.join(current_output_dir, f"{attempt_prefix}irjson_convert.log")
                            os.rename(log_file, renamed_log_path)

                        # Rename the failed JSON file
                        if os.path.exists(json_file):
                            renamed_json_path = os.path.join(current_output_dir, f"{attempt_prefix}{os.path.basename(json_file)}")
                            os.rename(json_file, renamed_json_path)
                            logger.warning(f"Conversion failed. Renamed failed JSON to {renamed_json_path}")

                        # Rename the response file
                        response_file = os.path.join(current_output_dir, f"{base_output_name}_response.txt")
                        if os.path.exists(response_file):
                            renamed_response_path = os.path.join(current_output_dir, f"{attempt_prefix}{base_output_name}_response.txt")
                            os.rename(response_file, renamed_response_path)

                        # Rename the prompt file for this attempt
                        prompt_file_to_rename = ""
                        if current_retry == 0:
                            prompt_file_to_rename = os.path.join(current_output_dir, "initial_prompt.txt")
                        else:
                            prompt_file_to_rename = os.path.join(current_output_dir, "retry_prompt.txt")
                        
                        if os.path.exists(prompt_file_to_rename):
                             os.rename(prompt_file_to_rename, os.path.join(current_output_dir, f"{attempt_prefix}{os.path.basename(prompt_file_to_rename)}"))

                        # Rename any partially created ONNX folder
                        partial_onnx_dir = os.path.join(current_output_dir, case_name)
                        if os.path.isdir(partial_onnx_dir):
                            renamed_onnx_dir = os.path.join(current_output_dir, f"{attempt_prefix}{case_name}_failed_onnx")
                            os.rename(partial_onnx_dir, renamed_onnx_dir)

                        if current_retry < max_retries:
                            logger.warning(f"ONNX conversion failed, attempting retry {current_retry + 1}/{max_retries}")
                            current_retry += 1
                            continue
                        else:
                            logger.error(f"ONNX conversion failed after all retries. Process files are kept in {process_dir}")
                            return False
                else:
                    return True
            else:
                if current_retry < max_retries:
                    logger.warning(f"JSON generation failed, attempting retry {current_retry + 1}/{max_retries}")
                    current_retry += 1
                    continue
                else:
                    logger.error("JSON generation failed after all retries")
                    if process_dir:
                         logger.info(f"Process files are kept in {process_dir}")
                    return False
                
    except Exception as e:
        logger.error(f"Error generating test case: {str(e)}")
        if process_dir:
            logger.info(f"Process files are kept in {process_dir}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate test cases for ONNX operators')
    parser.add_argument('operator', nargs='*', help='Operator name(s). Multiple operators can be specified separated by spaces.')
    
    # Modify output directory arguments
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument('-o', '--output', dest='output_dir', help='Directory to save the output files')
    output_group.add_argument('--output-dir', dest='output_dir', help='Directory to save the output files (deprecated, use -o or --output instead)')
    
    parser.add_argument('--quiet', action='store_true', help='Disable displaying LLM output to screen')
    parser.add_argument('--test-point', help='Specify a test point key from test_points.csv')
    parser.add_argument('--graph-pattern', help='Specify a graph pattern key from graph_patterns.csv')
    parser.add_argument('--add-req', help='Add additional requirements txt')
    parser.add_argument('--direct-prompt', help='Path to a prompt file to use directly instead of using the template system')
    parser.add_argument('--direct-request', help='Path to a txt file containing test case requirements to replace the default test point content')
    parser.add_argument('--convert-to-onnx', action='store_true', help='Convert generated JSON to ONNX model using irjson-convert')
    parser.add_argument('--max-retries', type=int, default=1, help='Maximum number of retry attempts for failed ONNX conversion')

    args = parser.parse_args()
    
    # Set default output directory if not specified
    if not args.output_dir:
        args.output_dir = 'outputs'
    
    # Check if operators are provided when not using direct prompt or direct request
    if not args.operator and not args.direct_prompt and not args.direct_request:
        logger.error("Please specify at least one operator name, provide a direct prompt file, or provide a direct request file")
        return 1
    
    # Determine the operator string
    operator_string = ""
    if args.operator:
        # In case of multiple arguments (e.g. MatMul Add Slice), join them
        # If a single string with spaces was passed (e.g. "MatMul Add Slice"), use as is
        if len(args.operator) == 1:
            operator_string = args.operator[0]
        else:
            operator_string = ' '.join(args.operator)
        logger.info(f"Processing operators: {operator_string}")
    elif args.direct_request:
        logger.info("Using direct request without operator specification")
    
    success = generate_testcase(
        operator_string, 
        args.output_dir, 
        args.quiet,
        test_point=args.test_point,
        graph_pattern=args.graph_pattern,
        add_req=args.add_req,
        direct_prompt=args.direct_prompt,
        direct_request=args.direct_request,
        convert_to_onnx=args.convert_to_onnx,
        max_retries=args.max_retries
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())