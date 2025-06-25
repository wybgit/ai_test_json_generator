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
from typing import Dict, Any, Optional
from colorama import init, Fore, Back, Style

# Initialize colorama for colored terminal output
init(autoreset=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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
        
        # Add enable_thinking if it exists in config
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
                
                # Initialize variables to store thinking process and final response
                thinking_process = []
                final_response = []
                output_line = ""  # Current line content
                is_receiving_content = False
                
                # Process the streaming response
                for line in response.iter_lines():
                    if line:
                        # Remove 'data: ' prefix and parse JSON
                        line_text = line.decode('utf-8').replace('data: ', '')
                        try:
                            data = json.loads(line_text)
                        except json.JSONDecodeError:
                            continue
                        
                        # Extract reasoning/thinking content
                        reasoning_content = data.get('choices', [{}])[0].get('delta', {}).get('reasoning_content')
                        if reasoning_content and not is_receiving_content:
                            thinking_process.append(reasoning_content)
                            # Update thinking display in a single line, replace newlines with spaces
                            output_line = f"{Fore.BLACK}{Back.WHITE}[思考中] {reasoning_content.replace(chr(10), ' ')}{Style.RESET_ALL}"
                            if show_output:
                                sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear line with sufficient spaces
                                sys.stdout.write(output_line[:100])  # Limit line length for display
                                sys.stdout.flush()
                        
                        # Extract response content
                        content = data.get('choices', [{}])[0].get('delta', {}).get('content')
                        if content:
                            is_receiving_content = True
                            final_response.append(content)
                            # Update response display in a single line, replace newlines with spaces
                            output_line = f"{Fore.WHITE}{Back.GREEN}[生成] {''.join(final_response[-100:]).replace(chr(10), ' ')}"
                            if show_output:
                                sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear line with sufficient spaces
                                sys.stdout.write(output_line[:100])  # Limit line length for display
                                sys.stdout.flush()
                        
                        # Check if response is finished
                        finish_reason = data.get('choices', [{}])[0].get('finish_reason')
                        if finish_reason == 'stop':
                            break
                
                # Add newline for better display
                if show_output:
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                
                # Combine thinking process and final response
                thinking_content = ''.join(thinking_process)
                response_content = ''.join(final_response)
                
                logger.info(f"Received complete response ({len(response_content)} chars)")
                if thinking_content:
                    logger.info(f"Captured thinking content ({len(thinking_content)} chars)")
                    full_content = f"THINKING:\n{thinking_content}\n\nRESPONSE:\n{response_content}"
                else:
                    full_content = response_content
                
                return full_content
                
        except Exception as e:
            logger.error(f"Error querying LLM: {e}")
            if response and hasattr(response, 'text'):
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
        fixed_json = re.sub(r':\s*([a-zA-Z0-9_]+)([,\s}])', r': "\1"\2', fixed_json)
        
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
                        retry_prompt = f"""{prompt}

Your previous response contained invalid JSON. Please fix the following errors and try again:

{error}

Please make sure to provide valid JSON.
"""
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

def main():
    """Command-line interface for the JSON generator."""
    parser = argparse.ArgumentParser(description='Generate JSON files using LLM based on templates')
    
    # Add new argument group for input mode
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--template', help='Path to the prompt template file')
    input_group.add_argument('--direct-prompt', help='Path to a prompt file to use directly')
    
    parser.add_argument('--replacements', help='Comma-separated key=value pairs to replace in the template. Values can be file paths.')
    parser.add_argument('--output-folder', default='output', help='Output folder for generated files')
    parser.add_argument('--output-name', default='output', help='Base name for the output file')
    parser.add_argument('--output-ext', default='json', help='File extension for the output')
    parser.add_argument('--config', default='config.json', help='Path to LLM config file. Can be absolute path, relative path, or just filename to use package default.')
    parser.add_argument('--max-retries', type=int, default=1, help='Maximum number of retry attempts')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode to save prompts and raw responses')
    parser.add_argument('--quiet', action='store_true', help='Disable displaying LLM output to screen')
    
    args = parser.parse_args()
    
    # Parse replacements only if template is used
    replacements = {}
    if args.template and args.replacements:
        replacements = parse_key_value_pairs(args.replacements)
    elif args.replacements and args.direct_prompt:
        logger.warning("Replacements are ignored when using direct prompt file")
    
    # Create the generator
    generator = LLMJsonGenerator(args.config)
    
    # Generate the JSON
    success = generator.generate(
        args.template if args.template else "",  # Empty string if using direct prompt
        replacements,
        args.output_folder,
        args.output_name,
        args.output_ext,
        args.max_retries,
        args.debug,
        not args.quiet,  # Invert the quiet flag to get show_output
        args.direct_prompt
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 