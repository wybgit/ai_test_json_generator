# AI JSON 生成器

一个基于模板生成AI模型JSON描述的工具，专门为ONNX NPU算子测试用例设计。

## 功能特性

- 基于模板的生成，支持变量替换
- 支持基于文件的替换值
- JSON验证和自动重试处理格式错误的响应
- 详细的错误反馈用于无效JSON
- 调试模式，可保存提示和响应
- 可配置的LLM后端（默认使用SiliconFlow API）
- 详细的生成过程日志记录
- **新功能：批量CSV处理**，支持从CSV文件读取测试点并使用Jinja2模板生成
- **新功能：断点续执行**，支持从中断处继续执行，防止网络问题导致重复执行

## 安装

### 使用pip（从GitHub）

```bash
pip install git+https://github.com/yourusername/AI_JSON_Generator.git
```

### 从Wheel包安装

1. 构建wheel包
   ```bash
   ./build_wheel.sh
   ```

2. 安装wheel包
   ```bash
   pip install dist/ai_json_generator-0.1.0-py3-none-any.whl
   ```

### 本地开发安装

1. 克隆此仓库
   ```bash
   git clone https://github.com/yourusername/AI_JSON_Generator.git
   cd AI_JSON_Generator
   ```

2. 以开发模式安装
   ```bash
   pip install -e .
   ```

### 必需依赖

工具会自动安装所需依赖：
- requests
- colorama
- rich
- jinja2

## 使用方法

### 命令行接口

安装后，您可以使用以下命令：

#### 使用模板生成JSON

```bash
ai-json-generator --template prompts/op_testcase.prompt --replacements "算子名=Add,算子参数=input_shape=[1,3,224,224]" --output-folder output --output-name add_operator
```

#### 生成算子测试用例

```bash
ai-json-generator Add --output-dir test_cases
```

#### 使用直接提示文件生成（单个测试用例）

```bash
ai-json-generator --direct-prompt examples/op_template.prompt.txt --convert-to-onnx --max-retries 3 -o abs_outputs
```

#### **新功能：批量CSV处理**

使用CSV文件批量生成多个测试用例，CSV表头将作为Jinja2模板变量：

```bash
ai-json-generator --direct-prompt examples/op_template.prompt.txt --batch-csv examples/test_points.csv --convert-to-onnx --max-retries 3 -o batch_outputs
```

**CSV文件格式示例（test_points.csv）：**
```csv
算子级联信息,算子级联结构
Abs+Relu,串联
Abs+Add,并联
Conv+Relu,串联
Div+Concat,并联
```

**对应的Jinja2模板示例：**
```
请按照以下要求生成用例：
{{ 算子级联信息 }}

按照如下图结构进行算子级联：
{{ 算子级联结构 }}
```

### 命令行参数说明

- `--direct-prompt`: 指定提示模板文件路径
- `--batch-csv`: 指定CSV文件路径，用于批量生成
- `--convert-to-onnx`: 将生成的JSON转换为ONNX模型
- `--max-retries`: 失败时的最大重试次数
- `-o, --output`: 指定输出目录
- `--debug`: 启用调试模式，保存中间文件
- `--quiet`: 静默模式，不显示LLM输出

### 批量处理功能详解

#### 输出结构

使用`--batch-csv`时，每个测试用例会在输出目录下创建独立的子目录：

```
batch_outputs/
├── test_001_Abs+Relu/
│   ├── operator_testcase.json
│   ├── operator_testcase.onnx
│   ├── test_metadata.json
│   └── rendered_prompt.txt
├── test_002_Abs+Add/
│   ├── operator_testcase.json
│   ├── operator_testcase.onnx
│   ├── test_metadata.json
│   └── rendered_prompt.txt
├── batch_results.csv
└── ...
```

#### 结果记录CSV

系统会自动生成`batch_results.csv`文件，记录每个测试用例的执行状态：

```csv
test_index,test_name,csv_data,json_status,onnx_status,output_directory,timestamp,error_message
1,Abs+Relu,"{""算子级联信息"": ""Abs+Relu"", ""算子级联结构"": ""串联""}",success,success,test_001_Abs+Relu,2024-01-01 12:00:00,
2,Abs+Add,"{""算子级联信息"": ""Abs+Add"", ""算子级联结构"": ""并联""}",success,failed,test_002_Abs+Add,2024-01-01 12:01:00,ONNX conversion failed
```

#### 断点续执行

如果批量处理过程中断（如网络问题），再次运行相同命令时会：
1. 读取现有的`batch_results.csv`文件
2. 跳过已成功完成的测试用例
3. 从中断处继续执行
4. 更新结果记录

### 基本Python API使用

```python
from ai_json_generator import LLMJsonGenerator, parse_key_value_pairs

# 初始化生成器
generator = LLMJsonGenerator("config.json")

# 解析替换参数
replacements = parse_key_value_pairs("算子名=Add,算子参数=inputs: [A, B], outputs: [C]")

# 生成JSON
success = generator.generate(
    template_path="prompts/op_testcase.prompt",
    replacements=replacements,
    output_folder="output",
    output_filename="add_operator",
    output_ext="json"
)
```

## 配置

### LLM配置文件

创建`config.json`文件来配置LLM设置：

```json
{
    "api_url": "https://api.siliconflow.cn/v1/chat/completions",
    "api_token": "your_api_token_here",
    "model": "deepseek-ai/deepseek-llm-67b-chat",
    "max_tokens": 4096,
    "temperature": 0.1,
    "top_p": 0.9
}
```

### 环境变量

您也可以通过环境变量指定配置文件路径：

```bash
export AI_JSON_GENERATOR_CONFIG=/path/to/your/config.json
```

## 模板系统

### Jinja2模板支持

系统支持完整的Jinja2模板语法：

```jinja2
你是一个onnx模型NPU转换工具用例设计助手，设计{{ 算子名 }}算子的相关模型IR JSON内容。

请按照以下要求生成用例：
{{ 算子级联信息 }}

按照如下图结构进行算子级联：
{{ 算子级联结构 }}

{% if 特殊要求 %}
特殊要求：{{ 特殊要求 }}
{% endif %}
```

### 向后兼容

系统同时支持简单的`{variable}`格式以保持向后兼容性。

## 调试和故障排除

### 调试模式

使用`--debug`参数启用调试模式：

```bash
ai-json-generator --direct-prompt template.txt --batch-csv data.csv --debug -o debug_output
```

调试模式会保存：
- 渲染后的提示文件
- LLM响应内容
- 错误日志
- 中间处理文件

### 常见问题

1. **网络连接问题**：使用`--max-retries`增加重试次数
2. **JSON格式错误**：检查模板文件格式，确保LLM输出有效JSON
3. **CSV格式问题**：确保CSV文件使用UTF-8编码，表头名称与模板变量匹配
4. **ONNX转换失败**：检查生成的JSON是否符合ONNX规范

### 日志级别

使用`--verbose`或`--debug`获取详细日志输出。

## 许可证

MIT License

## 贡献

欢迎提交问题和拉取请求来改进此工具。

## 更新日志

### v0.2.0
- 新增批量CSV处理功能
- 添加Jinja2模板引擎支持
- 实现断点续执行功能
- 添加结果记录CSV
- 改进错误处理和日志记录

### v0.1.0
- 初始版本
- 基本的JSON生成功能
- 模板系统支持
- ONNX转换集成