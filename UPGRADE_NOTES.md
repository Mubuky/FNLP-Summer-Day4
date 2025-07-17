# 训练数据构造工具升级说明

## 🆕 新版本 v2.0 - 基于Parquet数据的智能构造

### 主要改进

#### 1. 🎯 真实数据驱动
- **原版本**: 使用预定义的代码模板和问题模板
- **新版本**: 基于`data/test-00000-of-00001.parquet`中的128个真实编程问题
- **优势**: 更真实、更多样化的问题源，提高训练数据质量

#### 2. 🤖 三阶段智能生成
- **阶段1**: 从parquet文件解析真实编程问题
- **阶段2**: 使用GPT-4.1生成包含小错误的代码
- **阶段3**: 智能包装为Agent/Edit模式的instruction
- **阶段4**: 生成符合格式要求的特殊token输出

#### 3. 🔧 更智能的错误注入
- **原版本**: 使用固定的错误代码片段
- **新版本**: GPT-4.1根据具体问题动态生成有针对性的错误代码
- **错误类型**: 逻辑错误、边界条件错误、算法实现错误等

#### 4. 📊 增强的数据追踪
- 新增 `question_id` 和 `question_title` 字段
- 新增 `buggy_code` 字段记录生成的错误代码
- 分析报告包含问题来源统计

## 🛠️ 技术改进

### API调用优化
- **延迟初始化**: OpenAI客户端只在需要时创建，支持无API Key的测试
- **更好的错误处理**: 改进的重试机制和空值检查
- **类型安全**: 修复了所有类型检查错误

### 性能调整
- **默认参数**: 样本数从1000调整为100，线程数从10调整为32
- **循环使用**: 支持生成超过128个样本（循环使用parquet问题）
- **内存效率**: 更高效的数据处理流程

## 📁 文件变化

### 新增文件
- `test_new_constructor.py` - 新版本测试脚本
- `UPGRADE_NOTES.md` - 本升级说明文档

### 修改文件
- `data_constructor.py` - 完全重构，实现基于parquet的生成流程
- `TRAINING_DATA_GUIDE.md` - 更新使用指南
- `README.md` - 更新快速开始和文件说明
- `quick_start.sh` - 更新脚本以支持新版本

### 输出文件变化
- `training_data.json` → `training_data_from_parquet.json`
- `training_data_alpaca.json` → `training_data_from_parquet_alpaca.json`
- `training_data_analysis.txt` → `training_data_from_parquet_analysis.txt`

## 🚀 使用变化

### 命令行参数
```bash
# 原版本
python data_constructor.py --samples 1000 --threads 10

# 新版本（推荐参数）
python data_constructor.py --samples 100 --threads 32
```

### 前置条件
```bash
# 新增依赖检查
pip install pandas  # 用于读取parquet文件

# 新增数据文件要求
# 确保 data/test-00000-of-00001.parquet 文件存在
```

### 测试流程
```bash
# 新版本测试（推荐首先运行）
python test_new_constructor.py

# 原版本测试
python test_example.py
```

## 📈 质量提升

### 数据多样性
- **128个不同的编程问题**: 涵盖算法、数据结构、数学等多个领域
- **动态错误生成**: 每次运行生成不同的错误代码
- **智能模式选择**: Agent/Edit模式的合理分配

### 格式一致性
- **严格验证**: 每个生成的输出都经过格式验证
- **重试机制**: 格式不正确时自动重试
- **详细报告**: 提供问题来源和质量统计

### 可扩展性
- **循环使用**: 支持生成任意数量的样本
- **多线程优化**: 支持高效的并发生成
- **错误恢复**: 单个失败不影响整体进程

## 🔄 迁移指南

### 对于新用户
直接使用新版本：
```bash
python test_new_constructor.py  # 测试
python data_constructor.py --samples 50  # 小规模试用
```

### 对于现有用户
1. **备份现有数据**
2. **安装新依赖**: `pip install pandas`
3. **确保parquet文件存在**: `data/test-00000-of-00001.parquet`
4. **运行新版本测试**: `python test_new_constructor.py`
5. **更新脚本**: 使用新的输出文件名

### 兼容性说明
- **batch_validator.py**: 完全兼容新旧版本数据格式
- **output_checker.py**: 无变化，继续支持hw3_2.json格式
- **现有alpaca数据**: 格式保持一致，可以直接使用

## 🎯 性能对比

| 指标 | 原版本 | 新版本 | 改进 |
|------|--------|--------|------|
| 数据源 | 固定模板 | 128个真实问题 | ⬆️ 质量提升 |
| 错误代码 | 预定义片段 | GPT-4.1动态生成 | ⬆️ 多样性提升 |
| 默认样本数 | 1000 | 100 | ⬇️ 成本降低 |
| 默认线程数 | 10 | 32 | ⬆️ 并发性能提升 |
| 类型安全 | 部分 | 完全 | ⬆️ 稳定性提升 |
| 测试覆盖 | 基础 | 全面 | ⬆️ 可靠性提升 |

## 🔮 未来计划

1. **多语言支持**: 扩展到JavaScript、Java等其他编程语言
2. **更多数据源**: 支持其他格式的编程问题数据
3. **质量优化**: 基于使用反馈进一步优化生成质量
4. **自动评估**: 集成自动化的数据质量评估指标

---

**总结**: 新版本通过引入真实编程问题数据和智能生成流程，显著提升了训练数据的质量和多样性，为特殊Token模型微调提供了更可靠的数据基础。 