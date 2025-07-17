#!/bin/bash

# 特殊Token训练数据构造工具 - 快速开始脚本

echo "🚀 特殊Token训练数据构造工具 - 快速开始"
echo "=================================================="

# 检查Python环境
echo "🔍 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3.x"
    exit 1
fi

echo "✅ Python环境检查通过"

# 检查必要的工具文件
echo "🔍 检查工具文件..."
required_files=("data_constructor.py" "batch_validator.py" "output_checker.py" "test_example.py")
missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -ne 0 ]; then
    echo "❌ 错误: 缺少必要的工具文件: ${missing_files[*]}"
    exit 1
fi

echo "✅ 工具文件检查通过"

# 检查OpenAI API Key
echo "🔍 检查OpenAI API Key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  警告: 未设置OPENAI_API_KEY环境变量"
    echo "   请运行: export OPENAI_API_KEY='your-api-key-here'"
    echo "   跳过API相关功能，仅演示验证工具..."
    api_available=false
else
    echo "✅ OpenAI API Key已设置"
    api_available=true
fi

# 检查并安装依赖
echo "🔍 检查Python依赖..."
python3 -c "import openai" 2>/dev/null
if [ $? -ne 0 ] && [ "$api_available" = true ]; then
    echo "📦 安装openai库..."
    pip3 install openai
fi

echo "✅ 依赖检查完成"

# 步骤1: 运行演示脚本
echo ""
echo "📝 步骤1: 运行工具演示"
echo "========================="
python3 test_example.py

if [ $? -ne 0 ]; then
    echo "❌ 演示脚本运行失败"
    exit 1
fi

# 步骤2: 验证生成的示例文件
echo ""
echo "🔍 步骤2: 验证示例数据"
echo "======================"

# 检查是否生成了示例文件
if [ -f "sample_constructor_data.json" ]; then
    echo "📊 使用batch_validator验证constructor格式数据..."
    python3 batch_validator.py sample_constructor_data.json
    echo ""
fi

if [ -f "sample_hw3_data.json" ]; then
    echo "📊 使用output_checker验证hw3格式数据..."
    python3 output_checker.py sample_hw3_data.json
    echo ""
fi

# 步骤3: 如果有API key，运行小规模数据生成测试
if [ "$api_available" = true ]; then
    echo ""
    echo "🤖 步骤3: 测试数据生成（小规模）"
    echo "================================"
    echo "正在生成10个测试样本..."
    
    python3 data_constructor.py --samples 10 --threads 2 --output test_generation_parquet.json
    
    if [ $? -eq 0 ] && [ -f "test_generation_parquet.json" ]; then
        echo "✅ 数据生成测试成功！"
        echo "📊 验证生成的数据..."
        python3 batch_validator.py test_generation_parquet.json
    else
        echo "❌ 数据生成测试失败"
    fi
else
    echo ""
    echo "⏭️  步骤3: 跳过数据生成测试（未设置API Key）"
    echo "==========================================="
    echo "要测试数据生成功能，请："
    echo "1. 设置API Key: export OPENAI_API_KEY='your-key'"
    echo "2. 运行: python3 data_constructor.py --samples 10 --threads 2"
fi

# 总结
echo ""
echo "📋 快速开始完成！"
echo "=================="
echo "🎯 已完成的步骤："
echo "   ✅ 环境检查"
echo "   ✅ 工具演示"
echo "   ✅ 数据验证测试"
if [ "$api_available" = true ]; then
    echo "   ✅ 数据生成测试"
else
    echo "   ⏭️  数据生成测试（跳过）"
fi

echo ""
echo "📁 生成的文件："
ls -la sample_*.json test_*.json 2>/dev/null | sed 's/^/   /'

echo ""
echo "🔧 下一步建议："
if [ "$api_available" = true ]; then
    echo "   1. 扩大规模生成数据: python3 data_constructor.py --samples 500"
    echo "   2. 验证数据质量: python3 batch_validator.py training_data_from_parquet.json"
    echo "   3. 使用Alpaca格式数据进行模型微调"
else
    echo "   1. 设置OpenAI API Key"
    echo "   2. 运行数据生成: python3 data_constructor.py --samples 100"
    echo "   3. 验证和过滤数据"
fi
echo "   4. 查看详细文档: cat TRAINING_DATA_GUIDE.md"

echo ""
echo "✨ 工具链使用就绪！祝您微调顺利！" 