#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_validator.py - 批量验证构造的训练数据质量

功能：
1. 批量验证数据格式
2. 过滤出符合要求的数据
3. 转换为alpaca格式
4. 生成质量报告
"""

import json
import re
import sys
import argparse
from typing import List, Dict, Tuple
from pathlib import Path

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

def check_function_call(content: str, expected_function: str) -> Tuple[bool, str]:
    """检查是否正确调用了指定的函数"""
    function_call_pattern = r'{\s*"name"\s*:\s*"([^"]+)"'
    matches = re.findall(function_call_pattern, content)
    
    if matches:
        for match in matches:
            if match == expected_function:
                return True, f"找到正确的{expected_function}函数调用"
        return False, f"找到函数调用但不是{expected_function}: {matches}"
    else:
        return False, f"未找到{expected_function}函数调用"

def validate_single_output(output: str, index: int) -> Dict:
    """验证单个输出项"""
    result = {
        'index': index,
        'has_think': False,
        'has_special_marker': False,
        'marker_type': 'NONE',
        'correct_function_call': False,
        'function_call_details': '',
        'issues': [],
        'valid': False
    }
    
    # 1. 检查是否包含 think 部分
    think_content, non_think_content = extract_think_content(output)
    result['has_think'] = bool(think_content.strip())
    
    if not result['has_think']:
        result['issues'].append('缺少 <think> 部分')
    
    # 2. 检查特殊词符
    has_marker, marker_type = check_special_markers(non_think_content)
    result['has_special_marker'] = has_marker
    result['marker_type'] = marker_type
    
    if not has_marker:
        result['issues'].append('缺少特殊词符 <|EDIT|> 或 <|AGENT|>')
    
    # 3. 根据标记类型检查函数调用
    if marker_type == 'AGENT':
        has_correct_call, details = check_function_call(non_think_content, 'python')
        result['correct_function_call'] = has_correct_call
        result['function_call_details'] = details
        
        if not has_correct_call:
            result['issues'].append('<|AGENT|> 后未正确调用 python 函数')
            
    elif marker_type == 'EDIT':
        has_correct_call, details = check_function_call(non_think_content, 'editor')
        result['correct_function_call'] = has_correct_call
        result['function_call_details'] = details
        
        if not has_correct_call:
            result['issues'].append('<|EDIT|> 后未正确调用 editor 函数')
    
    # 判断是否完全有效
    result['valid'] = len(result['issues']) == 0
    
    return result

def validate_data_file(input_file: str, output_format: str = 'auto') -> Dict:
    """验证数据文件"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {'error': f'文件未找到: {input_file}'}
    except json.JSONDecodeError as e:
        return {'error': f'JSON 解析错误: {e}'}
    
    if not isinstance(data, list):
        return {'error': '数据格式错误：应该是一个列表'}
    
    results = {
        'input_file': input_file,
        'total_items': len(data),
        'valid_items': 0,
        'invalid_items': 0,
        'validation_details': [],
        'valid_data': [],
        'invalid_data': [],
        'summary': {
            'missing_think': 0,
            'missing_markers': 0,
            'wrong_function_calls': 0,
            'agent_count': 0,
            'edit_count': 0
        }
    }
    
    for i, item in enumerate(data):
        # 自动检测数据格式
        if output_format == 'auto':
            if 'output' in item:  # data_constructor格式
                output_field = 'output'
                instruction_field = 'instruction'
            elif 'Output' in item:  # hw3_2格式
                output_field = 'Output'
                instruction_field = 'Query'
            else:
                results['validation_details'].append({
                    'index': i,
                    'error': '无法识别数据格式：缺少output/Output字段'
                })
                results['invalid_items'] += 1
                continue
        else:
            output_field = 'output' if output_format == 'constructor' else 'Output'
            instruction_field = 'instruction' if output_format == 'constructor' else 'Query'
        
        if not isinstance(item, dict) or output_field not in item:
            results['validation_details'].append({
                'index': i,
                'error': f'项目格式错误：缺少 {output_field} 字段'
            })
            results['invalid_items'] += 1
            results['invalid_data'].append(item)
            continue
        
        output_text = item[output_field]
        validation_result = validate_single_output(output_text, i)
        results['validation_details'].append(validation_result)
        
        # 统计
        if validation_result['valid']:
            results['valid_items'] += 1
            # 保存有效数据
            valid_item = {
                'instruction': item.get(instruction_field, ''),
                'output': output_text,
                'index': i
            }
            if 'expected_type' in item:
                valid_item['expected_type'] = item['expected_type']
            if 'language' in item:
                valid_item['language'] = item['language']
            
            results['valid_data'].append(valid_item)
            
            # 类型统计
            if validation_result['marker_type'] == 'AGENT':
                results['summary']['agent_count'] += 1
            elif validation_result['marker_type'] == 'EDIT':
                results['summary']['edit_count'] += 1
        else:
            results['invalid_items'] += 1
            results['invalid_data'].append(item)
            
            # 问题统计
            if not validation_result['has_think']:
                results['summary']['missing_think'] += 1
            if not validation_result['has_special_marker']:
                results['summary']['missing_markers'] += 1
            if not validation_result['correct_function_call'] and validation_result['marker_type'] != 'NONE':
                results['summary']['wrong_function_calls'] += 1
    
    return results

def convert_to_alpaca_format(valid_data: List[Dict]) -> List[Dict]:
    """转换为alpaca格式"""
    alpaca_data = []
    
    for item in valid_data:
        alpaca_item = {
            "instruction": item["instruction"],
            "input": "",  # 我们的任务不需要额外input
            "output": item["output"]
        }
        alpaca_data.append(alpaca_item)
    
    return alpaca_data

def generate_quality_report(results: Dict, report_file: str):
    """生成质量报告"""
    report = []
    report.append("=" * 60)
    report.append("数据质量验证报告")
    report.append("=" * 60)
    report.append(f"输入文件: {results['input_file']}")
    report.append(f"总样本数: {results['total_items']}")
    report.append(f"有效样本: {results['valid_items']} ({results['valid_items']/results['total_items']*100:.1f}%)")
    report.append(f"无效样本: {results['invalid_items']} ({results['invalid_items']/results['total_items']*100:.1f}%)")
    report.append("")
    
    # 有效样本类型分布
    summary = results['summary']
    if results['valid_items'] > 0:
        report.append("有效样本类型分布:")
        report.append(f"  AGENT模式: {summary['agent_count']} ({summary['agent_count']/results['valid_items']*100:.1f}%)")
        report.append(f"  EDIT模式: {summary['edit_count']} ({summary['edit_count']/results['valid_items']*100:.1f}%)")
        report.append("")
    
    # 问题统计
    if results['invalid_items'] > 0:
        report.append("问题统计:")
        if summary['missing_think'] > 0:
            report.append(f"  缺少 <think> 部分: {summary['missing_think']} 项")
        if summary['missing_markers'] > 0:
            report.append(f"  缺少特殊词符: {summary['missing_markers']} 项")
        if summary['wrong_function_calls'] > 0:
            report.append(f"  函数调用错误: {summary['wrong_function_calls']} 项")
        report.append("")
    
    # 样本分析
    if results['valid_items'] > 0:
        report.append("有效样本示例:")
        for i, item in enumerate(results['valid_data'][:3]):  # 显示前3个
            report.append(f"  示例 {i+1} (索引 {item['index']}):")
            report.append(f"    指令: {item['instruction'][:100]}...")
            report.append(f"    输出: {item['output'][:100]}...")
            report.append("")
    
    if results['invalid_items'] > 0:
        report.append("无效样本问题详情:")
        invalid_details = [d for d in results['validation_details'] if not d.get('valid', False)]
        for detail in invalid_details[:5]:  # 显示前5个问题
            if 'error' in detail:
                report.append(f"  索引 {detail['index']}: {detail['error']}")
            else:
                issues = ', '.join(detail['issues'])
                report.append(f"  索引 {detail['index']}: {issues}")
        
        if len(invalid_details) > 5:
            report.append(f"  ... 还有 {len(invalid_details) - 5} 个无效样本")
        report.append("")
    
    # 保存报告
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    return report

def print_summary(results: Dict):
    """打印验证摘要"""
    print(f"📊 验证完成:")
    print(f"   输入文件: {results['input_file']}")
    print(f"   总样本数: {results['total_items']}")
    print(f"   ✅ 有效样本: {results['valid_items']} ({results['valid_items']/results['total_items']*100:.1f}%)")
    print(f"   ❌ 无效样本: {results['invalid_items']} ({results['invalid_items']/results['total_items']*100:.1f}%)")
    
    summary = results['summary']
    if results['valid_items'] > 0:
        print(f"   🤖 AGENT模式: {summary['agent_count']}")
        print(f"   ✏️  EDIT模式: {summary['edit_count']}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='批量验证训练数据质量')
    parser.add_argument('input_file', help='输入的JSON数据文件')
    parser.add_argument('--output', type=str, help='输出的alpaca格式文件路径')
    parser.add_argument('--report', type=str, help='质量报告文件路径')
    parser.add_argument('--format', choices=['auto', 'constructor', 'hw3'], default='auto',
                       help='数据格式 (auto: 自动检测, constructor: data_constructor格式, hw3: hw3_2格式)')
    parser.add_argument('--keep-invalid', action='store_true', help='同时保存无效数据用于分析')
    
    args = parser.parse_args()
    
    input_file = args.input_file
    if not Path(input_file).exists():
        print(f"❌ 错误: 文件不存在 {input_file}")
        return
    
    print(f"🔍 开始验证数据文件: {input_file}")
    
    # 执行验证
    results = validate_data_file(input_file, args.format)
    
    if 'error' in results:
        print(f"❌ 错误: {results['error']}")
        return
    
    # 打印摘要
    print_summary(results)
    
    # 生成质量报告
    # 确保输出目录存在
    import os
    os.makedirs("outputs/reports", exist_ok=True)
    os.makedirs("outputs/validation", exist_ok=True)
    
    if args.report:
        report_file = args.report
    else:
        base_name = os.path.basename(input_file).replace('.json', '_quality_report.txt')
        report_file = f"outputs/reports/{base_name}"
    
    report_lines = generate_quality_report(results, report_file)
    print(f"📊 质量报告已保存到: {report_file}")
    
    # 保存有效数据为alpaca格式
    if results['valid_items'] > 0:
        alpaca_data = convert_to_alpaca_format(results['valid_data'])
        
        if args.output:
            alpaca_file = args.output
        else:
            base_name = os.path.basename(input_file).replace('.json', '_valid_alpaca.json')
            alpaca_file = f"outputs/validation/{base_name}"
        
        with open(alpaca_file, 'w', encoding='utf-8') as f:
            json.dump(alpaca_data, f, ensure_ascii=False, indent=2)
        
        print(f"📦 有效数据(Alpaca格式)已保存到: {alpaca_file}")
    
    # 可选：保存无效数据用于分析
    if args.keep_invalid and results['invalid_items'] > 0:
        base_name = os.path.basename(input_file).replace('.json', '_invalid.json')
        invalid_file = f"outputs/validation/{base_name}"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            json.dump(results['invalid_data'], f, ensure_ascii=False, indent=2)
        
        print(f"🔍 无效数据已保存到: {invalid_file}")
    
    print("\n" + "=" * 50)
    print("验证完成！")

if __name__ == "__main__":
    main() 