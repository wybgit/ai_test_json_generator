# AI JSON Generator

A tool for generating AI model JSON descriptions based on templates, specifically designed for ONNX NPU operator test cases.

## Features

- Template-based generation with variable substitution
- Support for file-based replacement values
- JSON validation and automatic retry for malformed responses
- Detailed error feedback for invalid JSON
- Debug mode for saving prompts and responses
- Configurable LLM backend (uses SiliconFlow API by default)
- Detailed logging of generation process

## Installation

### Using pip (from GitHub)

```bash
pip install git+https://github.com/yourusername/AI_JSON_Generator.git
```

### Installing from Wheel Package

1. Build the wheel package
   ```bash
   ./build_wheel.sh
   ```

2. Install the wheel package
   ```bash
   pip install dist/ai_json_generator-0.1.0-py3-none-any.whl
   ```

### Local Development Installation

1. Clone this repository
   ```bash
   git clone https://github.com/yourusername/AI_JSON_Generator.git
   cd AI_JSON_Generator
   ```

2. Install in development mode
   ```bash
   pip install -e .
   ```

### Required Dependencies

The tool automatically installs required dependencies:
- requests
- colorama

## Usage

### Command Line Interface

After installation, you can use the following commands:

#### Generate JSON using a template

```bash
ai-json-generate --template prompts/op_testcase.prompt --replacements "算子名=Add,算子参数=input_shape=[1,3,224,224]" --output-folder output --output-name add_operator
```

#### Generate an operator test case

```bash
ai-json-operator Add --output-dir test_cases
```

### Basic Python API Usage

```python
from ai_json_generator import LLMJsonGenerator, parse_key_value_pairs

# Initialize the generator
generator = LLMJsonGenerator("config.json")

# Parse replacements
replacements = parse_key_value_pairs("算子名=Add,算子参数=inputs: [A, B], outputs: [C]")

# Generate JSON
success = generator.generate(
    "prompts/op_testcase.prompt",
    replacements,
    "output",
    "add_test",
    "json",
    max_retries=3,
    debug=True
)
```

### Command-line Arguments

- `--template`: Path to the prompt template file (Required)
- `--replacements`: Comma-separated key=value pairs to replace in the template. Values can be file paths.
- `--output-folder`: Output folder for generated files (Default: "output")
- `--output-name`: Base name for the output file (Default: "output")
- `--output-ext`: File extension for the output (Default: "json")
- `--config`: Path to LLM config file (Default: "config.json")
- `--max-retries`: Maximum number of retry attempts for JSON generation (Default: 3)
- `--debug`: Enable debug mode to save prompts and raw responses

### File-based Replacements

You can use file paths as replacement values. The content of the file will be used as the replacement:

```bash
ai-json-generate \
  --template prompts/op_testcase.prompt \
  --replacements "算子名=Add,算子参数=params.txt,用例要求=requirements.txt" \
  --output-folder test_cases \
  --output-name add_test
```

### Debug Mode

Enable debug mode to save the prompts and responses for troubleshooting:

```bash
ai-json-generate \
  --template prompts/op_testcase.prompt \
  --replacements "算子名=Add,算子参数=params.txt" \
  --debug
```

Debug mode will generate the following files:
- `{output_name}.prompt.txt`: The initial prompt sent to the LLM
- `{output_name}.attempt{n}.response.txt`: The raw response from each attempt
- `{output_name}.retry{n}.prompt.txt`: The retry prompts with error feedback

### Example with op_testcase.prompt

To generate a test case for the Add operator:

```bash
ai-json-generate \
  --template prompts/op_testcase.prompt \
  --replacements "算子名=Add,算子参数=inputs: [A, B], outputs: [C], attributes: {},算子类型=binary arithmetic,用例要求=测试基本的Add算子，输入两个相同shape的tensor，输出一个tensor,IR_JSON要求=IR模型描述应包含模型的input、output、node等信息" \
  --output-folder test_cases \
  --output-name add_basic \
  --output-ext json
```

## Error Handling

When JSON validation fails, the script will:
1. Extract the problematic part of the JSON
2. Send detailed error information back to the LLM
3. Retry up to the specified number of retries (default: 3)
4. Save the final error response if all retries fail

## ONNX Operator Test Case Generation

The package provides tools for generating test cases for ONNX operators:

### Single Operator Test Case

Use the `ai-json-operator` command to generate a test case for a specific operator:

```bash
ai-json-operator Conv
```

This command:
1. Looks up operator information in `data_files/onnx_operators.csv`
2. Reads test requirements from `data_files/test_point.txt`
3. Reads IR JSON format requirements from `data_files/IR_JSON_FORMAT.md`
4. Generates a test case JSON file using the LLM

### CSV Structure for Operators

The CSV file should have the following structure:

```
operator_name,versions,description,input_name,input_type,input_description,output_name,output_type,output_description,attribute_name,attribute_type,attribute_description,npu_unit
Conv,1,Convolution operator,X,T,Input tensor,Y,T,Output tensor,kernel_size,ints,Size of the convolution kernels,vector
```

## Configuration

The `config.json` file contains settings for the LLM API:

```json
{
    "api_token": "YOUR_API_TOKEN",
    "api_url": "https://api.siliconflow.cn/v1/chat/completions",
    "model": "Qwen/Qwen2.5-72B-Instruct",
    "max_tokens": 2048,
    "temperature": 0.7,
    "top_p": 0.7
} 
```

The package will look for this file in the following order:
1. Path specified by the `AI_JSON_GENERATOR_CONFIG` environment variable (if set)
2. The specified path (if provided as command-line argument)
3. The current working directory
4. The package installation directory
5. `~/.ai_json_generator/config.json`

### Setting the Configuration Path with Environment Variable

You can set the path to the configuration file using the environment variable:

```bash
# Linux/macOS
export AI_JSON_GENERATOR_CONFIG=/path/to/your/config.json
ai-json-generate --template your_template.prompt ...

# Windows (Command Prompt)
set AI_JSON_GENERATOR_CONFIG=C:\path\to\your\config.json
ai-json-generate --template your_template.prompt ...

# Windows (PowerShell)
$env:AI_JSON_GENERATOR_CONFIG="C:\path\to\your\config.json"
ai-json-generate --template your_template.prompt ...
```

## Logs

Logs are saved to `llm_generation.log` in the execution directory. They include information about:
- Template loading and filling
- File-based replacement processing
- LLM API requests
- JSON validation and error details
- Retry attempts
- File saving

Failed outputs are saved with a `.error` extension for debugging. 