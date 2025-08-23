from tools.ai_json_generator_tool import AIJsonGeneratorTool
from tools.base_tool import BaseTool

# 工具注册表
TOOL_REGISTRY = {
    'ai_json_generator': AIJsonGeneratorTool
}

def get_tool(tool_name: str, config: dict) -> BaseTool:
    """获取工具实例"""
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    tool_class = TOOL_REGISTRY[tool_name]
    return tool_class(config)

def list_available_tools():
    """列出所有可用的工具"""
    return list(TOOL_REGISTRY.keys())
