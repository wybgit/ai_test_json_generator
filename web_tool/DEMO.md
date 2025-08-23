# AI Tools Web Interface - 演示指南

## 快速开始

### 1. 启动服务

使用一键启动脚本：
```bash
cd /home/wyb/AI_tools/ai_test_json_generator/web_tool
./start_all.sh
```

或者分别启动前后端：
```bash
# 启动后端
./start_backend.sh

# 启动前端（新终端）
./start_frontend.sh
```

### 2. 访问应用

打开浏览器访问：**http://localhost:8080**

## 使用演示

### 步骤1：选择工具
1. 在主页面看到工具卡片：**AI JSON Generator**
2. 点击选择该工具
3. 工具配置区域将显示

### 步骤2：配置模板
1. 在"模板配置"区域，从下拉列表选择：**op_template.prompt.txt**
2. 模板内容将自动加载，显示Jinja2模板内容
3. 系统自动识别模板变量：
   - `算子级联信息`
   - `算子级联结构`

### 步骤3：选择数据模式

#### 选项A：手动填写变量
1. 保持"手动填写变量"选项
2. 在变量输入框中填写：
   - **算子级联信息**: `Abs单算子测试`
   - **算子级联结构**: `输入->Abs->输出`

#### 选项B：使用CSV数据（推荐）
1. 选择"使用 CSV 数据"选项
2. 从下拉列表选择：**test_points_1.csv**
3. 查看CSV数据预览，包含2行测试数据

### 步骤4：预览模板
1. 点击"刷新预览"按钮
2. 在"模板预览"区域查看渲染后的内容
3. 确保所有变量都正确替换

### 步骤5：执行工具
1. 设置"最大重试次数"（默认3次）
2. 点击"开始执行"按钮
3. 观察执行状态变化：**就绪** → **执行中** → **执行完成**

### 步骤6：查看实时日志
1. 执行区域显示实时日志输出
2. 观察ai-json-generator工具的执行过程
3. 日志包括：
   - 执行开始信息
   - 工具输出内容
   - 执行结果状态

### 步骤7：查看和下载结果
1. 执行完成后，"执行结果"区域显示生成的文件
2. 点击"查看"按钮在线预览JSON文件内容
3. 点击"下载"按钮下载单个文件
4. 点击"下载全部结果"获取ZIP压缩包

## 功能特色演示

### 1. 实时WebSocket通信
- 执行过程中的所有日志都实时显示
- 无需刷新页面即可看到最新状态
- 可随时停止正在执行的任务

### 2. 文件管理
- 支持模板文件上传（.txt格式）
- 支持CSV文件上传（.csv格式）
- 在线查看生成的JSON文件内容
- 语法高亮显示

### 3. 模板系统
- 完整的Jinja2模板支持
- 自动变量识别和提取
- 实时模板预览
- 变量验证

### 4. 批量处理
- CSV数据批量处理
- 一次性处理多行数据
- 每行数据生成独立的JSON文件

## 示例输出

执行成功后，会在输出目录生成类似以下文件：
```
ai_json_generator_20240823_132945/
├── batch_result_1.json    # 第一行CSV数据的结果
├── batch_result_2.json    # 第二行CSV数据的结果
└── execution_log.txt      # 执行日志
```

每个JSON文件包含完整的ONNX算子描述，如：
```json
{
    "Case_Name": "Abs_Single_Test_Case",
    "Case_Purpose": "测试Abs单算子",
    "Opset": 13,
    "Model_Inputs": ["input"],
    "Model_Outputs": ["output"],
    "Nodes": [...]
}
```

## 故障排除

### 1. 后端无法启动
- 检查Python依赖：`pip install -r backend/requirements.txt`
- 确保端口5000未被占用
- 查看后端日志：`cat backend.log`

### 2. 前端页面无法访问
- 确保端口8080未被占用
- 检查前端服务状态：`ps aux | grep "http.server"`

### 3. WebSocket连接失败
- 确保后端服务正常运行
- 检查防火墙设置
- 刷新页面重新连接

### 4. 工具执行失败
- 确保ai-json-generator工具已安装并在PATH中
- 检查模板语法是否正确
- 查看执行日志中的错误信息

## 扩展功能

### 添加新工具
1. 在 `backend/tools/` 创建新的工具类
2. 继承 `BaseTool` 类
3. 在 `tools/__init__.py` 中注册
4. 在 `config/config.py` 中配置

### 自定义模板
1. 创建新的 `.txt` 文件
2. 使用Jinja2语法定义变量：`{{ variable_name }}`
3. 上传到系统或放置在 `shared/templates/` 目录

### 扩展CSV数据
1. 确保CSV列名与模板变量名对应
2. 支持任意数量的行和列
3. 第一行必须是列标题

## 技术细节

- **后端**: Flask + Flask-SocketIO + Python
- **前端**: Vanilla JavaScript + Bootstrap 5
- **通信**: RESTful API + WebSocket
- **模板**: Jinja2 模板引擎
- **数据**: CSV文件处理，JSON输出

## 支持

如有问题，请检查：
1. 系统日志文件
2. 浏览器开发者工具控制台
3. 后端执行日志

联系开发团队获取技术支持。
