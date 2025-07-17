# 训练数据生成脚本

本目录包含两个简洁的脚本，用于生成Qwen3-8B特殊token训练数据。

## 脚本说明

### 1. `test_small.sh` - 小批量测试脚本
- **用途**: 快速测试和验证工具链
- **生成样本**: 10个问题
- **线程数**: 2
- **输出文件**: `test_small_10.json`
- **适用场景**: 开发测试、功能验证

### 2. `run_full.sh` - 全量生成脚本  
- **用途**: 正式的大规模数据生成
- **生成样本**: 128个问题（全部）
- **线程数**: 5
- **输出文件**: `training_data_full_128.json`
- **适用场景**: 正式训练数据生成

## 使用方法

### 准备工作
```bash
# 设置OpenAI API Key
export OPENAI_API_KEY='your-api-key-here'

# 确保在项目根目录
cd /home/mzli/day-3
```

### 运行小批量测试
```bash
./script/test_small.sh
```

### 运行全量生成
```bash
./script/run_full.sh
```

## 输出文件

- **test_small_10.json**: 小批量测试生成的10个样本
- **training_data_full_128.json**: 全量生成的128个样本

两个文件都是标准的Alpaca格式，可直接用于模型微调。

## 注意事项

1. **API费用**: 全量生成需要调用128次GPT-4o，请注意API使用费用
2. **运行时间**: 全量生成可能需要5-15分钟，取决于网络和API响应速度
3. **数据验证**: 脚本会自动运行 `batch_validator.py` 验证生成数据的质量
4. **错误处理**: 脚本包含完整的错误检查和友好的提示信息 