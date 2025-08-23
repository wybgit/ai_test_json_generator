# AI 工具 Web 界面

一个现代化的 Web 界面，用于调用和管理 AI 工具，特别是 ai-json-generator 工具。

## 功能特性

- 🔧 **模块化工具系统**: 支持多种 AI 工具，方便扩展
- 📝 **智能模板管理**: 支持 Jinja2 模板，实时预览和变量填写
- 📊 **CSV 数据支持**: 批量处理数据，支持文件上传和在线编辑
- 🚀 **实时执行监控**: WebSocket 实时日志输出，支持执行控制
- 📁 **结果管理**: 在线查看、下载单个文件或批量下载
- 🎨 **现代化 UI**: 响应式设计，美观易用
- 🔄 **实时通信**: WebSocket 支持，实时获取执行状态

## 项目结构

```
web_tool/
├── backend/                 # 后端 Flask 应用
│   ├── app/                # 应用主模块
│   │   ├── routes.py       # API 路由
│   │   └── socket_events.py # WebSocket 事件处理
│   ├── tools/              # 工具模块
│   │   ├── base_tool.py    # 工具基类
│   │   └── ai_json_generator_tool.py # AI JSON Generator 工具
│   ├── config/             # 配置模块
│   ├── utils/              # 工具函数
│   └── run.py              # 应用启动入口
├── frontend/               # 前端应用
│   ├── src/                # 源代码
│   │   ├── components/     # 组件模块
│   │   ├── services/       # 服务模块
│   │   └── utils/          # 工具函数
│   ├── static/             # 静态资源
│   └── index.html          # 主页面
└── shared/                 # 共享资源
    ├── templates/          # 模板文件
    ├── uploads/            # 上传文件
    └── outputs/            # 输出文件
```

## 安装和运行

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python run.py
```

后端服务将在 `http://localhost:5000` 启动。

### 3. 启动前端服务

```bash
cd frontend
python -m http.server 8080
```

前端服务将在 `http://localhost:8080` 启动。

### 4. 访问应用

打开浏览器访问 `http://localhost:8080`

## 使用说明

### 1. 选择工具

在主页面选择要使用的 AI 工具，目前支持：
- **AI JSON Generator**: ONNX 模型 NPU 转换工具用例设计助手

### 2. 配置模板

- **选择现有模板**: 从下拉列表中选择预设模板
- **上传新模板**: 支持 `.txt` 格式的 Jinja2 模板文件
- **填写变量**: 系统会自动识别模板中的变量并提供输入框

### 3. 数据配置

支持两种数据输入模式：

#### 手动模式
直接在界面中填写模板变量的值

#### CSV 模式
- 选择现有 CSV 文件或上传新文件
- CSV 文件的列名应与模板变量名对应
- 支持批量处理多行数据

### 4. 预览和执行

- **实时预览**: 查看模板渲染后的效果
- **开始执行**: 点击执行按钮开始工具调用
- **实时日志**: 查看工具执行的实时输出
- **停止执行**: 可随时停止正在执行的任务

### 5. 结果查看

- **文件列表**: 查看生成的所有文件
- **在线查看**: 支持文本文件的在线预览
- **单文件下载**: 下载单个结果文件
- **批量下载**: 将所有结果打包下载

## API 接口

### RESTful API

- `GET /api/health` - 健康检查
- `GET /api/tools` - 获取工具列表
- `GET /api/templates` - 获取模板列表
- `GET /api/templates/{name}` - 获取模板内容
- `POST /api/upload/template` - 上传模板文件
- `POST /api/upload/csv` - 上传 CSV 文件
- `POST /api/template/preview` - 模板预览
- `POST /api/tools/{name}/execute` - 执行工具（同步）
- `GET /api/outputs/{id}` - 获取执行结果

### WebSocket 事件

- `execute_tool_async` - 异步执行工具
- `execution_started` - 执行开始
- `execution_log` - 执行日志
- `execution_completed` - 执行完成
- `execution_error` - 执行错误
- `stop_execution` - 停止执行

## 添加新工具

要添加新的 AI 工具，请按照以下步骤：

### 1. 创建工具类

```python
# backend/tools/your_tool.py
from .base_tool import BaseTool

class YourTool(BaseTool):
    def validate_params(self, params):
        # 验证参数
        pass
    
    def build_command(self, params):
        # 构建执行命令
        pass
    
    def get_supported_templates(self):
        # 返回支持的模板
        pass
    
    def get_output_files(self, output_dir):
        # 返回输出文件列表
        pass
```

### 2. 注册工具

```python
# backend/tools/__init__.py
from .your_tool import YourTool

TOOL_REGISTRY = {
    'your_tool': YourTool,
    # ... 其他工具
}
```

### 3. 配置工具

```python
# backend/config/config.py
TOOLS_CONFIG = {
    'your_tool': {
        'name': 'Your Tool',
        'description': '工具描述',
        'executable': 'your-tool-command',
        'templates_supported': True,
        'csv_supported': True
    }
}
```

## 开发和调试

### 开发模式

在开发环境中，可以使用以下调试工具：

```javascript
// 浏览器控制台
window.debug.status()      // 获取应用状态
window.debug.export()      // 导出配置
window.debug.components    // 访问组件
window.debug.services     // 访问服务
```

### 日志级别

- `INFO`: 常规信息
- `WARNING`: 警告信息  
- `ERROR`: 错误信息
- `SUCCESS`: 成功信息

## 技术栈

### 后端
- **Flask**: Web 框架
- **Flask-SocketIO**: WebSocket 支持
- **Flask-CORS**: 跨域支持
- **Pandas**: 数据处理
- **Jinja2**: 模板引擎

### 前端
- **Vanilla JavaScript**: 原生 JavaScript
- **Bootstrap 5**: UI 框架
- **Socket.IO**: WebSocket 客户端
- **Prism.js**: 代码语法高亮
- **Font Awesome**: 图标库

## 部署说明

### 生产环境

1. 使用 WSGI 服务器（如 Gunicorn）运行后端
2. 使用 Nginx 作为反向代理和静态文件服务器
3. 配置 HTTPS 证书
4. 设置适当的环境变量

### Docker 部署

```dockerfile
# 示例 Dockerfile
FROM python:3.9
COPY backend /app/backend
COPY frontend /app/frontend
WORKDIR /app/backend
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "run.py"]
```

## 常见问题

### Q: WebSocket 连接失败？
A: 检查后端服务是否正常运行，确保端口 5000 可访问。

### Q: 文件上传失败？
A: 检查文件大小是否超过限制（16MB），文件格式是否正确。

### Q: 工具执行失败？
A: 查看执行日志，确保 ai-json-generator 工具已正确安装并可执行。

### Q: 模板变量识别错误？
A: 确保使用标准的 Jinja2 语法 `{{ variable_name }}`。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
