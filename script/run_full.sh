#!/bin/bash

# 全量生成脚本 - 生成全部128个问题的训练数据
# 用于正式的大规模数据生成

echo "🚀 全量生成 - 生成128个训练样本"
echo "================================="

# 检查环境
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 错误: 请设置 OPENAI_API_KEY 环境变量"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# 检查数据文件
if [ ! -f "data/test-00000-of-00001.parquet" ]; then
    echo "❌ 错误: 找不到数据文件 data/test-00000-of-00001.parquet"
    exit 1
fi

# 询问确认
echo "⚠️  注意: 将生成128个样本，可能需要较长时间和API费用"
read -p "是否继续? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "已取消操作"
    exit 0
fi

# 生成数据
echo "🤖 开始全量生成数据..."
echo "   样本数: 128"
echo "   线程数: 5"
echo "   输出文件: training_data_full_128.json"

python3 data_constructor.py \
    --samples 128 \
    --threads 5 \
    --output training_data_full_128.json

# 验证数据
if [ $? -eq 0 ] && [ -f "training_data_full_128.json" ]; then
    echo "✅ 数据生成成功！"
    echo "📊 验证数据质量..."
    python3 batch_validator.py training_data_full_128.json
    
    echo ""
    echo "📁 生成文件: training_data_full_128.json"
    echo "📊 数据统计:"
    wc -l training_data_full_128.json | awk '{print "   总行数: " $1}'
    ls -lh training_data_full_128.json | awk '{print "   文件大小: " $5}'
    
    echo ""
    echo "🎯 后续步骤:"
    echo "   1. 检查数据质量报告"
    echo "   2. 转换为alpaca格式进行微调"
    echo "   3. 备份生成的数据文件"
    echo "✨ 全量生成完成！"
else
    echo "❌ 数据生成失败"
    exit 1
fi 