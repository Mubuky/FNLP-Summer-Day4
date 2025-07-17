# Qwen3-8B 特殊Token集成项目

本项目实现了为 Qwen3-8B 模型添加特殊Token，并通过System Prompt设计使模型生成包含这些特殊Token的输出。

## 项目概述

本项目包含两个主要任务：

1. **任务一 (hw3_1.py)**: 为 Qwen3-8B 添加特殊Token并进行文本编码
2. **任务二 (hw3_2.py)**: 设计System Prompt使模型生成包含特殊Token的输出

## 特殊Token说明

项目添加了两个特殊Token：
- `<|AGENT|>` - 代理模式标识符，用于调试分析场景
- `<|EDIT|>` - 编辑模式标识符，用于直接修复场景

## 文件结构

```
├── hw3_1.py                    # 任务一：添加特殊Token并编码
├── hw3_2.py                    # 任务二：System Prompt设计和生成
├── query_and_output.json       # 输入数据（包含Query和期望Output）
├── query_only.json            # 查询数据（仅包含Query）
├── hw3_1.json                 # 任务一输出结果
├── hw3_2.json                 # 任务二输出结果
├── output_checker.py          # 输出格式检查工具
├── tokenizer_with_special_tokens/  # 保存的带特殊Token的Tokenizer
├── data_constructor.py        # 训练数据构造工具（重构版）
├── batch_validator.py         # 批量数据验证工具
├── test_example.py           # 原版本工具演示脚本
├── test_new_constructor.py   # 新版本测试脚本（新增）
├── TRAINING_DATA_GUIDE.md    # 训练数据构造详细指南（更新）
├── UPGRADE_NOTES.md          # 版本升级说明（新增）
└── README.md                  # 项目说明文档
```

## 环境要求

```bash
# 依赖库
transformers
vllm
torch
json
```

## 任务一：特殊Token集成与编码

### 功能说明

`hw3_1.py` 实现以下功能：

1. **加载基础Tokenizer**: 从 Qwen3-8B 模型加载原始tokenizer
2. **添加特殊Token**: 将 `<|AGENT|>` 和 `<|EDIT|>` 添加为特殊token
3. **保存修改后的Tokenizer**: 保存到 `./tokenizer_with_special_tokens/` 目录
4. **文本编码**: 读取 `query_and_output.json` 并进行编码
5. **生成输出**: 将结果保存到 `hw3_1.json`

### 输出格式

```json
{
  "special_tokens": [
    {
      "token": "<|AGENT|>",
      "id": token_id
    },
    {
      "token": "<|EDIT|>", 
      "id": token_id
    }
  ],
  "tasks": [
    {
      "text": "合并后的Query+Output文本",
      "token_ids": [token_id_list],
      "decoded_text": "解码验证文本"
    }
  ]
}
```

### 运行方式

```bash
python hw3_1.py
```

## 任务二：System Prompt设计

### 功能说明

`hw3_2.py` 实现以下功能：

1. **加载修改后的Tokenizer**: 使用任务一保存的tokenizer
2. **初始化vLLM引擎**: 配置并初始化推理引擎
3. **System Prompt设计**: 设计让模型生成特殊token的提示词
4. **批量推理**: 处理所有查询并生成包含特殊token的输出
5. **结果保存**: 将输出保存到 `hw3_2.json`

### System Prompt策略

项目采用**模式选择策略**：

#### 代理模式 (`<|AGENT|>`)
- **适用场景**: 用户没有提供具体错误信息，需要分析调试
- **输出格式**:
```
<think> 分析用户问题，判断需要调试分析的原因 </think>
<|AGENT|>
我会使用代理模式进行处理{"name": "python", "arguments": {"code": "用户的代码"}}
```

#### 编辑模式 (`<|EDIT|>`)
- **适用场景**: 用户提供了明确错误信息，可以直接修复
- **输出格式**:
```
<think> 分析具体错误信息，确定修复方案 </think>
<|EDIT|>
我会使用编辑模式修复问题{"name": "editor", "arguments": {"original_code": "原始代码", "modified_code": "修复后的代码"}}
```

### 工具定义

项目定义了两个函数工具：

1. **python**: 执行Python代码进行调试分析
2. **editor**: 比较和合并代码修改

### 运行方式

```bash
python hw3_2.py
```

**注意**: 初始化vLLM引擎可能需要几分钟时间，请耐心等待。

## 输出检查

使用 `output_checker.py` 检查任务二的输出格式：

```bash
# 检查默认文件 hw3_2.json
python output_checker.py

# 检查指定文件
python output_checker.py [文件路径]
```

### 检查项目

1. 是否包含 `<think>` 部分
2. 除think外是否含有特殊词符 `<|EDIT|>` 或 `<|AGENT|>`
3. `<|AGENT|>` 后是否正确调用 `python` 函数
4. `<|EDIT|>` 后是否调用 `editor` 函数

## 技术特点

### 任务一技术要点

- **特殊Token添加**: 使用 `add_special_tokens()` 方法安全添加
- **Tokenizer保存**: 完整保存包括配置文件的tokenizer
- **编码验证**: 通过编码-解码循环验证正确性
- **详细输出**: 提供token级别的详细信息

### 任务二技术要点

- **vLLM优化**: 使用GPU内存优化和eager模式
- **批量处理**: 一次性处理所有查询提高效率
- **Chat Template**: 使用Qwen格式的对话模板
- **采样参数**: 合理配置temperature和top_p参数

## 性能说明

- **任务一**: 主要为I/O操作，处理速度快
- **任务二**: 依赖GPU推理，批量处理提高效率
- **内存使用**: vLLM配置为使用80%GPU内存

## 注意事项

1. **模型路径**: 确保 `/home/share/models/Qwen3-8B` 路径存在
2. **GPU要求**: 任务二需要足够的GPU内存运行Qwen3-8B
3. **特殊Token**: 由于模型未经训练，完全使用prompt方式可能无法完全按预期输出
4. **文件编码**: 所有JSON文件使用UTF-8编码

## 预期结果

- **任务一**: 成功添加特殊token并正确编码所有文本
- **任务二**: 尽可能多地在输出中生成包含 `<|AGENT|>` 或 `<|EDIT|>` 的结果

由于模型没有经过专门训练，任务二的完成度可能不是100%，这是正常现象。

## 训练数据构造工具（新增）

为了提高模型生成特殊token的能力，项目新增了完整的训练数据构造工具链：

### 工具概述

1. **`data_constructor.py`** - 使用GPT-4o多线程构造符合格式要求的训练数据
2. **`batch_validator.py`** - 批量验证数据质量并过滤有效数据
3. **`test_example.py`** - 工具演示和测试脚本

### 快速开始

```bash
# 1. 设置OpenAI API Key
export OPENAI_API_KEY="your-api-key-here"

# 2. 测试新版本工具（推荐）
python test_new_constructor.py

# 3. 生成训练数据（基于parquet数据）
python data_constructor.py --samples 100 --threads 5

# 4. 验证数据质量
python batch_validator.py training_data_from_parquet.json

# 5. 运行完整演示
python test_example.py
```

### 输出文件

- `training_data_from_parquet.json` - 原始构造数据（包含问题来源信息）
- `training_data_from_parquet_alpaca.json` - Alpaca格式的有效数据（用于微调）
- `training_data_from_parquet_analysis.txt` - 数据质量分析报告（包含问题来源统计）

### 数据格式要求

训练数据必须符合以下格式：

1. **包含`<think>`部分**：分析用户问题
2. **包含特殊Token**：`<|AGENT|>` 或 `<|EDIT|>`
3. **正确的函数调用**：
   - `<|AGENT|>` 后调用 `python` 函数
   - `<|EDIT|>` 后调用 `editor` 函数

### 详细说明

详细的使用指南请参考 `TRAINING_DATA_GUIDE.md`。 