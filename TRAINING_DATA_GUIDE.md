# 特殊Token训练数据构造指南（基于Parquet数据）

本指南介绍如何使用基于parquet数据的新版工具构造符合特殊Token格式要求的训练数据。

## 🆕 新版本特性

- **真实编程问题**: 基于`data/test-00000-of-00001.parquet`中的128个真实编程问题
- **三阶段生成**: 问题解析 → 错误代码生成 → instruction包装 → 特殊token输出
- **智能错误注入**: 使用GPT-4.1生成包含各种类型bug的代码
- **自适应instruction**: 根据Agent/Edit模式智能包装问题

## 工具概述

### 1. `data_constructor.py` - 数据构造工具（重构版）
- **功能**: 基于parquet数据使用GPT-4.1多线程生成训练数据
- **输入**: `data/test-00000-of-00001.parquet`（128个真实编程问题）
- **输出**: 原始数据 + Alpaca格式数据 + 分析报告
- **新特性**: 三阶段智能生成流程

### 2. `batch_validator.py` - 批量验证工具
- **功能**: 验证现有数据质量并过滤有效数据
- **输入**: JSON格式的数据文件
- **输出**: 有效数据(Alpaca格式) + 质量报告

### 3. `output_checker.py` - 单文件检查工具
- **功能**: 检查单个文件的输出格式
- **输入**: hw3_2.json格式的文件
- **输出**: 详细的检查报告

## 环境准备

### 1. 安装依赖

```bash
pip install openai
pip install pathlib
```

### 2. 设置OpenAI API Key

本项目使用ChatAnywhere作为OpenAI API的代理服务，提供更稳定的访问：

```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"

# Windows
set OPENAI_API_KEY=your-api-key-here
```

**注意**: 项目已配置使用 `api.chatanywhere.tech` 作为API端点，无需额外配置base_url。

## 新版本工作流程

### 三阶段智能生成流程

1. **阶段1: 问题解析**
   - 从parquet文件加载128个真实编程问题
   - 提取问题描述，清理格式
   - 循环使用问题支持大规模数据生成

2. **阶段2: 错误代码生成**
   - 使用GPT-4.1根据问题描述生成有小错误的Python代码
   - 错误类型包括：逻辑错误、边界条件错误、算法实现错误等
   - 确保代码看起来合理但包含1-2个可识别的bug

3. **阶段3: Instruction包装**
   - 随机选择Agent或Edit模式
   - Agent模式：包装为需要调试分析的问题
   - Edit模式：添加具体错误信息，包装为需要直接修复的问题

4. **阶段4: 特殊Token输出生成**
   - 使用GPT-4.1生成包含特殊token的标准格式输出
   - 自动验证输出格式的正确性
   - 重试机制确保生成质量

## 使用流程

### 步骤1: 构造训练数据

使用`data_constructor.py`生成大量训练数据：

```bash
# 基本使用 - 生成100个样本（新版默认值）
python data_constructor.py

# 自定义参数
python data_constructor.py --samples 500 --threads 32 --output outputs/training_data/my_training_data.json

# 参数说明：
# --samples: 生成样本数量 (默认100，将循环使用128个parquet问题)
# --threads: 线程数量 (默认32，建议根据API限制调整)
# --output: 输出文件名 (默认outputs/training_data/training_data_from_parquet.json)
```

**新版本输出文件：**
- `training_data_from_parquet.json` - 原始数据（包含buggy_code等详细信息）
- `training_data_from_parquet_alpaca.json` - 有效数据的Alpaca格式
- `training_data_from_parquet_analysis.txt` - 包含问题来源统计的分析报告

### 步骤2: 验证数据质量

使用`batch_validator.py`验证和过滤数据：

```bash
# 验证data_constructor生成的数据
python batch_validator.py training_data.json

# 验证hw3_2.json格式的数据
python batch_validator.py hw3_2.json --format hw3

# 自定义输出路径
python batch_validator.py outputs/training_data/data.json --output outputs/validation/filtered_data.json --report outputs/reports/quality_report.txt

# 保留无效数据用于分析
python batch_validator.py data.json --keep-invalid
```

**输出文件：**
- `*_valid_alpaca.json` - 过滤后的有效数据(Alpaca格式)
- `*_quality_report.txt` - 质量验证报告
- `*_invalid.json` - 无效数据(如使用--keep-invalid)

### 步骤3: 检查特定文件

使用`output_checker.py`检查hw3_2格式的文件：

```bash
# 检查默认文件
python output_checker.py

# 检查指定文件
python output_checker.py outputs/tasks/hw3_2.json

# 显示详细信息
python output_checker.py outputs/tasks/hw3_2.json -v
```

## 数据格式说明

### 输入格式

#### data_constructor格式（新版本）
```json
[
  {
    "item_id": 0,
    "question_id": "eecef5ebcd4b0224ec24...",
    "question_title": "leetcode_minimize-length-of-array-using-operations",
    "instruction": "这个Python代码运行结果不对，帮我看看哪里有问题：\n\ndef solution(nums):\n    ...",
    "output": "<think>...</think>\n<|AGENT|>\n我会使用代理模式进行处理{\"name\": \"python\", \"arguments\": {...}}",
    "expected_type": "agent|edit",
    "buggy_code": "def solution(nums):\n    # 生成的有错误的代码",
    "valid": true|false,
    "issues": ["问题列表"]
  }
]
```

#### hw3_2格式
```json
[
  {
    "Query": "用户的问题或指令", 
    "Output": "模型的回答"
  }
]
```

### 输出格式

#### Alpaca格式
```json
[
  {
    "instruction": "用户的问题或指令",
    "input": "",
    "output": "模型的回答"
  }
]
```

## 格式要求

训练数据必须符合以下格式要求：

### 1. 必须包含`<think>`部分
```
<think> 分析用户问题，判断处理方式 </think>
```

### 2. 必须包含特殊Token

**代理模式 (AGENT)**:
```
<|AGENT|>
我会使用代理模式进行处理{"name": "python", "arguments": {"code": "用户的代码"}}
```

**编辑模式 (EDIT)**:
```
<|EDIT|>
我会使用编辑模式修复问题{"name": "editor", "arguments": {"original_code": "原始代码", "modified_code": "修复后的代码"}}
```

### 3. 函数调用要求
- `<|AGENT|>`后必须调用`python`函数
- `<|EDIT|>`后必须调用`editor`函数
- 函数调用格式必须是有效的JSON

## 质量控制

### 数据验证标准

1. **✅ 有效数据标准**:
   - 包含`<think>`部分
   - 包含`<|AGENT|>`或`<|EDIT|>`特殊Token
   - 特殊Token后有正确的函数调用
   - JSON格式正确

2. **❌ 常见问题**:
   - 缺少`<think>`部分
   - 缺少特殊Token
   - 函数调用格式错误
   - 特殊Token与函数不匹配

### 提高数据质量的建议

1. **调整System Prompt**:
   - 在`data_constructor.py`中修改`create_system_prompt()`函数
   - 增加更多示例和约束

2. **扩展问题模板**:
   - 在`PROBLEM_TEMPLATES`中添加更多样化的模板
   - 增加不同编程语言和场景

3. **优化代码库**:
   - 在`CODE_SNIPPETS`中添加更多有代表性的代码示例
   - 包含更多类型的bug和错误

## 性能优化

### 1. 多线程配置
```bash
# 根据API限制调整线程数
python data_constructor.py --threads 16   # 保守设置  
python data_constructor.py --threads 32  # 标准设置
```

### 2. 批量处理
```bash
# 分批生成大量数据
python data_constructor.py --samples 500 --output outputs/training_data/batch1.json
python data_constructor.py --samples 500 --output outputs/training_data/batch2.json
python data_constructor.py --samples 500 --output outputs/training_data/batch3.json

# 合并验证
python batch_validator.py outputs/training_data/batch1.json
python batch_validator.py outputs/training_data/batch2.json
python batch_validator.py outputs/training_data/batch3.json
```

### 3. 错误处理
- 工具会自动重试API调用失败的请求
- 无效数据会被标记但不会中断处理
- 所有错误信息都会记录在分析报告中

## 成本估算

### OpenAI API成本
- GPT-4.1价格: ~$0.03/1K tokens (输出)
- 每个样本平均: ~500 tokens输出
- 1000个样本估算: ~$15-20

### 时间估算
- 32线程处理1000样本: ~5-15分钟
- 实际时间取决于API响应速度和网络状况

## 故障排除

### 常见问题

1. **API Key错误**:
   ```
   ❌ 错误: 请设置 OPENAI_API_KEY 环境变量
   ```
   **解决**: 确保正确设置环境变量

2. **API限制**:
   ```
   API调用失败: Rate limit exceeded
   ```
   **解决**: 适当减少线程数或增加重试间隔（如从32调整为16）

3. **格式验证失败**:
   ```
   ❌ 无效样本: 缺少特殊词符 <|EDIT|> 或 <|AGENT|>
   ```
   **解决**: 调整System Prompt或增加重试次数

4. **文件路径错误**:
   ```
   ❌ 错误: 文件不存在
   ```
   **解决**: 检查文件路径和权限

### 调试技巧

1. **查看详细日志**:
   ```bash
   python data_constructor.py --samples 10 --threads 1
   ```

2. **分析无效样本**:
   ```bash
   python batch_validator.py data.json --keep-invalid
   ```

3. **检查单个文件**:
   ```bash
   python output_checker.py outputs/tasks/hw3_2.json -v
   ```

## 最佳实践

1. **开始时小规模测试（新版本建议）**:
   ```bash
   # 先测试工具是否正常工作
   python test_new_constructor.py
   
   # 小规模生成测试
   python data_constructor.py --samples 20 --threads 8
   ```

2. **验证质量后扩大规模**:
   ```bash
   # 中等规模测试
   python data_constructor.py --samples 200 --threads 32
   
   # 大规模生成（充分利用128个问题）
   python data_constructor.py --samples 1000 --threads 32
   ```

3. **定期检查和过滤数据**:
   ```bash
   python batch_validator.py training_data.json
   ```

4. **保存多个版本**:
   ```bash
   python data_constructor.py --output outputs/training_data/version1.json
python data_constructor.py --output outputs/training_data/version2.json
   ```

5. **监控数据质量趋势**:
   - 比较不同批次的有效率
   - 分析无效样本的共同问题
   - 持续优化System Prompt

## 结果文件说明

生成的文件用途：

- **`*_alpaca.json`**: 用于模型微调的标准格式数据
- **`*_analysis.txt`**: 分析数据质量和问题分布
- **`*_quality_report.txt`**: 详细的验证报告
- **`*_invalid.json`**: 用于分析和改进的无效数据

这些工具为特殊Token模型微调提供了完整的数据构造和质量控制流程。 