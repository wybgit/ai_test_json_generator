# IR JSON格式要求

IR JSON格式是一个标准化的模型描述格式，用于描述ONNX算子的测试用例。每个测试用例必须包含以下字段：

## 必需字段

1. Case_Name: 测试用例的名称，应该简洁明确地描述测试内容
2. Case_Purpose: 测试用例的目的，使用中文描述具体要测试的内容
3. Opset_Version: ONNX算子集版本号，通常与算子支持的版本一致
4. Model_Inputs: 模型的输入名集合，List格式，和模型的首层算子输入名对应
5. Model_Outputs: 模型的输出名集合，List格式，和模型的尾层算子输出名对应
6. Nodes: 节点列表，描述算子的具体配置，包含：
   - name: 节点名称
   - op_type: 算子类型
   - inputs: 输入列表
   - outputs: 输出列表
   - attributes: 属性列表（如果有）

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
                    "Type": "int64",
                    "Value": [7, 7]
                },
                {
                    "Name": "strides",
                    "Type": "int64",
                    "Value": [2, 2]
                },
                {
                    "Name": "pads",
                    "Type": "int64",
                    "Value": [3, 3, 3, 3]
                },
                {
                    "Name": "dilations",
                    "Type": "int64",
                    "Value": [1, 1]
                },
                {
                    "Name": "group",
                    "Type": "int64",
                    "Value": 1
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
                    "DATA_Type": "float32",
                    "Data_Value": 1e-5
                },
                {
                    "Name": "momentum",
                    "DATA_Type": "float32",
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
3. 需要根据每个节点的输入shape和算子本身的计算规则推理并设置正确的shape，避免onnx推理出现Incompatible dimensions；shape必须使用数组格式，即使是标量也要用数组表示
4. 节点的inputs和outputs必须与Model_Inputs和Model_Outputs中的name对应
5. 如果算子有属性参数，必须在attributes中完整指定
6. 多个算子级联，后一个算子的输入要和前一个算子的输出名称保持一致，并且Data_Format设置为在线数据
7. 输出不设置Data_Format
8. 对于离线数据，可以通过Data_Value字段提供具体的数值