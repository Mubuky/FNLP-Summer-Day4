#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_constructor.py - 使用GPT-4.1构造符合特殊token格式的训练数据 (基于parquet数据)

新的构造流程：
1. 从parquet文件读取编程问题
2. 使用GPT-4.1生成有小错误的代码
3. 根据需求(Agent/Edit)包装成instruction
4. 使用GPT-4.1生成包含特殊token的output
"""

import os
import json
import time
import random
import re
import threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple, Optional
import openai
from openai import OpenAI

# 设置OpenAI API (延迟初始化)
client = None

def get_openai_client():
    """获取OpenAI客户端，延迟初始化"""
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("请设置 OPENAI_API_KEY 环境变量")
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.chatanywhere.tech/v1"
        )
    return client

# 数据文件路径
PARQUET_FILE = "data/test-00000-of-00001.parquet"

def extract_think_content(output: str) -> Tuple[str, str]:
    """提取 think 部分和非 think 部分的内容"""
    think_pattern = r'<think>(.*?)</think>'
    think_matches = re.findall(think_pattern, output, re.DOTALL)
    think_content = '\n'.join(think_matches) if think_matches else ''
    non_think_content = re.sub(think_pattern, '', output, flags=re.DOTALL).strip()
    return think_content, non_think_content

def check_special_markers(non_think_content: str) -> Tuple[bool, str]:
    """检查是否包含特殊词符"""
    if '<|EDIT|>' in non_think_content:
        return True, 'EDIT'
    elif '<|AGENT|>' in non_think_content:
        return True, 'AGENT'
    else:
        return False, 'NONE'

def check_function_call(content: str, expected_function: str) -> bool:
    """检查是否正确调用了指定的函数"""
    function_call_pattern = r'{\s*"name"\s*:\s*"([^"]+)"'
    matches = re.findall(function_call_pattern, content)
    return expected_function in matches

def validate_output(output: str) -> Tuple[bool, List[str]]:
    """验证输出是否符合格式要求"""
    issues = []
    
    # 检查think部分
    think_content, non_think_content = extract_think_content(output)
    if not think_content.strip():
        issues.append('缺少 <think> 部分')
    
    # 检查特殊词符
    has_marker, marker_type = check_special_markers(non_think_content)
    if not has_marker:
        issues.append('缺少特殊词符 <|EDIT|> 或 <|AGENT|>')
        return False, issues
    
    # 检查函数调用
    if marker_type == 'AGENT':
        if not check_function_call(non_think_content, 'python'):
            issues.append('<|AGENT|> 后未正确调用 python 函数')
    elif marker_type == 'EDIT':
        if not check_function_call(non_think_content, 'editor'):
            issues.append('<|EDIT|> 后未正确调用 editor 函数')
    
    return len(issues) == 0, issues

def load_programming_problems(parquet_path: str) -> List[Dict]:
    """从parquet文件加载编程问题"""
    try:
        df = pd.read_parquet(parquet_path)
        problems = []
        
        for _, row in df.iterrows():
            # 提取问题内容 - turns可能是numpy数组
            turns = row['turns']
            if turns is not None and hasattr(turns, '__len__') and len(turns) > 0:
                problem_text = turns[0]
                
                # 清理问题文本，提取核心问题描述
                problem_desc = extract_problem_description(problem_text)
                
                problems.append({
                    'question_id': row['question_id'],
                    'question_title': row['question_title'],
                    'problem_description': problem_desc,
                    'original_text': problem_text
                })
        
        print(f"✅ 成功加载 {len(problems)} 个编程问题")
        return problems
        
    except Exception as e:
        print(f"❌ 加载parquet文件失败: {e}")
        return []

def extract_problem_description(problem_text: str) -> str:
    """从完整问题文本中提取核心问题描述"""
    # 移除指令部分
    lines = problem_text.split('\n')
    description_lines = []
    in_description = False
    
    for line in lines:
        if '### Question:' in line:
            in_description = True
            continue
        elif line.startswith('###') and in_description:
            break
        elif in_description:
            description_lines.append(line)
    
    description = '\n'.join(description_lines).strip()
    
    # 如果没有找到问题描述，返回整个文本的前部分
    if not description:
        description = problem_text[:1000] + "..." if len(problem_text) > 1000 else problem_text
    
    return description

def generate_buggy_code(problem_desc: str, max_retries: int = 3) -> Optional[str]:
    """使用GPT-4.1生成包含小错误的代码"""
    prompt = f"""请根据以下编程问题，生成一个包含小错误的Python代码实现。

问题描述：
{problem_desc}

要求：
1. 代码应该看起来合理，但包含1-2个小bug
2. 错误可以是：逻辑错误、边界条件错误、语法小错误、算法实现错误等
3. 不要生成完全错误或无法理解的代码
4. 只返回Python代码，不要额外解释

代码格式：
```python
# 在这里写代码
```
"""

    for attempt in range(max_retries):
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                timeout=30
            )
            
            code_response = response.choices[0].message.content
            
            # 提取代码
            if code_response:
                code_match = re.search(r'```python\n(.*?)\n```', code_response, re.DOTALL)
                if code_match:
                    return code_match.group(1).strip()
                else:
                    # 如果没有代码块，尝试提取整个响应
                    return code_response.strip()
            else:
                return None
                
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ 生成错误代码失败: {e}")
                return None
            time.sleep(1)
    
    return None

def create_instruction(problem_desc: str, buggy_code: str, instruction_type: str) -> str:
    """根据需求类型创建instruction"""
    if instruction_type == "agent":
        # Agent模式 - 用户没有明确错误信息，需要调试分析
        templates = [
            f"这个Python代码运行结果不对，帮我看看哪里有问题：\n\n{buggy_code}",
            f"我的代码好像有bug，但找不出来：\n\n{buggy_code}",
            f"这个算法输出异常，能帮我调试吗？\n\n{buggy_code}",
            f"我写的代码逻辑不对，请帮我分析：\n\n{buggy_code}",
            f"这个程序有问题但我不确定哪里错了：\n\n{buggy_code}",
            f"我的代码总是报错，能帮我看看吗？\n\n{buggy_code}",
            f"这个函数返回值不正确，请帮我调试：\n\n{buggy_code}",
        ]
    else:  # edit模式
        # Edit模式 - 用户提供明确错误信息，需要直接修复
        error_types = [
            "IndexError: list index out of range",
            "TypeError: unsupported operand type(s)",
            "NameError: name 'variable' is not defined",
            "ValueError: invalid literal for int()",
            "AttributeError: object has no attribute",
            "KeyError: key not found in dictionary",
            "ZeroDivisionError: division by zero",
            "RecursionError: maximum recursion depth exceeded",
            "SyntaxError: invalid syntax",
            "IndentationError: expected an indented block"
        ]
        
        error_msg = random.choice(error_types)
        templates = [
            f"这个Python代码报错：{error_msg}，请帮我修复：\n\n{buggy_code}",
            f"我的代码出现{error_msg.split(':')[0]}错误，需要修复：\n\n{buggy_code}",
            f"运行这个代码时出现{error_msg}，请修复：\n\n{buggy_code}",
            f"这个代码有错误：{error_msg}：\n\n{buggy_code}",
        ]
    
    return random.choice(templates)

def generate_output_with_special_tokens(instruction: str, instruction_type: str, max_retries: int = 3) -> Optional[str]:
    """使用GPT-4.1生成包含特殊token的输出"""
    
    system_prompt = """你是一个专业的代码调试助手。请根据用户的问题类型选择合适的处理模式：

**处理模式规则：**

1. **代理模式 (<|AGENT|>)** - 当用户没有提供具体错误信息，需要分析调试时使用
2. **编辑模式 (<|EDIT|>)** - 当用户提供了明确错误信息，可以直接修复时使用

**输出格式要求：**

对于代理模式：
<think> 分析用户问题，判断需要调试分析的原因 </think>
<|AGENT|>
我会使用代理模式进行处理{"name": "python", "arguments": {"code": "用户的代码"}}

对于编辑模式：
<think> 分析具体错误信息，确定修复方案 </think>
<|EDIT|>
我会使用编辑模式修复问题{"name": "editor", "arguments": {"original_code": "原始代码", "modified_code": "修复后的代码"}}

请严格按照上述格式输出，确保包含<think>部分和相应的特殊词符 <|EDIT|> 或 <|AGENT|>。"""

    for attempt in range(max_retries):
        try:
            client = get_openai_client()
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": instruction}
                ],
                temperature=0.7,
                max_tokens=2048,
                timeout=30
            )
            
            output = response.choices[0].message.content
            
            # 验证输出格式
            if output:
                is_valid, issues = validate_output(output)
            else:
                is_valid, issues = False, ["API返回空内容"]
            
            if is_valid:
                return output
            else:
                # 如果格式不对，在最后一次尝试时也返回，供分析
                if attempt == max_retries - 1:
                    return output
                else:
                    continue  # 重试
                    
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ 生成输出失败: {e}")
                return None
            time.sleep(1)  # 重试前等待
    
    return None

def process_single_problem(problem: Dict, item_id: int) -> Optional[Dict]:
    """处理单个编程问题，生成完整的训练样本"""
    try:
        # 步骤1: 生成有错误的代码
        print(f"🔧 项目 {item_id}: 生成错误代码...")
        buggy_code = generate_buggy_code(problem['problem_description'])
        
        if not buggy_code:
            print(f"❌ 项目 {item_id}: 生成错误代码失败")
            return None
        
        # 步骤2: 随机选择instruction类型
        instruction_type = random.choice(['agent', 'edit'])
        
        # 步骤3: 创建instruction
        print(f"📝 项目 {item_id}: 创建{instruction_type}类型instruction...")
        instruction = create_instruction(
            problem['problem_description'], 
            buggy_code, 
            instruction_type
        )
        
        # 步骤4: 生成包含特殊token的输出
        print(f"🤖 项目 {item_id}: 生成特殊token输出...")
        output = generate_output_with_special_tokens(instruction, instruction_type)
        
        if not output:
            print(f"❌ 项目 {item_id}: 生成输出失败")
            return None
        
        # 验证最终输出
        if output:
            is_valid, issues = validate_output(output)
        else:
            is_valid, issues = False, ["生成输出为空"]
        
        result = {
            'item_id': item_id,
            'question_id': problem['question_id'],
            'question_title': problem['question_title'],
            'instruction': instruction,
            'output': output,
            'expected_type': instruction_type,
            'buggy_code': buggy_code,
            'valid': is_valid,
            'issues': issues
        }
        
        status = "✅ 有效" if is_valid else f"❌ 无效: {', '.join(issues)}"
        print(f"✓ 完成项目 {item_id}: {instruction_type.upper()} - {status}")
        
        return result
        
    except Exception as e:
        print(f"❌ 项目 {item_id} 处理失败: {e}")
        return None

def construct_training_data_from_parquet(
    num_samples: int = 100, 
    num_threads: int = 32, 
    output_file: str = "outputs/training_data/training_data_from_parquet.json"
) -> List[Dict]:
    """从parquet数据构造训练数据"""
    
    print(f"🚀 开始从parquet数据构造 {num_samples} 个训练样本...")
    print(f"🔧 使用 {num_threads} 个线程")
    print(f"📁 输出文件: {output_file}")
    print("=" * 50)
    
    # 加载编程问题
    problems = load_programming_problems(PARQUET_FILE)
    
    if not problems:
        print("❌ 无法加载编程问题，退出")
        return []
    
    # 如果请求的样本数超过可用问题数，就循环使用
    if num_samples > len(problems):
        print(f"⚠️  请求样本数({num_samples})超过可用问题数({len(problems)})，将循环使用问题")
    
    selected_problems = []
    for i in range(num_samples):
        problem_idx = i % len(problems)
        selected_problems.append(problems[problem_idx])
    
    results = []
    valid_count = 0
    invalid_count = 0
    
    # 使用线程池执行
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交任务
        future_to_id = {
            executor.submit(process_single_problem, problem, i): i 
            for i, problem in enumerate(selected_problems)
        }
        
        # 收集结果
        for future in as_completed(future_to_id):
            result = future.result()
            if result:
                results.append(result)
                if result["valid"]:
                    valid_count += 1
                else:
                    invalid_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 构造完成统计:")
    print(f"   总样本数: {len(results)}")
    print(f"   ✅ 有效样本: {valid_count}")
    print(f"   ❌ 无效样本: {invalid_count}")
    print(f"   📈 有效率: {valid_count/len(results)*100:.1f}%" if results else "0%")
    
    # 保存所有数据（包括无效的，供分析）
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"💾 原始数据已保存到: {output_file}")
    
    # 提取有效数据并转换为alpaca格式
    valid_data = [item for item in results if item["valid"]]
    alpaca_data = convert_to_alpaca_format(valid_data)
    
    # 确保目录存在
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    alpaca_file = output_file.replace('.json', '_alpaca.json')
    with open(alpaca_file, 'w', encoding='utf-8') as f:
        json.dump(alpaca_data, f, ensure_ascii=False, indent=2)
    
    print(f"📦 Alpaca格式数据已保存到: {alpaca_file}")
    
    # 生成分析报告（保存到reports目录）
    base_name = os.path.basename(output_file).replace('.json', '_analysis.txt')
    report_file = f"outputs/reports/{base_name}"
    os.makedirs("outputs/reports", exist_ok=True)
    generate_analysis_report(results, report_file)
    
    return results

def convert_to_alpaca_format(data: List[Dict]) -> List[Dict]:
    """转换为alpaca格式"""
    alpaca_data = []
    
    for item in data:
        alpaca_item = {
            "instruction": item["instruction"],
            "input": "",  # 我们的任务不需要额外input
            "output": item["output"]
        }
        alpaca_data.append(alpaca_item)
    
    return alpaca_data

def generate_analysis_report(results: List[Dict], report_file: str):
    """生成分析报告"""
    valid_results = [r for r in results if r["valid"]]
    invalid_results = [r for r in results if not r["valid"]]
    
    report = []
    report.append("=" * 60)
    report.append("基于Parquet数据的训练数据构造分析报告")
    report.append("=" * 60)
    report.append(f"总样本数: {len(results)}")
    report.append(f"有效样本: {len(valid_results)} ({len(valid_results)/len(results)*100:.1f}%)")
    report.append(f"无效样本: {len(invalid_results)} ({len(invalid_results)/len(results)*100:.1f}%)")
    report.append("")
    
    # 按类型统计
    type_stats = {}
    for result in valid_results:
        t = result["expected_type"]
        type_stats[t] = type_stats.get(t, 0) + 1
    
    report.append("有效样本类型分布:")
    for t, count in type_stats.items():
        report.append(f"  {t}: {count} ({count/len(valid_results)*100:.1f}%)")
    report.append("")
    
    # 无效样本问题分析
    if invalid_results:
        issue_stats = {}
        for result in invalid_results:
            for issue in result["issues"]:
                issue_stats[issue] = issue_stats.get(issue, 0) + 1
        
        report.append("无效样本问题统计:")
        for issue, count in sorted(issue_stats.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {issue}: {count}")
        report.append("")
    
    # 问题来源统计
    question_stats = {}
    for result in results:
        title = result.get("question_title", "unknown")
        question_stats[title] = question_stats.get(title, 0) + 1
    
    report.append(f"问题来源分布（前10个）:")
    for title, count in sorted(question_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        title_short = title[:50] + "..." if len(title) > 50 else title
        report.append(f"  {title_short}: {count}")
    report.append("")
    
    # 保存报告
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"📊 分析报告已保存到: {report_file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从parquet数据构造符合特殊token格式的训练数据')
    parser.add_argument('--samples', type=int, default=100, help='生成样本数量 (默认: 100)')
    parser.add_argument('--threads', type=int, default=32, help='线程数量 (默认: 32)')
    parser.add_argument('--output', type=str, default='outputs/training_data/training_data_from_parquet.json', 
                       help='输出文件名 (默认: outputs/training_data/training_data_from_parquet.json)')
    
    args = parser.parse_args()
    
    # 检查API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误: 请设置 OPENAI_API_KEY 环境变量")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # 检查parquet文件
    if not os.path.exists(PARQUET_FILE):
        print(f"❌ 错误: 找不到parquet文件 {PARQUET_FILE}")
        print("请确保数据文件存在")
        return
    
    # 检查pandas依赖
    try:
        import pandas as pd
    except ImportError:
        print("❌ 错误: 需要安装pandas库")
        print("   pip install pandas")
        return
    
    construct_training_data_from_parquet(
        num_samples=args.samples,
        num_threads=args.threads,
        output_file=args.output
    )

if __name__ == "__main__":
    main() 