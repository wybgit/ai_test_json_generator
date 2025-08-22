# AI JSON Generator API 文档

## 概述

AI JSON Generator 提供了两套API：
- **API v1**: 简单的Web界面功能
- **API v2**: 完整的CLI功能映射，直接调用核心ai-json-generator功能

## CLI 命令行用法

### 基本用法

```bash
# 生成单个算子的测试用例
ai-json-generator MatMul -o outputs

# 生成多个算子的测试用例
ai-json-generator "MatMul Add Slice" -o outputs

# 使用直接提示文件
ai-json-generator --direct-prompt prompt.txt -o outputs

# 批量生成（使用CSV和模板）
ai-json-generator --batch-csv data.csv --direct-prompt template.txt -o outputs

# 转换为ONNX模型
ai-json-generator MatMul -o outputs --convert-to-onnx

# 调试模式
ai-json-generator MatMul -o outputs --debug --verbose
```

### CLI 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `operator` | string | 算子名称，支持多个算子 |
| `-o, --output` | string | 输出目录 |
| `--quiet` | bool | 禁用输出显示 |
| `--test-point` | string | 指定测试点key |
| `--graph-pattern` | string | 指定图模式key |
| `--add-req` | string | 添加额外要求 |
| `--direct-prompt` | string | 直接使用的提示文件路径 |
| `--direct-request` | string | 直接使用的请求文件路径 |
| `--batch-csv` | string | 批量生成的CSV文件路径 |
| `--convert-to-onnx` | bool | 转换为ONNX模型 |
| `--max-retries` | int | 最大重试次数 (默认: 1) |
| `--debug` | bool | 启用调试模式 |
| `--verbose, -v` | bool | 详细模式 |
| `--no-color` | bool | 禁用彩色输出 |

## API v2 端点

### 基础URL
```
http://localhost:5000/api/v2
```

### 1. 单个测试用例生成

**端点**: `POST /api/v2/generate/single`

**功能**: 对应CLI命令 `ai-json-generator <operator> [options]`

**请求体**:
```json
{
    "operator": "MatMul",              // 可选，算子名称
    "output_dir": "outputs",           // 可选，输出目录
    "test_point": null,                // 可选，测试点
    "graph_pattern": null,             // 可选，图模式
    "add_req": null,                   // 可选，额外要求
    "direct_prompt": "生成MatMul算子...", // 可选，直接提示内容或文件路径
    "direct_request": null,            // 可选，直接请求内容或文件路径
    "convert_to_onnx": false,          // 可选，是否转换为ONNX
    "max_retries": 1,                  // 可选，最大重试次数
    "debug": true,                     // 可选，调试模式
    "quiet": false                     // 可选，静默模式
}
```

**响应**:
```json
{
    "success": true,
    "task_id": "uuid-string",
    "message": "生成任务已启动",
    "status_url": "/api/v2/tasks/{task_id}/status"
}
```

### 2. 批量测试用例生成

**端点**: `POST /api/v2/generate/batch`

**功能**: 对应CLI命令 `ai-json-generator --batch-csv <csv> --direct-prompt <prompt> [options]`

**请求体**:
```json
{
    "csv_data": [                      // 必需，CSV数据数组
        {
            "算子名": "MatMul",
            "算子级联信息": "MatMul+Relu",
            "算子级联结构": "串联",
            "特殊要求": "支持广播"
        }
    ],
    "prompt_template": "生成{{算子名}}算子...", // 必需，Jinja2模板
    "output_dir": "outputs",           // 可选，输出目录
    "convert_to_onnx": false,          // 可选，是否转换为ONNX
    "max_retries": 1,                  // 可选，最大重试次数
    "debug": true,                     // 可选，调试模式
    "quiet": false                     // 可选，静默模式
}
```

**响应**:
```json
{
    "success": true,
    "task_id": "uuid-string",
    "message": "批量生成任务已启动",
    "status_url": "/api/v2/tasks/{task_id}/status"
}
```

### 3. 任务状态查询

**端点**: `GET /api/v2/tasks/{task_id}/status`

**响应**:
```json
{
    "success": true,
    "task": {
        "id": "uuid-string",
        "type": "single_generation",    // 或 "batch_generation"
        "status": "running",            // created, running, completed, failed, error
        "logs": [                       // 最近50条日志
            {
                "timestamp": "10:30:15",
                "level": "info",
                "message": "开始生成..."
            }
        ],
        "result": {                     // 仅在completed状态
            "success": true,
            "output_dir": "/path/to/output",
            "files": [...]
        },
        "error": null,                  // 仅在error状态
        "created_at": "2024-01-01T10:30:00",
        "last_update": "2024-01-01T10:30:30"
    }
}
```

### 4. 任务日志获取

**端点**: `GET /api/v2/tasks/{task_id}/logs`

**响应**:
```json
{
    "success": true,
    "logs": [
        {
            "timestamp": "10:30:15",
            "level": "info",
            "message": "开始生成..."
        }
    ]
}
```

### 5. 任务文件列表

**端点**: `GET /api/v2/tasks/{task_id}/files`

**响应**:
```json
{
    "success": true,
    "files": [
        {
            "name": "MatMul_test.json",
            "path": "MatMul_test.json",
            "size": 1024,
            "preview": "{\"graph\": {...}}",
            "type": "json"
        }
    ]
}
```

### 6. 任务文件下载

**端点**: `GET /api/v2/tasks/{task_id}/download`

**响应**: ZIP文件下载

### 7. 任务列表

**端点**: `GET /api/v2/tasks`

**响应**:
```json
{
    "success": true,
    "tasks": [
        {
            "id": "uuid-string",
            "type": "single_generation",
            "status": "completed",
            "created_at": "2024-01-01T10:30:00",
            "last_update": "2024-01-01T10:35:00"
        }
    ]
}
```

### 8. 配置信息获取

**端点**: `GET /api/v2/config`

**响应**:
```json
{
    "success": true,
    "config": {
        "model": "Qwen/Qwen3-235B-A22B",
        "api_url": "https://api.siliconflow.cn/v1/chat/completions",
        "max_tokens": 8192,
        "temperature": 0.6
    }
}
```

## API v1 端点（兼容性）

### 1. 模板管理
- `GET /api/templates` - 获取模板列表
- `POST /api/parse_template` - 解析模板变量

### 2. CSV文件管理
- `GET /api/csv_files` - 获取CSV文件列表

### 3. 生成功能（已弃用，建议使用v2）
- `POST /api/generate` - 生成测试用例（WebSocket方式）

## 使用示例

### Python示例

```python
import requests
import time

# 1. 生成单个测试用例
response = requests.post('http://localhost:5000/api/v2/generate/single', json={
    'direct_prompt': '生成一个MatMul算子的测试用例',
    'convert_to_onnx': True,
    'debug': True
})

if response.json()['success']:
    task_id = response.json()['task_id']
    
    # 2. 监控任务状态
    while True:
        status_response = requests.get(f'http://localhost:5000/api/v2/tasks/{task_id}/status')
        task = status_response.json()['task']
        
        print(f"任务状态: {task['status']}")
        
        if task['status'] in ['completed', 'failed', 'error']:
            break
            
        time.sleep(2)
    
    # 3. 下载结果
    if task['status'] == 'completed':
        download_response = requests.get(f'http://localhost:5000/api/v2/tasks/{task_id}/download')
        with open(f'results_{task_id}.zip', 'wb') as f:
            f.write(download_response.content)
```

### JavaScript示例

```javascript
// 1. 生成测试用例
async function generateTestCase() {
    const response = await fetch('/api/v2/generate/single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'direct_prompt': '生成一个MatMul算子的测试用例',
            'convert_to_onnx': true,
            'debug': true
        })
    });
    
    const result = await response.json();
    if (result.success) {
        return result.task_id;
    }
}

// 2. 监控任务状态
async function monitorTask(taskId) {
    const response = await fetch(`/api/v2/tasks/${taskId}/status`);
    const data = await response.json();
    
    if (data.success) {
        const task = data.task;
        console.log('任务状态:', task.status);
        
        // 显示新日志
        task.logs.forEach(log => {
            console.log(`[${log.timestamp}] ${log.message}`);
        });
        
        return task.status;
    }
}
```

## 错误处理

所有API端点都使用统一的错误格式：

```json
{
    "success": false,
    "error": "错误描述信息"
}
```

HTTP状态码：
- `200` - 成功
- `400` - 请求参数错误
- `404` - 资源不存在
- `500` - 服务器内部错误

## 注意事项

1. **任务异步执行**: v2 API采用异步任务模式，需要通过轮询获取结果
2. **会话管理**: 任务与HTTP会话关联，清除cookies会丢失任务访问权限
3. **文件清理**: 生成的文件会保留一段时间，建议及时下载
4. **并发限制**: 建议同时运行的任务不超过5个
5. **模板语法**: 使用Jinja2模板语法，变量格式为`{{变量名}}`

## 与CLI的对应关系

| CLI命令 | API端点 | 说明 |
|---------|---------|------|
| `ai-json-generator MatMul` | `POST /api/v2/generate/single` | 单个算子生成 |
| `--direct-prompt file.txt` | `direct_prompt` 参数 | 直接提示 |
| `--batch-csv data.csv --direct-prompt template.txt` | `POST /api/v2/generate/batch` | 批量生成 |
| `--convert-to-onnx` | `convert_to_onnx` 参数 | ONNX转换 |
| `--debug --verbose` | `debug` 参数 | 调试模式 |
| `--max-retries 3` | `max_retries` 参数 | 重试设置 |
| `-o outputs` | `output_dir` 参数 | 输出目录 |

通过API v2，Web界面可以完全复现CLI的所有功能。
