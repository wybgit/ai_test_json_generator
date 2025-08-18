#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import logging
import time
import requests
import re
from typing import Dict, Any, Optional, List, Tuple
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
import csv
import subprocess
import tempfile
import shutil
import site
import importlib
from importlib import import_module
import importlib.resources as pkg_resources

# Initialize Rich Console
console = Console()

# Set up logging with RichHandler
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger('json_generator')

class LLMJsonGenerator:
    def __init__(self, config_path="config.json"):
        self.config = self._load_config(config_path)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_token']}"
        }
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load LLM configuration from JSON file."""
        # First check if environment variable is set
        env_config_path = os.environ.get('AI_JSON_GENERATOR_CONFIG')
        if env_config_path and os.path.isfile(env_config_path):
            config_file = env_config_path
            logger.info(f"Using config file from environment variable: {config_file}")
        # Check if config file exists with absolute path
        elif os.path.isabs(config_path) and os.path.isfile(config_path):
            config_file = config_path
            logger.info(f"Using config file from absolute path: {config_file}")
        # Check relative to current directory
        elif os.path.isfile(config_path):
            config_file = config_path
            logger.info(f"Using config file from current directory: {config_file}")
        # Check in package directory
        else:
            package_dir = os.path.dirname(os.path.abspath(__file__))
            # Try config in package directory
            package_config = os.path.join(package_dir, config_path)
            if os.path.isfile(package_config):
                config_file = package_config
                logger.info(f"Using config file from package directory: {config_file}")
            else:
                # Try config in home directory
                home_dir = os.path.expanduser("~")
                home_config = os.path.join(home_dir, '.ai_json_generator', config_path)
                if os.path.isfile(home_config):
                    config_file = home_config
                    logger.info(f"Using config file from home directory: {config_file}")
                else:
                    # Try config in package data
                    try:
                        import importlib.resources as pkg_resources
                        with pkg_resources.path('ai_json_generator', config_path) as p:
                            if os.path.isfile(p):
                                config_file = str(p)
                                logger.info(f"Using config file from package data: {config_file}")
                            else:
                                raise FileNotFoundError(f"Config file not found: {config_path}")
                    except ImportError:
                        # Fallback for Python < 3.7
                        package_data_config = os.path.join(package_dir, config_path)
                        if os.path.isfile(package_data_config):
                            config_file = package_data_config
                            logger.info(f"Using config file from package data: {config_file}")
                        else:
                            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
            raise
    
    def _read_template(self, template_path: str) -> str:
        """Read prompt template from file."""
        # First try to find as absolute path or relative to current directory
        if os.path.isabs(template_path) and os.path.isfile(template_path):
            template_file = template_path
        elif os.path.isfile(template_path):
            template_file = template_path
        else:
            # Try to find in package directory
            package_dir = os.path.dirname(os.path.abspath(__file__))
            template_file = os.path.join(package_dir, '..', template_path)
            if not os.path.isfile(template_file):
                # Check in prompts directory within package
                template_file = os.path.join(package_dir, '..', 'prompts', os.path.basename(template_path))
                if not os.path.isfile(template_file):
                    logger.error(f"Template file not found: {template_path}")
                    raise FileNotFoundError(f"Template file not found: {template_path}")
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read template from {template_file}: {e}")
            raise
    
    def _process_replacements(self, replacements: Dict[str, str]) -> Dict[str, str]:
        """Process replacements and load file contents if value is a file path."""
        processed_replacements = {}
        for key, value in replacements.items():
            # Check if value is a file path
            if os.path.isfile(value):
                logger.info(f"Treating replacement value for '{key}' as a file path: {value}")
                try:
                    with open(value, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    processed_replacements[key] = file_content
                    logger.info(f"Loaded {len(file_content)} characters from file for '{key}'")
                except Exception as e:
                    logger.error(f"Failed to read file for replacement '{key}': {e}")
                    # Fall back to using the path as the value
                    processed_replacements[key] = value
            else:
                processed_replacements[key] = value
        
        return processed_replacements
    
    def _fill_template(self, template: str, replacements: Dict[str, str]) -> str:
        """Fill the template with provided replacements."""
        filled_template = template
        processed_replacements = self._process_replacements(replacements)
        
        for key, value in processed_replacements.items():
            placeholder = f"{{{key}}}"
            filled_template = filled_template.replace(placeholder, value)
            
        return filled_template
    
    def query_llm(self, prompt: str, show_output: bool = True) -> str:
        """Query the LLM with the given prompt using streaming and displaying thinking process."""
        payload = {
            "model": self.config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"],
            "top_p": self.config["top_p"],
            "stream": True,
            "thinking_budget": self.config.get("thinking_budget", 4096),
            "min_p": self.config.get("min_p", 0.05),
            "top_k": self.config.get("top_k", 50),
            "frequency_penalty": self.config.get("frequency_penalty", 0.5),
            "n": 1,
            "stop": []
        }
        
        if "enable_thinking" in self.config:
            payload["enable_thinking"] = self.config["enable_thinking"]
        
        try:
            logger.info("Sending request to LLM API...")
            with requests.post(
                self.config["api_url"],
                headers=self.headers,
                json=payload,
                stream=True
            ) as response:
                response.raise_for_status()
                
                thinking_process = []
                final_response = []
                is_receiving_content = False

                if show_output:
                    # Assuming Progress, SpinnerColumn, TextColumn, console are imported
                    # from rich.progress, rich.spinner, rich.text, and rich.console respectively.
                    # Also assuming 'console' is an initialized Console object.
                    from rich.progress import Progress, SpinnerColumn, TextColumn
                    from rich.console import Console
                    console = Console()

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                        transient=True
                    ) as progress:
                        task = progress.add_task("[yellow]Connecting...", total=None)
                        
                        for line in response.iter_lines():
                            if line:
                                line_text = line.decode('utf-8').replace('data: ', '')
                                try:
                                    data = json.loads(line_text)
                                except json.JSONDecodeError:
                                    continue
                                
                                reasoning_content = data.get('choices', [{}])[0].get('delta', {}).get('reasoning_content')
                                if reasoning_content and not is_receiving_content:
                                    thinking_process.append(reasoning_content)
                                    display_text = reasoning_content.replace('\n', ' ').strip()
                                    progress.update(task, description=f"[bold blue][思考中] {display_text}")

                                content = data.get('choices', [{}])[0].get('delta', {}).get('content')
                                if content:
                                    if not is_receiving_content:
                                        is_receiving_content = True
                                        progress.update(task, description="[bold green][生成中]")
                                    final_response.append(content)

                                if data.get('choices', [{}])[0].get('finish_reason') == 'stop':
                                    progress.update(task, description="[bold green]Done!")
                                    break
                else:
                    for line in response.iter_lines():
                        if line:
                            line_text = line.decode('utf-8').replace('data: ', '')
                            try:
                                data = json.loads(line_text)
                            except json.JSONDecodeError:
                                continue
                            reasoning_content = data.get('choices', [{}])[0].get('delta', {}).get('reasoning_content')
                            if reasoning_content:
                                thinking_process.append(reasoning_content)
                            content = data.get('choices', [{}])[0].get('delta', {}).get('content')
                            if content:
                                final_response.append(content)
                            if data.get('choices', [{}])[0].get('finish_reason') == 'stop':
                                break
                
                thinking_content = ''.join(thinking_process)
                response_content = ''.join(final_response)
                
                logger.info(f"Received complete response ({len(response_content)} chars)")
                if thinking_content:
                    logger.info(f"Captured thinking content ({len(thinking_content)} chars)")
                    return f"THINKING:\n{thinking_content}\n\nRESPONSE:\n{response_content}"
                else:
                    return response_content
                
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                logger.error(f"Response: {response.text}")
            raise
    
    def extract_json_content(self, response: str) -> Optional[str]:
        """Extract JSON content from the LLM response."""
        try:
            # First check if response contains thinking and actual response
            if "THINKING:\n" in response and "\n\nRESPONSE:\n" in response:
                # Focus on extracting from the RESPONSE section
                parts = response.split("\n\nRESPONSE:\n", 1)
                if len(parts) > 1:
                    response_part = parts[1]
                else:
                    response_part = response
            else:
                response_part = response
            
            # For the op_testcase.prompt, the JSON will be between "用例IR JSON如下" and "JSON输出完毕"
            start_marker = "用例IR JSON如下"
            end_marker = "JSON输出完毕"
            
            # Clean up any whitespace or newlines around these markers
            json_content = ""
            
            # First try with markers
            start_index = response_part.find(start_marker)
            end_index = response_part.find(end_marker)
            
            if start_index != -1 and end_index != -1:
                # Extract JSON content between the markers
                json_content = response_part[start_index + len(start_marker):end_index].strip()
                logger.info(f"Extracted JSON content with markers, found content of length: {len(json_content)}")
            else:
                logger.warning(f"Could not find JSON markers in response. Start marker: '{start_marker}' found: {start_index != -1}, End marker: '{end_marker}' found: {end_index != -1}")
                # If we can't find the markers, use the entire response part
                json_content = response_part
                logger.info(f"Using full response content of length: {len(json_content)}")
            
            # Extract any JSON-like content wrapped in code blocks or braces
            result = self._extract_json_from_text(json_content)
            
            # Try to fix malformed JSON as a last resort
            try:
                json.loads(result)
                return result
            except json.JSONDecodeError:
                fixed_result = self._fix_malformed_json(result)
                logger.info(f"Attempted to fix malformed JSON, result length: {len(fixed_result)}")
                return fixed_result
            
        except Exception as e:
            logger.error(f"Error extracting JSON content: {e}")
            return None
    
    def _extract_code_blocks(self, text: str) -> list:
        """Extract code blocks from markdown text."""
        code_blocks = []
        
        # Look for triple backtick code blocks - various formats
        # Handle different variations: ```json, ``` json, ```
        start_patterns = ["```json", "``` json", "```"]
        end_pattern = "```"
        
        for start_pattern in start_patterns:
            start_idx = 0
            while True:
                # Find the start of the code block
                start_idx = text.find(start_pattern, start_idx)
                if start_idx == -1:
                    break
                
                # Find the end of the code block
                end_idx = text.find(end_pattern, start_idx + len(start_pattern))
                if end_idx == -1:
                    break
                
                # Extract the code block content, excluding the markers
                code_block = text[start_idx + len(start_pattern):end_idx].strip()
                
                # Only add non-empty code blocks
                if code_block:
                    code_blocks.append(code_block)
                
                # Move past this code block
                start_idx = end_idx + len(end_pattern)
        
        return code_blocks
    
    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text. Tries various methods to find valid JSON."""
        # First try to extract from code blocks
        code_blocks = self._extract_code_blocks(text)
        if code_blocks:
            logger.info(f"Found {len(code_blocks)} code blocks")
            # Try each code block to see if it's valid JSON
            for block in code_blocks:
                try:
                    # Test if it's valid JSON
                    json.loads(block)
                    logger.info("Found valid JSON in code block")
                    return block
                except json.JSONDecodeError:
                    # Try to fix common issues with JSON
                    fixed_block = self._fix_malformed_json(block)
                    try:
                        # Test if the fixed block is valid JSON
                        json.loads(fixed_block)
                        logger.info("Found valid JSON after fixing malformed JSON")
                        return fixed_block
                    except json.JSONDecodeError:
                        continue
        
        # If no valid code blocks, try to find JSON directly
        try:
            # Look for {...} pattern
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                json_str = text[start_idx:end_idx+1]
                # Test if it's valid JSON
                try:
                    json.loads(json_str)
                    logger.info("Found valid JSON with brace matching")
                    return json_str
                except json.JSONDecodeError:
                    # Try to fix common issues with JSON
                    fixed_json = self._fix_malformed_json(json_str)
                    try:
                        # Test if the fixed JSON is valid
                        json.loads(fixed_json)
                        logger.info("Found valid JSON after fixing malformed JSON with brace matching")
                        return fixed_json
                    except json.JSONDecodeError:
                        pass
        except json.JSONDecodeError:
            pass
        
        # Return the entire text as a last resort
        return text
    
    def _fix_malformed_json(self, json_str: str) -> str:
        """
        Try to fix common issues with malformed JSON. 
        
        Args:
            json_str: Potentially malformed JSON string
            
        Returns:
            Fixed JSON string
        """
        # Remove any leading/trailing non-JSON characters (like Chinese colons)
        json_str = json_str.strip()
        
        # Handle the case where the JSON is preceded by Chinese colon or other characters
        if not json_str.startswith('{'):
            start_idx = json_str.find('{')
            if start_idx != -1:
                json_str = json_str[start_idx:]
        
        # Handle the case where there's incomplete JSON at the end
        if not json_str.endswith('}'):
            end_idx = json_str.rfind('}')
            if end_idx != -1:
                json_str = json_str[:end_idx+1]
        
        # Fix missing quotes around keys and string values
        lines = json_str.split('\n')
        fixed_lines = []
        
        in_string = False  # Track if we're inside a quoted string
        
        for line in lines:
            # Skip processing if we're confident this is part of a code block delimiter
            if line.strip() in ['```', '```json', '``` json']:
                continue
            
            # Process line to fix common JSON issues
            line = line.rstrip()
            
            # Fix unquoted keys at the beginning of lines
            # Pattern: whitespace + word + whitespace + colon
            line = re.sub(r'(\s*)([a-zA-Z0-9_]+)(\s*):(\s*)', r'\1"\2"\3:\4', line)
            
            # Fix string values without quotes
            # Pattern: colon + whitespace + word + optional comma at end of line
            line = re.sub(r':(\s*)([a-zA-Z0-9_]+)(\s*)(,?)(\s*)$', r': "\2"\3\4\5', line)
            
            # Fix missing quotes in arrays
            # Special case for unquoted array elements at the beginning
            line = re.sub(r'\[(\s*)([a-zA-Z0-9_]+)(\s*)(,?)(\s*)', r'[\1"\2"\3\4\5', line)
            # Special case for unquoted array elements at the end
            line = re.sub(r'(\s*)([a-zA-Z0-9_]+)(\s*)(,?)(\s*)\]', r'\1"\2"\3\4\5]', line)
            
            fixed_lines.append(line)
        
        fixed_json = '\n'.join(fixed_lines)
        
        # One final check - if we have any keys or values without quotes, try to fix them
        fixed_json = re.sub(r':\s*([a-zA-Z0-9_]+)([,\]}])', r': "\1"\2', fixed_json)
        
        return fixed_json
    
    def validate_json(self, json_str: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate the JSON string and return the parsed object or error message.
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            Tuple of (parsed_json, error_message)
            If JSON is valid, parsed_json will be the parsed object and error_message will be None
            If JSON is invalid, parsed_json will be None and error_message will contain the error details
        """
        if not json_str:
            return None, "Empty JSON string"
            
        try:
            # Try to parse the JSON
            parsed_json = json.loads(json_str)
            return parsed_json, None
        except json.JSONDecodeError as e:
            # Get the error details
            error_message = str(e)
            
            # Extract the position where the error occurred
            error_line = e.lineno
            error_column = e.colno
            error_position = e.pos
            
            # Get the line with the error and its context
            lines = json_str.split('\n')
            error_context = []
            
            # Add a few lines before and after the error
            start_line = max(0, error_line - 3)
            end_line = min(len(lines), error_line + 3)
            
            for i in range(start_line, end_line):
                line_num = i + 1
                line = lines[i] if i < len(lines) else ""
                
                # Highlight the error line
                if line_num == error_line:
                    error_context.append(f"LINE {line_num} (ERROR): {line}")
                    # Add an indicator pointing to the error column
                    indicator = ' ' * (error_column + 11) + '^'
                    error_context.append(indicator)
                else:
                    error_context.append(f"LINE {line_num}: {line}")
            
            # Build detailed error message
            detailed_error = f"JSON Validation Error: {error_message}\n"
            detailed_error += f"Error at position {error_position}, line {error_line}, column {error_column}\n"
            detailed_error += "Context:\n" + "\n".join(error_context)
            
            return None, detailed_error
    
    def generate(self, template_path: str, replacements: Dict[str, str], 
                 output_folder: str, output_filename: str, output_ext: str, 
                 max_retries: int = 1, debug: bool = False, show_output: bool = True,
                 direct_prompt_file: Optional[str] = None) -> bool:
        """
        Generate a JSON file using an LLM based on the template and replacements.
        
        Args:
            template_path: Path to the template file
            replacements: Dictionary of key-value pairs to replace in the template
            output_folder: Folder to save the output file
            output_filename: Base name for the output file
            output_ext: File extension for the output
            max_retries: Maximum number of retry attempts
            debug: Whether to save debug information
            show_output: Whether to display LLM output to screen
            direct_prompt_file: Optional path to a prompt file to use directly instead of template and replacements
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)
            
            # If direct prompt file is provided, use it instead of template and replacements
            if direct_prompt_file:
                try:
                    with open(direct_prompt_file, 'r', encoding='utf-8') as f:
                        prompt = f.read()
                    logger.info(f"Using direct prompt from file: {direct_prompt_file}")
                except Exception as e:
                    logger.error(f"Error reading direct prompt file: {e}")
                    return False
            else:
                # Read template
                template = self._read_template(template_path)
                logger.info(f"Loaded template from {template_path} ({len(template)} chars)")
                
                # Fill template with replacements
                prompt = self._fill_template(template, replacements)
                logger.info(f"Filled template with {len(replacements)} replacements")
            
            if debug:
                prompt_file = os.path.join(output_folder, f"{output_filename}.prompt.txt")
                with open(prompt_file, 'w', encoding='utf-8') as f:
                    f.write(prompt)
                logger.info(f"Saved prompt to {prompt_file}")
            
            # Attempt to generate JSON with retries
            for attempt in range(max_retries):
                logger.info(f"Attempt {attempt + 1}/{max_retries}")
                
                # Query LLM
                response = self.query_llm(prompt, show_output)
                
                if debug:
                    response_file = os.path.join(output_folder, f"{output_filename}.attempt{attempt+1}.response.txt")
                    with open(response_file, 'w', encoding='utf-8') as f:
                        f.write(response)
                    logger.info(f"Saved response to {response_file}")
                
                # Extract JSON content
                json_content = self.extract_json_content(response)
                
                # Validate JSON
                parsed_json, error = self.validate_json(json_content)
                
                if parsed_json:
                    # JSON is valid, save it
                    output_file = os.path.join(output_folder, f"{output_filename}.{output_ext}")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                    logger.info(f"Generated valid JSON file: {output_file}")
                    return True
                else:
                    # JSON is invalid, try again
                    logger.warning(f"Invalid JSON on attempt {attempt + 1}: {error}")
                    
                    if attempt < max_retries - 1:
                        # Prepare retry prompt
                        retry_prompt = f"""{prompt}\n\nYour previous response contained invalid JSON. Please fix the following errors and try again:\n\n{error}\n\nPlease make sure to provide valid JSON."""
                        prompt = retry_prompt
                        
                        if debug:
                            retry_file = os.path.join(output_folder, f"{output_filename}.retry{attempt+1}.prompt.txt")
                            with open(retry_file, 'w', encoding='utf-8') as f:
                                f.write(retry_prompt)
            
            # All attempts failed
            logger.error(f"Failed to generate valid JSON after {max_retries} attempts")
            
            # Save the last error response
            error_file = os.path.join(output_folder, f"{output_filename}.{output_ext}.error")
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
            logger.info(f"Saved invalid JSON to {error_file}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error generating JSON: {e}")
            return False

def parse_key_value_pairs(pair_str: str) -> Dict[str, str]:
    """Parse a comma-separated string of key=value pairs into a dictionary."""
    if not pair_str:
        return {}
        
    pairs = {}
    for item in pair_str.split(','):
        if '=' in item:
            key, value = item.split('=', 1)
            pairs[key.strip()] = value.strip()
    
    return pairs

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
    """Read content from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""

def create_temp_file(content, prefix="tmp_", suffix=".txt"):
    """Create a temporary file with the given content."""
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
                console.print(output.strip())
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
                     convert_to_onnx: bool = False, max_retries: int = 1, debug: bool = False) -> bool:
    """Generate test case for the specified operator(s)."""
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
                    debug=debug,
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
                    debug=debug,
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
    """Command-line interface for the JSON generator."""
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
    parser.add_argument('--debug', action='store_true', help='Enable debug mode, saving intermediate files.')

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
        max_retries=args.max_retries,
        debug=args.debug
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
