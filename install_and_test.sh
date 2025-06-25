#!/bin/bash

# Exit on error
set -e

echo "Installing AI JSON Generator package..."
pip install -e .

echo "Testing package installation..."

# Check if the commands are available
which ai-json-generate
which ai-json-operator

# Create a test config directory and copy config
echo "Setting up test configuration..."
mkdir -p test_config
if [ -f "config.json" ]; then
    cp config.json test_config/test_config.json
elif [ -f "ai_json_generator/config.json" ]; then
    cp ai_json_generator/config.json test_config/test_config.json
else
    echo '{"api_token":"test_token","api_url":"https://api.example.com/v1/chat/completions","model":"TestModel","max_tokens":2048,"temperature":0.7,"top_p":0.7}' > test_config/test_config.json
    echo "Created dummy test config"
fi

# Test with environment variable
echo "Testing environment variable configuration..."
export AI_JSON_GENERATOR_CONFIG="$(pwd)/test_config/test_config.json"
echo "Set AI_JSON_GENERATOR_CONFIG=$AI_JSON_GENERATOR_CONFIG"

echo "Running a simple test..."
mkdir -p test_output

# Create a sample test if source files exist
if [ -d "prompts" ] && [ -f "prompts/op_testcase.prompt" ]; then
    TEMPLATE_PATH="prompts/op_testcase.prompt"
elif [ -d "ai_json_generator/prompts" ] && [ -f "ai_json_generator/prompts/op_testcase.prompt" ]; then
    TEMPLATE_PATH="ai_json_generator/prompts/op_testcase.prompt"
else
    echo "Skipping test as op_testcase.prompt file not found."
    echo "Installation complete!"
    exit 0
fi

echo "Running test with template: $TEMPLATE_PATH"
ai-json-generate \
  --template "$TEMPLATE_PATH" \
  --replacements "算子名=Add,算子参数=inputs: [A, B], outputs: [C], attributes: {},算子类型=binary arithmetic,用例要求=测试基本的Add算子，输入两个相同shape的tensor，输出一个tensor,IR_JSON要求=IR模型描述应包含模型的input、output、node等信息" \
  --output-folder test_output \
  --output-name add_basic \
  --debug

if [ -f "test_output/add_basic.json" ]; then
    echo "Test successful! Generated test_output/add_basic.json"
else
    echo "Test failed. No output file generated."
fi

echo "Installation and test complete!" 