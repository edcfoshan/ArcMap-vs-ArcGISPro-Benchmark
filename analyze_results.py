#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyze and compare benchmark results between Python 2.7 and Python 3.x
Compatible with Python 2.7 and 3.x

Usage:
    python analyze_results.py [--results-dir PATH]
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import json
import csv
import argparse
from datetime import datetime

# Python 2/3 compatibility for file open
import io

def open_text_file(filepath, mode):
    """Open file with UTF-8 encoding for both Python 2 and 3"""
    if sys.version_info[0] >= 3:
        return io.open(filepath, mode, encoding='utf-8', newline='')
    else:
        return io.open(filepath, mode, encoding='utf-8')

# Alias for CSV compatibility
open_csv_file = open_text_file

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.result_exporter import ResultExporter


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Analyze ArcGIS Python Benchmark Results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Analyze results in default directory:
    python analyze_results.py
  
  Analyze results in custom directory:
    python analyze_results.py --results-dir /path/to/results
        '''
    )
    
    parser.add_argument(
        '--results-dir',
        type=str,
        default=settings.RAW_RESULTS_DIR,
        help='Directory containing result JSON files (default: from settings)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=settings.TABLES_DIR,
        help='Output directory for generated tables'
    )
    
    # Python 2/3 compatibility for argparse
    if len(sys.argv) == 1:
        return parser.parse_args([])
    
    return parser.parse_args()


def load_results(results_dir):
    """Load benchmark results from JSON files"""
    results_py2 = None
    results_py3 = None
    
    # Look for result files
    for filename in os.listdir(results_dir):
        if filename.endswith('.json') and 'benchmark_results' in filename:
            filepath = os.path.join(results_dir, filename)
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            results = data.get('results', [])
            
            # Determine Python version from filename or content
            if 'py2' in filename:
                results_py2 = results
                print("Loaded Python 2.7 results from: {}".format(filename))
            elif 'py3' in filename:
                results_py3 = results
                print("Loaded Python 3.x results from: {}".format(filename))
            else:
                # Try to detect from content
                if results and 'python_version' in results[0]:
                    if results[0]['python_version'].startswith('2.'):
                        results_py2 = results
                        print("Loaded Python 2.7 results from: {}".format(filename))
                    else:
                        results_py3 = results
                        print("Loaded Python 3.x results from: {}".format(filename))
    
    return results_py2, results_py3


def create_comparison(results_py2, results_py3):
    """Create side-by-side comparison"""
    comparison = []
    
    # Create lookup dictionaries
    py2_lookup = {r['test_name']: r for r in results_py2 if r.get('success')}
    py3_lookup = {r['test_name']: r for r in results_py3 if r.get('success')}
    
    # Get all test names
    all_tests = sorted(set(py2_lookup.keys()) | set(py3_lookup.keys()))
    
    for test_name in all_tests:
        py2_result = py2_lookup.get(test_name, {})
        py3_result = py3_lookup.get(test_name, {})
        
        py2_time = py2_result.get('mean_time', 0)
        py2_std = py2_result.get('std_time', 0)
        py3_time = py3_result.get('mean_time', 0)
        py3_std = py3_result.get('std_time', 0)
        
        # Calculate speedup
        if py3_time > 0 and py2_time > 0:
            speedup = py2_time / py3_time
        else:
            speedup = 0
        
        # 判断哪个版本更快
        if speedup > 1.05:
            faster = "Python 3.x 更快"
        elif speedup < 0.95:
            faster = "Python 2.7 更快"
        else:
            faster = "性能相当"
        
        # Get category
        category = py2_result.get('category', py3_result.get('category', 'unknown'))
        
        comparison.append({
            'test_name': test_name,
            'category': category,
            'py2_time': py2_time,
            'py2_std': py2_std,
            'py3_time': py3_time,
            'py3_std': py3_std,
            'speedup': speedup,
            'faster': faster,
            'py2_success': test_name in py2_lookup,
            'py3_success': test_name in py3_lookup
        })
    
    return comparison


def calculate_statistics(comparison):
    """计算统计摘要"""
    stats = {
        'total_tests': len(comparison),
        'py3_faster': len([c for c in comparison if c['faster'] == "Python 3.x 更快"]),
        'py2_faster': len([c for c in comparison if c['faster'] == "Python 2.7 更快"]),
        'equal': len([c for c in comparison if c['faster'] == "性能相当"]),
        'average_speedup': 0,
        'median_speedup': 0,
        'max_speedup': 0,
        'min_speedup': 0
    }
    
    speedups = [c['speedup'] for c in comparison if c['speedup'] > 0]
    
    if speedups:
        stats['average_speedup'] = sum(speedups) / len(speedups)
        stats['median_speedup'] = sorted(speedups)[len(speedups) // 2]
        stats['max_speedup'] = max(speedups)
        stats['min_speedup'] = min(speedups)
    
    return stats


def format_time(value, std):
    """Format time with standard deviation"""
    if value == 0:
        return "N/A"
    return "{:.4f} ± {:.4f}".format(value, std)


def format_speedup(value):
    """Format speedup value"""
    if value == 0:
        return "N/A"
    return "{:.2f}x".format(value)


def generate_markdown_table(comparison, stats, results_py2=None, results_py3=None):
    """生成 Markdown 对比报告（全中文）"""
    lines = []
    
    lines.append("# ArcGIS Python 2.7 vs Python 3.x 性能对比报告")
    lines.append("")
    lines.append("*生成时间：{}*".format(datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')))
    lines.append("")
    
    # 数据规模信息
    lines.append("## 测试数据规模")
    lines.append("")
    lines.append("| 配置项 | 数值 |")
    lines.append("|--------|------|")
    lines.append("| 数据规模 | **{}** |".format(settings.DATA_SCALE.upper()))
    lines.append("| 渔网多边形 | {:,} ({:,}×{:,}) |".format(
        settings.VECTOR_CONFIG['fishnet_rows'] * settings.VECTOR_CONFIG['fishnet_cols'],
        settings.VECTOR_CONFIG['fishnet_rows'],
        settings.VECTOR_CONFIG['fishnet_cols']
    ))
    lines.append("| 随机点数量 | {:,} |".format(settings.VECTOR_CONFIG['random_points']))
    lines.append("| 缓冲区测试点 | {:,} |".format(settings.VECTOR_CONFIG['buffer_points']))
    lines.append("| 叠加分析要素 | {:,} × {:,} |".format(
        settings.VECTOR_CONFIG['intersect_features_a'],
        settings.VECTOR_CONFIG['intersect_features_b']
    ))
    lines.append("| 空间连接 | {:,}点 + {:,}多边形 |".format(
        settings.VECTOR_CONFIG['spatial_join_points'],
        settings.VECTOR_CONFIG['spatial_join_polygons']
    ))
    lines.append("| 字段计算记录 | {:,} |".format(settings.VECTOR_CONFIG['calculate_field_records']))
    lines.append("| 栅格大小 | {:,}×{:,} ({:,}像素) |".format(
        settings.RASTER_CONFIG['constant_raster_size'],
        settings.RASTER_CONFIG['constant_raster_size'],
        settings.RASTER_CONFIG['constant_raster_size'] ** 2
    ))
    lines.append("")
    
    # 规模说明
    scale_desc = {
        'tiny': '超小规模 - 快速验证/调试（约1-2分钟）',
        'small': '小型规模 - 功能测试（约5-10分钟）',
        'standard': '标准规模 - 常规测试（约15-30分钟）',
        'medium': '中型规模 - 性能对比（约30-60分钟）',
        'large': '大型规模 - 学术研究（约2-4小时）'
    }
    lines.append("**规模说明**: {}".format(scale_desc.get(settings.DATA_SCALE, '未知')))
    lines.append("")
    
    # 统计摘要
    lines.append("## 统计摘要")
    lines.append("")
    lines.append("| 指标 | 数值 |")
    lines.append("|------|------|")
    lines.append("| 测试项目总数 | {} |".format(stats['total_tests']))
    lines.append("| Python 3.x 更快 | {} ({:.1f}%) |".format(
        stats['py3_faster'],
        stats['py3_faster'] / stats['total_tests'] * 100 if stats['total_tests'] > 0 else 0
    ))
    lines.append("| Python 2.7 更快 | {} ({:.1f}%) |".format(
        stats['py2_faster'],
        stats['py2_faster'] / stats['total_tests'] * 100 if stats['total_tests'] > 0 else 0
    ))
    lines.append("| 性能相当 | {} ({:.1f}%) |".format(
        stats['equal'],
        stats['equal'] / stats['total_tests'] * 100 if stats['total_tests'] > 0 else 0
    ))
    lines.append("| 平均加速比 | {:.2f}x |".format(stats['average_speedup']))
    lines.append("| 中位数加速比 | {:.2f}x |".format(stats['median_speedup']))
    lines.append("| 最大加速比 | {:.2f}x |".format(stats['max_speedup']))
    lines.append("| 最小加速比 | {:.2f}x |".format(stats['min_speedup']))
    lines.append("")
    
    # 详细结果表
    lines.append("## 详细对比结果")
    lines.append("")
    
    # Check if we have multiprocess results from raw data
    has_mp_results = False
    mp_data = {}  # {base_name: {py2_single, py2_multi, py3_single, py3_multi}}
    
    if results_py2 or results_py3:
        # Extract multiprocess results from raw data
        def extract_mp_results(results, version):
            """Extract MP test results from raw results"""
            mp_results = {}
            for r in results or []:
                name = r.get('test_name', '')
                if 'MP_' in name:
                    # Parse name like "Py2_MP_V1_CreateFishnet_single" or "MP_V1_CreateFishnet_single"
                    base_name = name
                    if '_single' in name:
                        base_name = name.replace('_single', '').replace('Py2_', '').replace('Py3_', '').replace('Py27_', '').replace('Py39_', '')
                        mp_results[base_name] = mp_results.get(base_name, {})
                        mp_results[base_name]['%s_single' % version] = r.get('mean_time', 0)
                    elif '_multiprocess' in name:
                        base_name = name.replace('_multiprocess', '').replace('Py2_', '').replace('Py3_', '').replace('Py27_', '').replace('Py39_', '')
                        mp_results[base_name] = mp_results.get(base_name, {})
                        mp_results[base_name]['%s_multi' % version] = r.get('mean_time', 0)
                        mp_results[base_name]['workers'] = r.get('num_workers', 4)
            return mp_results
        
        py2_mp = extract_mp_results(results_py2, 'py2')
        py3_mp = extract_mp_results(results_py3, 'py3')
        
        # Merge data
        all_bases = set(py2_mp.keys()) | set(py3_mp.keys())
        for base in all_bases:
            mp_data[base] = {
                'py2_single': py2_mp.get(base, {}).get('py2_single', 0),
                'py2_multi': py2_mp.get(base, {}).get('py2_multi', 0),
                'py3_single': py3_mp.get(base, {}).get('py3_single', 0),
                'py3_multi': py3_mp.get(base, {}).get('py3_multi', 0),
                'workers': py2_mp.get(base, {}).get('workers', 4) or py3_mp.get(base, {}).get('workers', 4)
            }
            if mp_data[base]['py2_single'] or mp_data[base]['py2_multi'] or mp_data[base]['py3_single'] or mp_data[base]['py3_multi']:
                has_mp_results = True
    
    if has_mp_results:
        # 有多进程结果，显示扩展表格（包含常规测试和多进程测试）
        lines.append("| 测试项目 | 类别 | Py2.7单进程 | Py2.7多进程 | Py3.x单进程 | Py3.x多进程 | Py2.7单/多加速 | Py3.x单/多加速 |")
        lines.append("|----------|------|-------------|-------------|-------------|-------------|----------------|----------------|")
        
        # Regular tests (non-MP) - 显示 Py2.7 vs Py3.x 对比
        regular_tests = [r for r in comparison if not r.get('test_name', '').startswith('MP_') and 'MP_' not in r.get('test_name', '')]
        for item in regular_tests:
            lines.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                item['test_name'],
                item['category'],
                format_time(item['py2_time'], item['py2_std']),
                "-",
                format_time(item['py3_time'], item['py3_std']),
                "-",
                format_speedup(item['speedup']),
                "-"
            ))
        
        # Multiprocess tests - 显示单进程vs多进程对比
        for base_name, data in sorted(mp_data.items()):
            py2_single = data.get('py2_single', 0)
            py2_multi = data.get('py2_multi', 0)
            py3_single = data.get('py3_single', 0)
            py3_multi = data.get('py3_multi', 0)
            
            # 计算多进程加速比（单进程时间 / 多进程时间）
            py2_mp_speedup = py2_single / py2_multi if py2_multi > 0 else 0
            py3_mp_speedup = py3_single / py3_multi if py3_multi > 0 else 0
            
            # 简化显示名称：去掉 MP_ 前缀
            display_name = base_name.replace('MP_', '')
            
            lines.append("| {} | multiprocess | {} | {} | {} | {} | {} | {} |".format(
                display_name,
                "{:.4f}".format(py2_single) if py2_single > 0 else "-",
                "{:.4f}".format(py2_multi) if py2_multi > 0 else "-",
                "{:.4f}".format(py3_single) if py3_single > 0 else "-",
                "{:.4f}".format(py3_multi) if py3_multi > 0 else "-",
                "{:.2f}x".format(py2_mp_speedup) if py2_mp_speedup > 0 else "-",
                "{:.2f}x".format(py3_mp_speedup) if py3_mp_speedup > 0 else "-"
            ))
    else:
        # 无多进程结果，显示标准表格
        lines.append("| 测试项目 | 类别 | Python 2.7 (秒) | Python 3.x (秒) | 加速比 | 更快 |")
        lines.append("|----------|------|-----------------|-----------------|--------|------|")
        
        for item in comparison:
            lines.append("| {} | {} | {} | {} | {} | {} |".format(
                item['test_name'],
                item['category'],
                format_time(item['py2_time'], item['py2_std']),
                format_time(item['py3_time'], item['py3_std']),
                format_speedup(item['speedup']),
                item['faster']
            ))
    
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    lines.append("- **时间格式**: 平均值 ± 标准差（单位：秒）")
    lines.append("- **加速比**: Python 2.7 执行时间 / Python 3.x 执行时间")
    lines.append("  - 加速比 > 1：Python 3.x 更快")
    lines.append("  - 加速比 < 1：Python 2.7 更快")
    lines.append("  - 加速比 ≈ 1：两者性能相当（差异 < 5%）")
    lines.append("- **更快**: 表示性能更优的 Python 版本")
    lines.append("")
    lines.append("## 分析结论")
    lines.append("")
    lines.append("根据基准测试结果：")
    if stats['average_speedup'] > 1:
        lines.append("- 总体趋势：**Python 3.x 比 Python 2.7 快 {:.2f} 倍**".format(stats['average_speedup']))
        lines.append("  - Python 3.x 性能提升 {:.1f}%".format((stats['average_speedup']-1)*100))
    else:
        lines.append("- 总体趋势：**Python 2.7 比 Python 3.x 快 {:.2f} 倍**".format(1 / stats['average_speedup']))
        lines.append("  - Python 2.7 性能提升 {:.1f}%".format((1/stats['average_speedup']-1)*100))
    
    lines.append("- Python 3.x 在 {} / {} 个测试项目中更快（占比 {:.1f}%）".format(
        stats['py3_faster'],
        stats['total_tests'],
        stats['py3_faster'] / stats['total_tests'] * 100 if stats['total_tests'] > 0 else 0
    ))
    
    lines.append("")
    lines.append("")
    lines.append("## 多进程性能对比")
    lines.append("")
    
    if has_mp_results:
        lines.append("> **说明**: 对比单进程与多进程（默认4进程）的性能差异。")
        lines.append("> 详细数据见上文「详细对比结果」表格中的多进程相关列。")
        lines.append("")
        
        # Calculate overall statistics from mp_data
        py2_speedups = []
        py3_speedups = []
        for base_name, data in mp_data.items():
            if data.get('py2_single') and data.get('py2_multi'):
                py2_speedups.append(data['py2_single'] / data['py2_multi'])
            if data.get('py3_single') and data.get('py3_multi'):
                py3_speedups.append(data['py3_single'] / data['py3_multi'])
        
        lines.append("### 多进程统计摘要")
        lines.append("")
        lines.append("| Python版本 | 测试项目数 | 平均加速比 | 评价 |")
        lines.append("|-----------|-----------|-----------|------|")
        if py2_speedups:
            avg_sp = sum(py2_speedups) / len(py2_speedups)
            eval_text = "优秀" if avg_sp >= 3.5 else "良好" if avg_sp >= 2.5 else "一般" if avg_sp >= 1.5 else "较差"
            lines.append("| Python 2.7 | {} | {:.2f}x | {} |".format(len(py2_speedups), avg_sp, eval_text))
        if py3_speedups:
            avg_sp = sum(py3_speedups) / len(py3_speedups)
            eval_text = "优秀" if avg_sp >= 3.5 else "良好" if avg_sp >= 2.5 else "一般" if avg_sp >= 1.5 else "较差"
            lines.append("| Python 3.x | {} | {:.2f}x | {} |".format(len(py3_speedups), avg_sp, eval_text))
        lines.append("")
        
        lines.append("**说明**:")
        lines.append("- **加速比**: 单进程时间 / 多进程时间，理想值为进程数（4.0x）")
        lines.append("- **评价标准**: 优秀(≥3.5x) / 良好(2.5-3.5x) / 一般(1.5-2.5x) / 较差(<1.5x)")
    else:
        lines.append("本次测试未启用多进程对比。")
        lines.append("")
        lines.append("如需启用多进程测试，请勾选「多进程对比」选项。")
    
    lines.append("")
    lines.append("---")
    lines.append("*报告由 ArcGIS Python 性能对比测试工具自动生成*")
    
    return '\n'.join(lines)


def generate_latex_table(comparison, stats):
    """Generate LaTeX comparison table"""
    lines = []
    
    lines.append("% ArcGIS Python Performance Comparison")
    lines.append("% Generated on {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    lines.append("")
    
    # Summary table
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{Summary Statistics}")
    lines.append("\\begin{tabular}{lc}")
    lines.append("\\hline")
    lines.append("\\textbf{Metric} & \\textbf{Value} \\\\")
    lines.append("\\hline")
    lines.append("Total Tests & {} \\\\".format(stats['total_tests']))
    lines.append("Python 3.x Faster & {} ({:.1f}\\%) \\\\".format(
        stats['py3_faster'],
        stats['py3_faster'] / stats['total_tests'] * 100 if stats['total_tests'] > 0 else 0
    ))
    lines.append("Python 2.7 Faster & {} ({:.1f}\\%) \\\\".format(
        stats['py2_faster'],
        stats['py2_faster'] / stats['total_tests'] * 100 if stats['total_tests'] > 0 else 0
    ))
    lines.append("Average Speedup & {:.2f}x \\\\".format(stats['average_speedup']))
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\label{tab:summary_stats}")
    lines.append("\\end{table}")
    lines.append("")
    
    # Detailed results table
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{Detailed Benchmark Results}")
    lines.append("\\begin{tabular}{llcccc}")
    lines.append("\\hline")
    lines.append("\\textbf{Test} & \\textbf{Category} & \\textbf{Py2.7 (s)} & \\textbf{Py3.x (s)} & \\textbf{Speedup} & \\textbf{Faster} \\\\")
    lines.append("\\hline")
    
    for item in comparison:
        py2_str = "{:.2f}$\\pm${:.2f}".format(item['py2_time'], item['py2_std']) if item['py2_time'] > 0 else "N/A"
        py3_str = "{:.2f}$\\pm${:.2f}".format(item['py3_time'], item['py3_std']) if item['py3_time'] > 0 else "N/A"
        
        lines.append("{} & {} & {} & {} & {:.2f}x & {} \\\\".format(
            item['test_name'].replace('_', '\\_'),
            item['category'],
            py2_str,
            py3_str,
            item['speedup'],
            item['faster'].replace('.', '.').replace(' ', '\\ ')
        ))
    
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\label{tab:detailed_results}")
    lines.append("\\end{table}")
    
    return '\n'.join(lines)


def generate_csv(comparison, output_path):
    """Generate CSV file"""
    fieldnames = [
        'test_name', 'category',
        'py2_time', 'py2_std', 'py2_success',
        'py3_time', 'py3_std', 'py3_success',
        'speedup', 'faster'
    ]
    
    with open_csv_file(output_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in comparison:
            writer.writerow({k: item.get(k, '') for k in fieldnames})
    
    return output_path


def save_outputs(comparison, stats, output_dir, results_py2=None, results_py3=None):
    """Save all output formats"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    saved_files = {}
    
    # Markdown
    md_content = generate_markdown_table(comparison, stats, results_py2, results_py3)
    md_path = os.path.join(output_dir, "comparison_report.md")
    with open_text_file(md_path, 'w') as f:
        f.write(md_content)
    saved_files['markdown'] = md_path
    print("Markdown report saved: {}".format(md_path))
    
    # LaTeX
    latex_content = generate_latex_table(comparison, stats)
    latex_path = os.path.join(output_dir, "comparison_table.tex")
    with open_text_file(latex_path, 'w') as f:
        f.write(latex_content)
    saved_files['latex'] = latex_path
    print("LaTeX table saved: {}".format(latex_path))
    
    # CSV
    csv_path = os.path.join(output_dir, "comparison_data.csv")
    generate_csv(comparison, csv_path)
    saved_files['csv'] = csv_path
    print("CSV data saved: {}".format(csv_path))
    
    # JSON
    json_path = os.path.join(output_dir, "comparison_data.json")
    with open_text_file(json_path, 'w') as f:
        json.dump({
            'comparison': comparison,
            'statistics': stats,
            'generated': datetime.now().isoformat()
        }, f, indent=2)
    saved_files['json'] = json_path
    print("JSON data saved: {}".format(json_path))
    
    return saved_files


def main():
    """Main function"""
    # Parse arguments
    args = parse_args()
    
    # Print banner
    print("=" * 70)
    print("ArcGIS Python Benchmark Results Analyzer")
    print("=" * 70)
    print("")
    print("Results directory: {}".format(args.results_dir))
    print("Output directory: {}".format(args.output_dir))
    print("")
    
    # Load results
    results_py2, results_py3 = load_results(args.results_dir)
    
    if not results_py2 and not results_py3:
        print("\nERROR: No benchmark results found!")
        print("Please run run_benchmarks.py with both Python versions first.")
        return 1
    
    if not results_py2:
        print("\nWARNING: Python 2.7 results not found!")
    
    if not results_py3:
        print("\nWARNING: Python 3.x results not found!")
    
    if not results_py2 or not results_py3:
        print("\nCannot create comparison without results from both versions.")
        return 1
    
    # Create comparison
    print("\nCreating comparison...")
    comparison = create_comparison(results_py2, results_py3)
    
    # Calculate statistics
    stats = calculate_statistics(comparison)
    
    # Print summary
    print("\n" + "=" * 70)
    print("Analysis Summary")
    print("=" * 70)
    print("Total tests: {}".format(stats['total_tests']))
    print("Python 3.x faster: {} ({:.1f}%)".format(
        stats['py3_faster'],
        stats['py3_faster'] / stats['total_tests'] * 100
    ))
    print("Python 2.7 faster: {} ({:.1f}%)".format(
        stats['py2_faster'],
        stats['py2_faster'] / stats['total_tests'] * 100
    ))
    print("Equal performance: {} ({:.1f}%)".format(
        stats['equal'],
        stats['equal'] / stats['total_tests'] * 100
    ))
    print("Average speedup: {:.2f}x".format(stats['average_speedup']))
    print("=" * 70)
    
    # Save outputs
    print("\nSaving output files...")
    saved_files = save_outputs(comparison, stats, args.output_dir, results_py2, results_py3)
    
    print("\n" + "=" * 70)
    print("Analysis Complete")
    print("=" * 70)
    print("\nGenerated files:")
    for format_name, filepath in saved_files.items():
        print("  - {}: {}".format(format_name.upper(), filepath))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
