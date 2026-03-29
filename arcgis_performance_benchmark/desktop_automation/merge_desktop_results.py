# -*- coding: utf-8 -*-
"""
合并分析工具
对比四种运行方式的性能：
1. 独立 Python 2.7
2. 独立 Python 3.x
3. ArcMap Python 窗口
4. ArcGIS Pro Python 窗格
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import json

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze_results import generate_markdown_table, generate_latex_table, generate_csv, open_text_file


def load_result_file(filepath):
    """Load result file if exists"""
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data.get('results', [])
    except Exception as e:
        print("Warning: Could not load {}: {}".format(filepath, e))
        return None


def create_comparison(all_results):
    """Create comparison table"""
    # Get all test names
    all_tests = set()
    for results in all_results.values():
        if results:
            for r in results:
                all_tests.add(r.get('test_name', ''))
    
    comparison = []
    
    for test_name in sorted(all_tests):
        row = {'test_name': test_name}
        
        for env_name, results in all_results.items():
            if results:
                for r in results:
                    if r.get('test_name') == test_name:
                        if r.get('success'):
                            row[env_name] = r.get('mean_time', 0)
                        else:
                            row[env_name] = None
                        break
        
        comparison.append(row)
    
    return comparison


def generate_full_report(comparison, output_dir):
    """Generate full comparison report"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Markdown report
    md_lines = []
    md_lines.append("# ArcGIS Python 性能对比报告\n")
    md_lines.append("## 运行环境对比\n")
    md_lines.append("对比四种运行方式的性能差异：\n")
    md_lines.append("- **Standalone Py2.7**: 独立 Python 2.7 解释器\n")
    md_lines.append("- **Standalone Py3.x**: 独立 Python 3.x 解释器\n")
    md_lines.append("- **ArcMap Python**: ArcMap Python 窗口\n")
    md_lines.append("- **ArcGIS Pro**: ArcGIS Pro Python 窗格\n")
    md_lines.append("\n")
    
    # Table header
    headers = ['Test', 'Standalone Py2.7', 'Standalone Py3.x', 'ArcMap Python', 'ArcGIS Pro']
    md_lines.append("| {} |".format(" | ".join(headers)))
    md_lines.append("|{}|".format("|".join(["---"] * len(headers))))
    
    # Table rows
    for row in comparison:
        test_name = row.get('test_name', '')
        py2_standalone = row.get('standalone_py2', '-')
        py3_standalone = row.get('standalone_py3', '-')
        arcmap = row.get('arcmap', '-')
        arcgis_pro = row.get('arcgis_pro', '-')
        
        # Format values
        def fmt(val):
            if val is None:
                return "N/A"
            elif val == '-':
                return "-"
            else:
                return "{:.4f}s".format(val)
        
        md_lines.append("| {} | {} | {} | {} | {} |".format(
            test_name,
            fmt(py2_standalone),
            fmt(py3_standalone),
            fmt(arcmap),
            fmt(arcgis_pro)
        ))
    
    md_lines.append("\n")
    
    # Analysis
    md_lines.append("## 分析\n\n")
    
    # Calculate averages for available data
    env_times = {}
    for env_name in ['standalone_py2', 'standalone_py3', 'arcmap', 'arcgis_pro']:
        times = [r.get(env_name) for r in comparison if r.get(env_name) is not None]
        if times:
            env_times[env_name] = sum(times) / len(times)
    
    if env_times:
        md_lines.append("### 平均耗时\n\n")
        md_lines.append("| 运行环境 | 平均耗时 |\n")
        md_lines.append("|----------|----------|\n")
        
        env_names = {
            'standalone_py2': '独立 Python 2.7',
            'standalone_py3': '独立 Python 3.x',
            'arcmap': 'ArcMap Python 窗口',
            'arcgis_pro': 'ArcGIS Pro Python 窗格'
        }
        
        for env_name, avg_time in sorted(env_times.items(), key=lambda x: x[1]):
            md_lines.append("| {} | {:.4f}s |\n".format(env_names.get(env_name, env_name), avg_time))
        
        md_lines.append("\n")
        
        # Find fastest
        fastest = min(env_times.items(), key=lambda x: x[1])
        md_lines.append("### 结论\n\n")
        md_lines.append("**最快运行方式**: {} ({:.4f}s)\n\n".format(
            env_names.get(fastest[0], fastest[0]),
            fastest[1]
        ))
        
        # Calculate overhead
        if 'standalone_py3' in env_times and 'arcgis_pro' in env_times:
            overhead = ((env_times['arcgis_pro'] - env_times['standalone_py3']) / env_times['standalone_py3']) * 100
            md_lines.append("**ArcGIS Pro 开销**: {:.1f}%\n\n".format(overhead))
        
        if 'standalone_py2' in env_times and 'arcmap' in env_times:
            overhead = ((env_times['arcmap'] - env_times['standalone_py2']) / env_times['standalone_py2']) * 100
            md_lines.append("**ArcMap 开销**: {:.1f}%\n\n".format(overhead))
    
    # Save markdown
    md_path = os.path.join(output_dir, "desktop_comparison_report.md")
    with open_text_file(md_path, 'w') as f:
        f.write(''.join(md_lines))
    
    print("Markdown report saved: {}".format(md_path))
    
    # Also save as CSV
    csv_path = os.path.join(output_dir, "desktop_comparison_data.csv")
    with open_text_file(csv_path, 'w') as f:
        # Header
        f.write("Test,Standalone Py2.7,Standalone Py3.x,ArcMap Python,ArcGIS Pro\n")
        
        # Rows
        for row in comparison:
            test_name = row.get('test_name', '')
            values = [
                str(row.get('standalone_py2', '')) if row.get('standalone_py2') is not None else '',
                str(row.get('standalone_py3', '')) if row.get('standalone_py3') is not None else '',
                str(row.get('arcmap', '')) if row.get('arcmap') is not None else '',
                str(row.get('arcgis_pro', '')) if row.get('arcgis_pro') is not None else ''
            ]
            f.write("{},{}\n".format(test_name, ','.join(values)))
    
    print("CSV data saved: {}".format(csv_path))


def main():
    """Main function"""
    print("=" * 70)
    print("桌面软件 vs 独立解释器 性能对比分析")
    print("=" * 70)
    
    results_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "raw"
    )
    
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "tables"
    )
    
    # Load all results
    print("\n加载测试结果...\n")
    
    all_results = {
        'standalone_py2': load_result_file(
            os.path.join(results_dir, "benchmark_results_py2.json")
        ),
        'standalone_py3': load_result_file(
            os.path.join(results_dir, "benchmark_results_py3.json")
        ),
        'arcmap': load_result_file(
            os.path.join(results_dir, "benchmark_results_arcmap.json")
        ),
        'arcgis_pro': load_result_file(
            os.path.join(results_dir, "benchmark_results_arcgis_pro.json")
        )
    }
    
    # Check what we have
    available = [name for name, results in all_results.items() if results]
    missing = [name for name, results in all_results.items() if not results]
    
    print("可用结果: {}".format(', '.join(available)))
    if missing:
        print("缺失结果: {}".format(', '.join(missing)))
        print("\n提示：缺失的结果需要在对应环境中手动运行测试脚本")
    
    if not available:
        print("\n错误：没有找到任何测试结果！")
        print("请先运行测试（独立解释器或桌面软件）")
        return 1
    
    # Create comparison
    print("\n生成对比分析...\n")
    comparison = create_comparison(all_results)
    
    # Generate report
    generate_full_report(comparison, output_dir)
    
    print("\n" + "=" * 70)
    print("分析完成！")
    print("=" * 70)
    print("\n生成的文件:")
    print("  - desktop_comparison_report.md")
    print("  - desktop_comparison_data.csv")
    
    return 0


def open_text_file(filepath, mode):
    """Open file with UTF-8 encoding"""
    import io
    if sys.version_info[0] >= 3:
        return io.open(filepath, mode, encoding='utf-8', newline='')
    else:
        return io.open(filepath, mode, encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
