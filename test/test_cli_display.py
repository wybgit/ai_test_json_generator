#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the new CLI display functionality.
"""

import time
from ai_json_generator.cli_display import CLIDisplay

def test_basic_display():
    """Test basic display functionality."""
    print("Testing normal mode...")
    display = CLIDisplay(debug=False, quiet=False)
    
    display.print_header("🤖 AI JSON Test Case Generator", "Testing normal display mode")
    
    display.info("This is an info message")
    display.success("This is a success message")
    display.warning("This is a warning message")
    display.error("This is an error message")
    
    # Test config info
    config = {
        'model': 'gpt-4',
        'api_url': 'https://api.example.com/v1/chat/completions',
        'max_tokens': 4096,
        'temperature': 0.7
    }
    display.print_config_info(config)
    
    # Test generation start
    display.print_generation_start("MatMul", "outputs")
    
    time.sleep(1)

def test_debug_display():
    """Test debug display functionality."""
    print("\nTesting debug mode...")
    display = CLIDisplay(debug=True, quiet=False)
    
    display.print_header("🔍 Debug Mode Test", "Testing debug display mode")
    
    display.info("This is an info message in debug mode")
    display.debug("This is a debug message")
    display.success("This is a success message in debug mode")
    display.warning("This is a warning message in debug mode")
    display.error("This is an error message in debug mode")
    
    time.sleep(1)

def test_quiet_display():
    """Test quiet display functionality."""
    print("\nTesting quiet mode...")
    display = CLIDisplay(debug=False, quiet=True)
    
    display.info("This info message should not appear")
    display.success("This success message should not appear")
    display.warning("This warning message should appear")
    display.error("This error message should appear")
    
    time.sleep(1)

def test_llm_progress():
    """Test LLM progress indicator."""
    print("\nTesting LLM progress...")
    display = CLIDisplay(debug=False, quiet=False)
    
    with display.create_llm_progress("Initializing LLM connection...") as progress:
        time.sleep(1)
        progress.update_connecting()
        time.sleep(1)
        progress.update_thinking("Let me think about how to generate this test case for MatMul operator...")
        time.sleep(2)
        progress.update_thinking("I need to consider the input shapes and data types for this operation...")
        time.sleep(2)
        progress.update_generating()
        time.sleep(2)
        progress.update_complete()

def test_file_operations():
    """Test file operation messages."""
    print("\nTesting file operations...")
    display = CLIDisplay(debug=False, quiet=False)
    
    display.print_file_saved("/tmp/test.json", "JSON file")
    display.print_file_saved("/tmp/test.onnx", "ONNX model")
    
    display.print_summary(True, "Operation completed successfully")
    time.sleep(1)
    display.print_summary(False, "Operation failed due to validation error")

if __name__ == "__main__":
    test_basic_display()
    test_debug_display()
    test_quiet_display()
    test_llm_progress()
    test_file_operations()
    
    print("\n✅ All CLI display tests completed!")
