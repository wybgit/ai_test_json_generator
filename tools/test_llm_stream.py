import json
import requests
import sys
from colorama import init, Fore, Back, Style

init(autoreset=True)  # 初始化colorama，确保颜色设置自动重置

def stream_chat_response(url, payload, headers):
    """发送流式请求并处理响应，在同一行内刷新显示思考过程和回复内容"""
    with requests.post(url, json=payload, headers=headers, stream=True) as response:
        response.raise_for_status()
        
        # 初始化变量存储思考过程和最终回复
        thinking_process = []
        final_response = []
        current_line = ""  # 当前行内容
        is_receiving_content = False
        
        for line in response.iter_lines():
            if line:
                # 移除'data: '前缀并解析JSON
                line = line.decode('utf-8').replace('data: ', '')
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # 提取思考过程内容
                reasoning_content = data.get('choices', [{}])[0].get('delta', {}).get('reasoning_content')
                if reasoning_content and not is_receiving_content:
                    thinking_process.append(reasoning_content)
                    # 更新当前行（思考过程）
                    current_line = f"{Fore.BLACK}{Back.WHITE}[思考中] {reasoning_content}{Style.RESET_ALL}"
                    # 清空当前行并写入新内容
                    sys.stdout.write('\r' + ' ' * len(current_line) + '\r')
                    sys.stdout.write(current_line)
                    sys.stdout.flush()
                
                # 提取回复内容
                content = data.get('choices', [{}])[0].get('delta', {}).get('content')
                if content:
                    is_receiving_content = True
                    final_response.append(content)
                    # 更新当前行（回复内容）
                    current_line = f"{Fore.WHITE}{Back.GREEN}[回复] {''.join(final_response)}{Style.RESET_ALL}"
                    # 清空当前行并写入新内容
                    sys.stdout.write('\r' + ' ' * len(current_line) + '\r')
                    sys.stdout.write(current_line)
                    sys.stdout.flush()
                
                # 检查是否结束
                finish_reason = data.get('choices', [{}])[0].get('finish_reason')
                if finish_reason == 'stop':
                    break
        
        # 最后添加换行符，保持美观
        sys.stdout.write('\n')
        sys.stdout.flush()
        
        return {
            'thinking_process': ''.join(thinking_process),
            'final_response': ''.join(final_response)
        }

# 使用示例（保持与之前相同）
url = "https://api.siliconflow.cn/v1/chat/completions"
payload = {
    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "stream": True,
    "max_tokens": 512,
    "thinking_budget": 4096,
    "min_p": 0.05,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "stop": [],
    "messages": [
        {"role": "system", "content": "今天星期几"}
    ]
}
headers = {
    "Authorization": "Bearer sk-shfdyfflywfqrbpdmitynbzxygnhezpajjelataqjowxrqlp",
    "Content-Type": "application/json"
}

result = stream_chat_response(url, payload, headers)
print("\n--- 完整思考过程 ---")
print(result['thinking_process'])
print("\n--- 最终回复 ---")
print(result['final_response'])