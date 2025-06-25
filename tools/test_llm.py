import requests

url = "https://api.siliconflow.cn/v1/chat/completions"

prompt = '''你是一个onnx模型NPU转换工具用例设计助手，设计matmul add算子的相关模型IR JSON内容。

请按照以下要求生成用例：
1. 算子名称：matmul add
2. 算子参数信息：
算子: matmul
描述: Matrix product that behaves like [numpy.matmul](https://numpy.org/doc/stable/reference/generated/numpy.matmul.html).
支持版本: 13, 1, 9
输入:
  - A (类型: T) - N-dimensional matrix A
  - B (类型: T) - N-dimensional matrix B
输出:
  - Y (类型: T) - Matrix multiply results from A * B
执行单元: cube

算子: add
描述: Performs element-wise binary addition (with Numpy-style broadcasting support).   This operator supports **multidirectional (i.e., Numpy-style) broadcasting**; for more details please check [the doc](Broadcasting.md).   (Opset 14 change): Extend supported types to include uint8, int8, uint16, and int16.
支持版本: 14, 1, 6, 7, 13
输入:
  - A (类型: T) - First operand.
  - B (类型: T) - Second operand.
输出:
  - C (类型: T) - Result, has same element type as two inputs
执行单元: vector

3. 测试点信息：
测试点: default
描述: 测试算子默认参数和形状的基本功能

4. 构图模式：
构图模式: sequential
描述: 将算子按序连接，前一个算子的输出连接到下一个算子的输入

5. 构建JSON时请遵循以下连接规则：
   - 对于级联算子，前一个算子的输出名称需要与后一个算子的输入名称保持一致，作为连接点
   - 对于多个算子共用同一输入的场景，确保相关输入具有相同的名称和形状
   - 所有在线(Online)输入应当被包含在Model_Inputs列表中
   - 最终的输出(算子链最后的输出)应当被包含在Model_Outputs列表中
   - 准确跟踪输入和输出的数据类型和形状，确保连接的算子间数据类型和形状兼容

6. 你需要生成完整的IR JSON模型描述，每个模型描述需要包含以下内容：
   - 适当的Opset版本（通常与算子支持版本一致）
   - 和用例要求相关的Case_Name和Case_Purpose，名称需要反映测试内容
   - 模型的Model_Inputs和Model_Outputs正确对应模型中的节点
   - 完整的Nodes数组，包含所需的输入、输出和属性设置

7. IR JSON格式要求：
# IR JSON格式要求

IR JSON格式是一个标准化的模型描述格式，用于描述ONNX算子的测试用例。每个测试用例必须包含以下字段：

## 必需字段

1. Case_Name: 测试用例的名称，应该简洁明确地描述测试内容
2. Case_Purpose: 测试用例的目的，使用中文描述具体要测试的内容
3. Opset: ONNX算子集版本号，通常与算子支持的版本一致
4. Model_Inputs: 模型的输入名集合，List格式，和模型的首层算子输入名对应
5. Model_Outputs: 模型的输出名集合，List格式，和模型的尾层算子输出名对应
6. Nodes: 节点列表，描述算子的具体配置，包含：
   - Node_Name: 节点名称
   - Op_Type: 算子类型
   - Inputs: list，输入列表
   - Outputs: list，输出列表
   - Shape: string，"1,3,224,224"，数据的shape
   - Data_Format: string，在线Online，离线Offline
   - Data_Range: list，[min，max]，数据范围
   - Data_Value: list，[1, 2, 3, ...]，数据值
   - Attributes: 属性列表（如果有）

## 格式示例，下面展示了Conv算子接BN算子的模型描述的IR Json

```json
{
    "Case_Name": "Conv_BN_Test_Case",
    "Case_Purpose": "Test Conv with BatchNormalization with shape visualization",
    "Case_Category": "example",
    "Framework": "onnx",
    "Opset": 13,
    "Model_Inputs": ["data"],
    "Model_Outputs": ["prob"],
    "Nodes": [
        {
            "Node_Name": "conv1",
            "Op_Type": "Conv",
            "Inputs": [
                {
                    "Name": "data",
                    "Shape": "1,3,224,224",
                    "Data_Type": "float32",
                    "Data_Format": "Online",
                    "Data_Range": [-1, 1]
                },
                {
                    "Name": "W_conv",
                    "Shape": "64,3,7,7",
                    "Data_Type": "float32",
                    "Data_Format": "Offline",
                    "Data_Range": [-0.1, 0.1]
                },
                {
                    "Name": "B_conv",
                    "Shape": "64",
                    "Data_Type": "float32",
                    "Data_Format": "Offline",
                    "Data_Range": [0, 0.01]
                }
            ],
            "Outputs": [
                {
                    "Name": "conv1_output",
                    "Shape": "1,64,112,112",
                    "Data_Type": "float32"
                }
            ],
            "Attributes": [
                {
                    "Name": "kernel_shape",
                    "Data_Type": "int64",
                    "Data_Value": [7, 7]
                },
                {
                    "Name": "strides",
                    "Data_Type": "int64",
                    "Data_Value": [2, 2]
                },
                {
                    "Name": "pads",
                    "Data_Type": "int64",
                    "Data_Value": [3, 3, 3, 3]
                },
                {
                    "Name": "dilations",
                    "Type": "int64",
                    "Data_Value": [1, 1]
                },
                {
                    "Name": "group",
                    "Type": "int64",
                    "Data_Value": 1
                }
            ]
        },
        {
            "Node_Name": "bn1",
            "Op_Type": "BatchNormalization",
            "Inputs": [
                {
                    "Name": "conv1_output",
                    "Shape": "1,64,112,112",
                    "Data_Type": "float32",
                    "Data_Format": "Online"
                },
                {
                    "Name": "bn_scale",
                    "Shape": "64",
                    "Data_Type": "float32",
                    "Data_Format": "Offline",
                    "Data_Range": [0.9, 1.1]
                },
                {
                    "Name": "bn_B",
                    "Shape": "64",
                    "Data_Type": "float32",
                    "Data_Format": "Offline",
                    "Data_Range": [0, 0.01]
                },
                {
                    "Name": "bn_mean",
                    "Shape": "64",
                    "Data_Type": "float32",
                    "Data_Format": "Offline",
                    "Data_Range": [0, 0.01]
                },
                {
                    "Name": "bn_var",
                    "Shape": "64",
                    "Data_Type": "float32",
                    "Data_Format": "Offline",
                    "Data_Range": [0.9, 1.1]
                }
            ],
            "Outputs": [
                {
                    "Name": "prob",
                    "Shape": "1,64,112,112",
                    "Data_Type": "float32"
                }
            ],
            "Attributes": [
                {
                    "Name": "epsilon",
                    "Data_Type": "float32",
                    "Data_Value": 1e-5
                },
                {
                    "Name": "momentum",
                    "Data_Type": "float32",
                    "Data_Value": 0.9
                }
            ]
        }
    ]
}  
```

## 注意事项

1. 所有字段名称必须严格按照上述格式，区分大小写
2. 数据类型必须使用标准的ONNX类型名称，使用opset13定义的算子参数和属性
3. 需要根据每个节点的输入shape和算子本身的计算规则推理并设置正确的shape，避免onnx推理出现Incompatible dimensions
4. 节点的inputs和outputs必须与Model_Inputs和Model_Outputs中的name对应
5. 如果算子有属性参数，必须在attributes中完整指定
6. 多个算子级联，后一个算子的输入要和前一个算子的输出名称保持一致，并且Data_Format设置为在线数据
7. 输出不设置Data_Format
8. 对于离线数据，可以通过Data_Value字段提供具体的数值

- 参考IR JSON格式要求中的格式样例进行生成，要求之外的参数和内容不要生成
- 格式要求中的参数和内容必须生成，不要遗漏
请直接只输出JSON相关内容，不需要多余的注释和说明，以"用例IR JSON如下"开头，以"JSON输出完毕"结束。确保JSON格式正确，可以直接被解析。 '''

payload = {
    "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "stream": False,
    "max_tokens": 8192,
    "thinking_budget": 4096,
    "min_p": 0.05,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "stop": [],
    "messages": [
        {
            "role": "user",
            "content": f"{prompt}"
        }
    ]
}
headers = {
    "Authorization": "Bearer sk-shfdyfflywfqrbpdmitynbzxygnhezpajjelataqjowxrqlp",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)
data = response.json()
content = data["choices"][0]["message"]["content"]
# print(response.text)
with open("response.txt", "w", encoding="utf-8") as file:
    file.write(response.text)

with open("content.txt", "w", encoding="utf-8") as file:
    file.write(content)