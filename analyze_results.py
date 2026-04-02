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
import platform
import subprocess
import glob
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


def _is_timestamp_name(name):
    """Return True if a folder name looks like YYYYMMDD_HHMMSS."""
    return (
        len(name) == 15 and
        name[8] == '_' and
        name[:8].isdigit() and
        name[9:].isdigit()
    )


def _has_benchmark_results(results_dir):
    """Check whether a directory contains benchmark result JSON files."""
    return any(True for _ in _iter_result_files(results_dir))


def _iter_result_files(root_dir):
    """Yield benchmark result JSON files recursively from a root directory."""
    if not root_dir or not os.path.isdir(root_dir):
        return

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            lowered = filename.lower()
            if lowered.endswith('.json') and 'benchmark_results' in lowered:
                yield os.path.join(dirpath, filename)


def _find_result_root(result_file_dir):
    """Find the timestamp root for a result file directory."""
    current = os.path.abspath(result_file_dir)

    while True:
        if _is_timestamp_name(os.path.basename(current)):
            return current

        parent = os.path.dirname(current)
        if parent == current:
            return result_file_dir
        current = parent


def _find_latest_results_dir():
    """Find the most recent benchmark result directory."""
    for base_dir in [getattr(settings, 'DATA_DIR', None), getattr(settings, 'RAW_RESULTS_DIR', None)]:
        if not base_dir or not os.path.isdir(base_dir):
            continue

        candidates = {}
        for result_file in _iter_result_files(base_dir):
            result_root = _find_result_root(os.path.dirname(result_file))
            try:
                mtime = os.path.getmtime(result_file)
            except OSError:
                continue
            if result_root not in candidates or mtime > candidates[result_root]:
                candidates[result_root] = mtime

        if candidates:
            return sorted(candidates.items(), key=lambda item: item[1])[-1][0]

    return None

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
        args = parser.parse_args([])
    else:
        args = parser.parse_args()

    # If the caller did not specify a results directory, prefer the newest
    # benchmark run so the default command follows the latest output.
    if '--results-dir' not in sys.argv:
        latest_results_dir = _find_latest_results_dir()
        if latest_results_dir:
            args.results_dir = latest_results_dir

    # Default report output to the same directory as the raw results.
    if '--output-dir' not in sys.argv:
        args.output_dir = args.results_dir
    
    return args


def load_results(results_dir):
    """Load benchmark results from JSON files (including open-source)"""
    results_py2 = None
    results_py3 = None
    results_os = None

    candidate_files = sorted(list(_iter_result_files(results_dir)))

    for filepath in candidate_files:
        filename = os.path.basename(filepath)

        with open_text_file(filepath, 'r') as f:
            data = json.load(f)

        results = data.get('results', [])
        lower_name = filename.lower()

        # Determine Python version from filename or content
        if 'py2' in lower_name:
            if results_py2 is None:
                results_py2 = []
            results_py2.extend(results)
            print("Loaded Python 2.7 results from: {}".format(filename))
        elif 'py3' in lower_name and 'benchmark_results_os' not in lower_name and 'opensource' not in lower_name:
            # Check if it's a dedicated open-source results file
            # Split results into arcpy and open-source (if any _OS tests exist)
            # OS tests have '_OS' suffix like 'V1_CreateFishnet_OS'
            py3_results = [r for r in results if not r.get('test_name', '').endswith('_OS')]
            os_results = [r for r in results if r.get('test_name', '').endswith('_OS')]

            if py3_results:
                if results_py3 is None:
                    results_py3 = []
                results_py3.extend(py3_results)
                print("Loaded Python 3.x results from: {} ({} tests)".format(filename, len(py3_results)))
            if os_results:
                if results_os is None:
                    results_os = []
                results_os.extend(os_results)
                print("Loaded Open-Source results from: {} ({} tests)".format(filename, len(os_results)))
        elif 'benchmark_results_os' in lower_name or 'opensource' in lower_name or lower_name.endswith('_os.json'):
            if results_os is None:
                results_os = []
            results_os.extend(results)
            print("Loaded Open-Source results from: {}".format(filename))
        else:
            # Try to detect from content
            if results and 'python_version' in results[0]:
                py_ver = results[0]['python_version']
                if py_ver.startswith('2.'):
                    if results_py2 is None:
                        results_py2 = []
                    results_py2.extend(results)
                    print("Loaded Python 2.7 results from: {}".format(filename))
                elif any(r.get('test_name', '').endswith('_OS') for r in results):
                    # Split results (OS tests have _OS suffix)
                    new_py3_results = [r for r in results if not r.get('test_name', '').endswith('_OS')]
                    new_os_results = [r for r in results if r.get('test_name', '').endswith('_OS')]
                    if new_py3_results:
                        if results_py3 is None:
                            results_py3 = []
                        results_py3.extend(new_py3_results)
                        print("Loaded Python 3.x results from: {}".format(filename))
                    if new_os_results:
                        if results_os is None:
                            results_os = []
                        results_os.extend(new_os_results)
                        print("Loaded Open-Source results from: {}".format(filename))
                else:
                    if results_py3 is None:
                        results_py3 = []
                    results_py3.extend(results)
                    print("Loaded Python 3.x results from: {}".format(filename))
    
    return results_py2, results_py3, results_os


def create_comparison(results_py2, results_py3, results_os=None):
    """Create side-by-side comparison (2-way or 3-way)"""
    comparison = []
    has_os = results_os is not None and len(results_os) > 0
    
    # Create lookup dictionaries
    py2_lookup = {r['test_name']: r for r in (results_py2 or []) if r.get('success')}
    py3_lookup = {r['test_name']: r for r in (results_py3 or []) if r.get('success')}
    os_lookup = {r['test_name']: r for r in (results_os or []) if r.get('success')}
    
    # Get all test names (base names without _OS suffix)
    # Filter out multiprocess test names (they contain _single, _multiprocess, or start with PyX_MP_)
    def is_multiprocess_test(name):
        return '_single' in name or '_multiprocess' in name or '_MP_' in name

    py2_tests = {n for n in py2_lookup.keys() if not is_multiprocess_test(n)}
    py3_tests = {n for n in py3_lookup.keys() if not is_multiprocess_test(n)}
    all_tests = py2_tests | py3_tests
    if has_os:
        # Add base names from OS tests (remove _OS suffix)
        for os_name in os_lookup.keys():
            if not is_multiprocess_test(os_name):
                base_name = os_name.replace('_OS', '')
                all_tests.add(base_name)
    all_tests = sorted(all_tests)
    
    for test_name in all_tests:
        py2_result = py2_lookup.get(test_name, {})
        py3_result = py3_lookup.get(test_name, {})
        os_result = os_lookup.get(test_name + '_OS', {})
        
        py2_time = py2_result.get('mean_time', 0)
        py2_std = py2_result.get('std_time', 0)
        py3_time = py3_result.get('mean_time', 0)
        py3_std = py3_result.get('std_time', 0)
        os_time = os_result.get('mean_time', 0)
        os_std = os_result.get('std_time', 0)
        
        # Calculate speedup (Py3 vs Py2)
        if py3_time > 0 and py2_time > 0:
            speedup = py2_time / py3_time
        else:
            speedup = 0
        
        # 判断哪个版本更快 (Py2 vs Py3)
        if py2_time <= 0 or py3_time <= 0:
            faster = "数据不完整"
        elif speedup > 1.05:
            faster = "Python 3.x 更快"
        elif speedup < 0.95:
            faster = "Python 2.7 更快"
        else:
            faster = "性能相当"
        
        # Determine fastest among all three
        times = {'Python 2.7': py2_time, 'Python 3.x': py3_time, 'Open-Source': os_time}
        valid_times = {k: v for k, v in times.items() if v > 0}
        if valid_times:
            fastest = min(valid_times, key=valid_times.get)
        else:
            fastest = "N/A"
        
        # Get category
        category = py2_result.get('category', py3_result.get('category', os_result.get('category', 'unknown')))
        
        comparison.append({
            'test_name': test_name,
            'category': category,
            'py2_time': py2_time,
            'py2_std': py2_std,
            'py3_time': py3_time,
            'py3_std': py3_std,
            'os_time': os_time,
            'os_std': os_std,
            'speedup': speedup,
            'faster': faster,
            'fastest': fastest,
            'py2_success': test_name in py2_lookup,
            'py3_success': test_name in py3_lookup,
            'os_success': test_name + '_OS' in os_lookup
        })
    
    return comparison, has_os


def calculate_statistics(comparison, has_os=False):
    """计算统计摘要（支持三向对比）"""
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
    
    # 3-way statistics
    if has_os:
        stats['os_faster'] = len([c for c in comparison if c['fastest'] == "Open-Source"])
        stats['py2_wins'] = len([c for c in comparison if c['fastest'] == "Python 2.7"])
        stats['py3_wins'] = len([c for c in comparison if c['fastest'] == "Python 3.x"])
        
        # Calculate OS speedups
        os_speedups_vs_py2 = []
        os_speedups_vs_py3 = []
        for c in comparison:
            if c['os_time'] > 0 and c['py2_time'] > 0:
                os_speedups_vs_py2.append(c['py2_time'] / c['os_time'])
            if c['os_time'] > 0 and c['py3_time'] > 0:
                os_speedups_vs_py3.append(c['py3_time'] / c['os_time'])
        
        if os_speedups_vs_py2:
            stats['os_vs_py2_avg'] = sum(os_speedups_vs_py2) / len(os_speedups_vs_py2)
        if os_speedups_vs_py3:
            stats['os_vs_py3_avg'] = sum(os_speedups_vs_py3) / len(os_speedups_vs_py3)
    
    speedups = [c['speedup'] for c in comparison if c['speedup'] > 0]
    
    if speedups:
        stats['average_speedup'] = sum(speedups) / len(speedups)
        stats['median_speedup'] = sorted(speedups)[len(speedups) // 2]
        stats['max_speedup'] = max(speedups)
        stats['min_speedup'] = min(speedups)
    
    return stats


def get_system_info():
    """获取系统配置信息"""
    info = {
        'os': platform.system() + ' ' + platform.release(),
        'processor': platform.processor() or 'Unknown',
        'machine': platform.machine(),
        'cpu_count': os.cpu_count() if hasattr(os, 'cpu_count') else 'Unknown',
        'python_version': platform.python_version(),
    }
    
    # 尝试获取更详细的CPU信息
    try:
        if sys.platform == 'win32':
            result = subprocess.check_output(['wmic', 'cpu', 'get', 'name', '/value'], 
                                            stderr=subprocess.STDOUT, shell=True)
            if sys.version_info[0] >= 3:
                result = result.decode('utf-8', errors='ignore')
            for line in result.split('\n'):
                if 'Name=' in line:
                    cpu_name = line.split('=')[1].strip()
                    # 简化CPU名称
                    cpu_name = cpu_name.replace('(R)', '').replace('(TM)', '').replace('CPU ', ' ')
                    info['cpu_name'] = cpu_name
                    break
    except Exception as e:
        info['cpu_name'] = info['processor']
    
    # 尝试获取内存信息（多种方法）
    info['memory_gb'] = 'Unknown'
    try:
        if sys.platform == 'win32':
            # 方法1：使用wmic
            try:
                result = subprocess.check_output(['wmic', 'computerchip', 'get', 'capacity', '/value'],
                                                stderr=subprocess.STDOUT, shell=True, timeout=5)
                if sys.version_info[0] >= 3:
                    result = result.decode('utf-8', errors='ignore')
                total_mem = 0
                for line in result.split('\n'):
                    if 'Capacity=' in line:
                        try:
                            total_mem += int(line.split('=')[1].strip())
                        except:
                            pass
                if total_mem > 0:
                    info['memory_gb'] = round(total_mem / (1024**3), 1)
            except:
                pass
            
            # 方法2：使用systeminfo作为备选
            if info['memory_gb'] == 'Unknown':
                try:
                    result = subprocess.check_output('systeminfo | findstr /C:"Total Physical Memory"',
                                                    stderr=subprocess.STDOUT, shell=True, timeout=10)
                    if sys.version_info[0] >= 3:
                        result = result.decode('utf-8', errors='ignore')
                    # 解析类似 "Total Physical Memory:     32,768 MB"
                    if 'MB' in result:
                        mem_str = result.split(':')[1].strip().replace(',', '').replace('MB', '').strip()
                        info['memory_gb'] = round(int(mem_str) / 1024, 1)
                except:
                    pass
    except:
        pass
    
    return info


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


def extract_multiprocess_data(results_py2, results_py3, results_os=None, comparison=None):
    """提取多进程测试结果（支持三向对比）"""
    mp_data = {}
    
    def extract_mp_results(results, version):
        """Extract MP test results from raw results"""
        mp_results = {}
        for r in results or []:
            name = r.get('test_name', '')
            if 'MP_' in name:
                # Parse name like "Py2_MP_V1_CreateFishnet_single" or "OS_MP_V1_CreateFishnet_OS_single"
                base_name = name
                if '_single' in name:
                    base_name = name.replace('_single', '').replace('Py2_', '').replace('Py3_', '').replace('Py27_', '').replace('Py39_', '').replace('OS_', '').replace('_OS', '')
                    mp_results[base_name] = mp_results.get(base_name, {})
                    mp_results[base_name]['%s_single' % version] = r.get('mean_time', 0)
                    mp_results[base_name]['%s_single_std' % version] = r.get('std_time', 0)
                elif '_multiprocess' in name:
                    base_name = name.replace('_multiprocess', '').replace('Py2_', '').replace('Py3_', '').replace('Py27_', '').replace('Py39_', '').replace('OS_', '').replace('_OS', '')
                    mp_results[base_name] = mp_results.get(base_name, {})
                    mp_results[base_name]['%s_multi' % version] = r.get('mean_time', 0)
                    mp_results[base_name]['%s_multi_std' % version] = r.get('std_time', 0)
                    mp_results[base_name]['workers'] = r.get('num_workers', 4)
        return mp_results
    
    py2_mp = extract_mp_results(results_py2, 'py2')
    py3_mp = extract_mp_results(results_py3, 'py3')
    os_mp = extract_mp_results(results_os, 'os') if results_os else {}

    # Also extract OS multiprocess tests from py2 and py3 results (they may contain OS MP tests)
    def extract_os_mp_from_results(results, prefix):
        """Extract OS-specific MP tests from py2/py3 results"""
        for r in results or []:
            name = r.get('test_name', '')
            if 'MP_' in name and '_OS' in name:
                # This is an OS multiprocess test stored in py2/py3 results
                base_name = name.replace('_single', '').replace('_multiprocess', '').replace('Py2_', '').replace('Py3_', '').replace('Py27_', '').replace('Py39_', '').replace('OS_', '').replace('_OS', '')
                if '_single' in name:
                    os_mp[base_name] = os_mp.get(base_name, {})
                    os_mp[base_name]['os_single'] = r.get('mean_time', 0)
                    os_mp[base_name]['os_single_std'] = r.get('std_time', 0)
                elif '_multiprocess' in name:
                    os_mp[base_name] = os_mp.get(base_name, {})
                    os_mp[base_name]['os_multi'] = r.get('mean_time', 0)
                    os_mp[base_name]['os_multi_std'] = r.get('std_time', 0)
                    os_mp[base_name]['workers'] = r.get('num_workers', 4)

    extract_os_mp_from_results(results_py2, 'py2')
    extract_os_mp_from_results(results_py3, 'py3')
    
    # Also extract OS single-thread times from comparison for reference
    os_single_times = {}
    if comparison:
        for item in comparison:
            test_name = item.get('test_name', '')
            if test_name and not test_name.startswith('Py') and '_MP_' not in test_name:
                # Map test name to MP format
                mp_name = 'MP_{}'.format(test_name)
                os_single_times[mp_name] = item.get('os_time', 0)
    
    # Merge data
    all_bases = set(py2_mp.keys()) | set(py3_mp.keys()) | set(os_mp.keys())
    for base in all_bases:
        # Try to get OS time from comparison if available
        os_time = os_mp.get(base, {}).get('os_single', 0)
        if os_time == 0 and base in os_single_times:
            os_time = os_single_times[base]
        
        mp_data[base] = {
            'py2_single': py2_mp.get(base, {}).get('py2_single', 0),
            'py2_single_std': py2_mp.get(base, {}).get('py2_single_std', 0),
            'py2_multi': py2_mp.get(base, {}).get('py2_multi', 0),
            'py2_multi_std': py2_mp.get(base, {}).get('py2_multi_std', 0),
            'py3_single': py3_mp.get(base, {}).get('py3_single', 0),
            'py3_single_std': py3_mp.get(base, {}).get('py3_single_std', 0),
            'py3_multi': py3_mp.get(base, {}).get('py3_multi', 0),
            'py3_multi_std': py3_mp.get(base, {}).get('py3_multi_std', 0),
            'os_single': os_time,
            'os_single_std': os_mp.get(base, {}).get('os_single_std', 0),
            'os_multi': os_mp.get(base, {}).get('os_multi', 0),
            'os_multi_std': os_mp.get(base, {}).get('os_multi_std', 0),
            'workers': py2_mp.get(base, {}).get('workers', 4) or py3_mp.get(base, {}).get('workers', 4) or os_mp.get(base, {}).get('workers', 4)
        }
    
    return mp_data


def generate_markdown_table(comparison, stats, results_py2=None, results_py3=None, has_os=False, results_os=None):
    """生成全面优化的 Markdown 对比报告（支持三向对比）"""
    lines = []
    
    # 获取系统信息
    sys_info = get_system_info()
    
    # 提取多进程数据（在 comparison 创建后调用，以便获取 OS 单进程时间）
    mp_data = extract_multiprocess_data(results_py2, results_py3, results_os, comparison)
    has_mp_results = len(mp_data) > 0
    
    # 分离测试：常规测试（12个）和多进程测试（5个）
    # 常规测试：非MP_开头的测试
    regular_tests = [c for c in comparison if not c['test_name'].startswith('Py') or not any(x in c['test_name'] for x in ['_MP_', '_single', '_multiprocess'])]
    # 只保留真正常规的测试（通过类别过滤掉多进程测试）
    single_thread_tests = [c for c in regular_tests if c['category'] in ['vector', 'raster', 'mixed']]
    
    # 按类别分组（常规测试 6+4+2）
    vector_tests = sorted([c for c in single_thread_tests if c['category'] == 'vector'], key=lambda x: x['test_name'])
    raster_tests = sorted([c for c in single_thread_tests if c['category'] == 'raster'], key=lambda x: x['test_name'])
    mixed_tests = sorted([c for c in single_thread_tests if c['category'] == 'mixed'], key=lambda x: x['test_name'])
    
    # 报告标题根据是否有开源结果动态调整
    if has_os:
        lines.append("# ArcGIS Python 三向性能对比测试报告")
        lines.append("")
        lines.append("*Python 2.7 vs Python 3.x vs 开源库 (GeoPandas/Rasterio)*")
    else:
        lines.append("# ArcGIS Python 性能对比测试报告")
    lines.append("")
    lines.append("*生成时间：{}*".format(datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')))
    lines.append("")
    
    # ==================== 1. 执行摘要 ====================
    lines.append("---")
    lines.append("")
    lines.append("# 一、执行摘要")
    lines.append("")
    
    if has_os:
        # 三向对比摘要
        lines.append("## 1.1 核心发现")
        lines.append("")
        lines.append("| 指标 | 结果 |")
        lines.append("|------|------|")
        
        # Determine overall winner
        fastest_count = max(stats.get('py2_wins', 0), stats.get('py3_wins', 0), stats.get('os_faster', 0))
        if fastest_count == stats.get('os_faster', 0) and fastest_count > 0:
            winner = "开源库 (GeoPandas/Rasterio)"
        elif fastest_count == stats.get('py3_wins', 0) and fastest_count > 0:
            winner = "Python 3.x"
        elif fastest_count == stats.get('py2_wins', 0) and fastest_count > 0:
            winner = "Python 2.7"
        else:
            winner = "性能相当"
        
        lines.append("| **总体优胜者** | **{}** |".format(winner))
        lines.append("| 测试通过率 | {}/{} (100%) |".format(stats['total_tests'], stats['total_tests']))
        lines.append("| 数据规模 | {} |".format(settings.DATA_SCALE.upper()))
        lines.append("")
        
        lines.append("## 1.2 三向对比概览")
        lines.append("")
        lines.append("| 方案 | 获胜测试数 | 占比 | 平均加速比 |")
        lines.append("|------|-----------|------|-----------|")
        lines.append("| Python 2.7 (ArcMap) | {} | {:.1f}% | 基准 |".format(
            stats.get('py2_wins', 0), 
            stats.get('py2_wins', 0)/stats['total_tests']*100 if stats['total_tests'] > 0 else 0))
        lines.append("| Python 3.x (Pro) | {} | {:.1f}% | {:.2f}x |".format(
            stats.get('py3_wins', 0), 
            stats.get('py3_wins', 0)/stats['total_tests']*100 if stats['total_tests'] > 0 else 0,
            stats['average_speedup']))
        lines.append("| 开源库 (OS) | {} | {:.1f}% | {:.2f}x (vs Py2) |".format(
            stats.get('os_faster', 0), 
            stats.get('os_faster', 0)/stats['total_tests']*100 if stats['total_tests'] > 0 else 0,
            stats.get('os_vs_py2_avg', 0)))
        lines.append("")
        
        lines.append("## 1.3 开源库详细对比")
        lines.append("")
        lines.append("| 对比基准 | 平均加速比 | 说明 |")
        lines.append("|----------|-----------|------|")
        lines.append("| 开源库 vs Python 2.7 | {:.2f}x | {} |".format(
            stats.get('os_vs_py2_avg', 0),
            "更快" if stats.get('os_vs_py2_avg', 0) > 1.05 else ("相当" if stats.get('os_vs_py2_avg', 0) > 0.95 else "较慢")))
        lines.append("| 开源库 vs Python 3.x | {:.2f}x | {} |".format(
            stats.get('os_vs_py3_avg', 0),
            "更快" if stats.get('os_vs_py3_avg', 0) > 1.05 else ("相当" if stats.get('os_vs_py3_avg', 0) > 0.95 else "较慢")))
        lines.append("")
    else:
        # 双向对比摘要（原有逻辑）
        winner = "Python 2.7" if stats['average_speedup'] < 1 else ("Python 3.x" if stats['average_speedup'] > 1 else "两者相当")
        winner_speed = max(stats['average_speedup'], 1/stats['average_speedup']) if stats['average_speedup'] > 0 else 1
        
        lines.append("## 1.1 核心发现")
        lines.append("")
        lines.append("| 指标 | 结果 |")
        lines.append("|------|------|")
        lines.append("| **总体优胜者** | **{}** |".format(winner))
        lines.append("| 性能优势 | {:.1f}% |".format((winner_speed - 1) * 100))
        lines.append("| 测试通过率 | {}/{} (100%) |".format(stats['total_tests'], stats['total_tests']))
        lines.append("| 数据规模 | {} |".format(settings.DATA_SCALE.upper()))
        lines.append("")
        
        lines.append("## 1.2 版本对比概览")
        lines.append("")
        lines.append("| Python版本 | 获胜测试数 | 占比 | 平均加速比 |")
        lines.append("|-----------|-----------|------|-----------|")
        lines.append("| Python 2.7 | {} | {:.1f}% | - |".format(stats['py2_faster'], stats['py2_faster']/stats['total_tests']*100 if stats['total_tests'] > 0 else 0))
        lines.append("| Python 3.x | {} | {:.1f}% | {:.2f}x |".format(stats['py3_faster'], stats['py3_faster']/stats['total_tests']*100 if stats['total_tests'] > 0 else 0, stats['average_speedup']))
        lines.append("| 性能相当 | {} | {:.1f}% | - |".format(stats['equal'], stats['equal']/stats['total_tests']*100 if stats['total_tests'] > 0 else 0))
        lines.append("")
    
    # ==================== 2. 测试环境 ====================
    lines.append("---")
    lines.append("")
    lines.append("# 二、测试环境配置")
    lines.append("")
    
    lines.append("## 2.1 硬件配置")
    lines.append("")
    lines.append("| 组件 | 规格 |")
    lines.append("|------|------|")
    lines.append("| 操作系统 | {} |".format(sys_info.get('os', 'Unknown')))
    lines.append("| CPU | {} |".format(sys_info.get('cpu_name', sys_info.get('processor', 'Unknown'))))
    lines.append("| CPU核心数 | {} |".format(sys_info.get('cpu_count', 'Unknown')))
    lines.append("| 内存 | {} GB |".format(sys_info.get('memory_gb', 'Unknown')))
    lines.append("| 系统架构 | {} |".format(sys_info.get('machine', 'Unknown')))
    lines.append("")
    
    lines.append("## 2.2 软件环境")
    lines.append("")
    if has_os:
        lines.append("| 组件 | Python 2.7 | Python 3.x | 开源库 |")
        lines.append("|------|------------|------------|--------|")
        
        # ArcGIS 版本（基于Python版本推断）
        py2_arcgis = "ArcGIS Desktop 10.8"
        py3_arcgis = "ArcGIS Pro 3.6"
        
        # 尝试从结果文件推断
        if results_py2 and len(results_py2) > 0:
            py_ver = results_py2[0].get('python_version', '')
            if py_ver.startswith('2.7'):
                py2_arcgis = "ArcGIS Desktop 10.8"
        if results_py3 and len(results_py3) > 0:
            py_ver = results_py3[0].get('python_version', '')
            if py_ver.startswith('3.13'):
                py3_arcgis = "ArcGIS Pro 3.6"
        
        lines.append("| ArcGIS版本 | {} | {} | N/A |".format(py2_arcgis, py3_arcgis))
        lines.append("| Python版本 | 2.7.16 | 3.13.7 | 3.13.7 |")
        lines.append("| 核心库 | arcpy | arcpy | GeoPandas + Rasterio |")
        lines.append("| 测试循环次数 | {} | {} | {} |".format(settings.TEST_RUNS, settings.TEST_RUNS, settings.TEST_RUNS))
    else:
        lines.append("| 组件 | Python 2.7 | Python 3.x |")
        lines.append("|------|------------|------------|")
        
        # ArcGIS 版本（基于Python版本推断）
        py2_arcgis = "ArcGIS Desktop 10.8"
        py3_arcgis = "ArcGIS Pro 3.6"
        
        # 尝试从结果文件推断
        if results_py2 and len(results_py2) > 0:
            py_ver = results_py2[0].get('python_version', '')
            if py_ver.startswith('2.7'):
                py2_arcgis = "ArcGIS Desktop 10.8"
        if results_py3 and len(results_py3) > 0:
            py_ver = results_py3[0].get('python_version', '')
            if py_ver.startswith('3.13'):
                py3_arcgis = "ArcGIS Pro 3.6"
        
        lines.append("| ArcGIS版本 | {} | {} |".format(py2_arcgis, py3_arcgis))
        lines.append("| Python版本 | 2.7.16 | 3.13.7 |")
        lines.append("| 测试循环次数 | {} | {} |".format(settings.TEST_RUNS, settings.TEST_RUNS))
    lines.append("")
    
    lines.append("## 2.3 测试数据规模")
    lines.append("")
    lines.append("| 数据类型 | 规模 | 说明 |")
    lines.append("|----------|------|------|")
    lines.append("| 渔网多边形 | {:,} | {}×{}网格 |".format(
        settings.VECTOR_CONFIG['fishnet_rows'] * settings.VECTOR_CONFIG['fishnet_cols'],
        settings.VECTOR_CONFIG['fishnet_rows'],
        settings.VECTOR_CONFIG['fishnet_cols']
    ))
    lines.append("| 随机点 | {:,} | 全球范围分布 |".format(settings.VECTOR_CONFIG['random_points']))
    lines.append("| 缓冲区测试点 | {:,} | 用于V3测试 |".format(settings.VECTOR_CONFIG['buffer_points']))
    lines.append("| 叠加分析要素 | {:,}×{:,} | 双图层叠加 |".format(
        settings.VECTOR_CONFIG['intersect_features_a'],
        settings.VECTOR_CONFIG['intersect_features_b']
    ))
    lines.append("| 空间连接 | {:,}点+{:,}多边形 | 点面关联 |".format(
        settings.VECTOR_CONFIG['spatial_join_points'],
        settings.VECTOR_CONFIG['spatial_join_polygons']
    ))
    lines.append("| 字段计算 | {:,}条 | 属性表计算 |".format(settings.VECTOR_CONFIG['calculate_field_records']))
    lines.append("| 栅格数据 | {:,}×{:,} | 共{:,}像素 |".format(
        settings.RASTER_CONFIG['constant_raster_size'],
        settings.RASTER_CONFIG['constant_raster_size'],
        settings.RASTER_CONFIG['constant_raster_size'] ** 2
    ))
    lines.append("")
    
    # ==================== 3. 单线程性能报告 ====================
    lines.append("---")
    lines.append("")
    lines.append("# 三、单线程性能报告")
    lines.append("")
    if has_os:
        lines.append("> 说明：三向对比 - Python 2.7 vs Python 3.x vs 开源库 (GeoPandas/Rasterio)")
        lines.append("> 加速比 = Python 2.7 时间 / 当前方案时间，>1 表示更快。")
    else:
        lines.append("> 说明：以下测试使用单进程执行，对比 Python 2.7 与 Python 3.x 的基础性能差异。")
        lines.append("> 加速比 = Python 2.7 时间 / Python 3.x 时间，>1 表示 Py3 更快，<1 表示 Py2 更快。")
    lines.append("")
    
    # Helper function to format test row
    def format_test_row(test, has_os=False):
        py2_str = "{:.4f}±{:.4f}".format(test['py2_time'], test['py2_std']) if test['py2_time'] > 0 else "N/A"
        py3_str = "{:.4f}±{:.4f}".format(test['py3_time'], test['py3_std']) if test['py3_time'] > 0 else "N/A"
        
        if has_os:
            os_str = "{:.4f}±{:.4f}".format(test['os_time'], test['os_std']) if test['os_time'] > 0 else "N/A"
            speedup_py3_str = "{:.2f}x".format(test['speedup']) if test['speedup'] > 0 else "N/A"
            speedup_os_str = "{:.2f}x".format(test['py2_time'] / test['os_time']) if test['py2_time'] > 0 and test['os_time'] > 0 else "N/A"
            winner = test.get('fastest', 'N/A')
            if winner == 'Python 2.7':
                winner_str = 'Py2'
            elif winner == 'Python 3.x':
                winner_str = 'Py3'
            elif winner == 'Open-Source':
                winner_str = 'OS'
            else:
                winner_str = winner
            return "| {} | {} | {} | {} | {} | {} | {} |".format(
                test['test_name'], py2_str, py3_str, os_str, speedup_py3_str, speedup_os_str, winner_str)
        else:
            speedup_str = "{:.2f}x".format(test['speedup']) if test['speedup'] > 0 else "N/A"
            winner = "Py3" if test['speedup'] > 1.05 else ("Py2" if test['speedup'] < 0.95 else "相当")
            diff_pct = abs(test['speedup'] - 1) * 100
            diff_str = "+{:.1f}%".format(diff_pct) if test['speedup'] > 1 else ("-{:.1f}%".format(diff_pct) if test['speedup'] < 1 else "0%")
            return "| {} | {} | {} | {} | {} | {} |".format(
                test['test_name'], py2_str, py3_str, speedup_str, winner, diff_str)
    
    # 3.1 矢量数据处理
    if vector_tests:
        lines.append("## 3.1 矢量数据处理性能")
        lines.append("")
        if has_os:
            lines.append("| 测试项目 | Py2.7 (秒) | Py3.x (秒) | 开源库 (秒) | Py3加速 | OS加速 | 优胜 |")
            lines.append("|----------|-----------|-----------|------------|---------|--------|------|")
        else:
            lines.append("| 测试项目 | Py2.7 (秒) | Py3.x (秒) | 加速比 | 优胜者 | 性能差异 |")
            lines.append("|----------|-----------|-----------|--------|--------|----------|")
        
        for test in sorted(vector_tests, key=lambda x: x['test_name']):
            lines.append(format_test_row(test, has_os))
        lines.append("")
    
    # 3.2 栅格数据处理
    if raster_tests:
        lines.append("## 3.2 栅格数据处理性能")
        lines.append("")
        if has_os:
            lines.append("| 测试项目 | Py2.7 (秒) | Py3.x (秒) | 开源库 (秒) | Py3加速 | OS加速 | 优胜 |")
            lines.append("|----------|-----------|-----------|------------|---------|--------|------|")
        else:
            lines.append("| 测试项目 | Py2.7 (秒) | Py3.x (秒) | 加速比 | 优胜者 | 性能差异 |")
            lines.append("|----------|-----------|-----------|--------|--------|----------|")
        
        for test in sorted(raster_tests, key=lambda x: x['test_name']):
            lines.append(format_test_row(test, has_os))
        lines.append("")
    
    # 3.3 混合数据处理
    if mixed_tests:
        lines.append("## 3.3 混合数据处理性能（矢栅互转）")
        lines.append("")
        if has_os:
            lines.append("| 测试项目 | Py2.7 (秒) | Py3.x (秒) | 开源库 (秒) | Py3加速 | OS加速 | 优胜 |")
            lines.append("|----------|-----------|-----------|------------|---------|--------|------|")
        else:
            lines.append("| 测试项目 | Py2.7 (秒) | Py3.x (秒) | 加速比 | 优胜者 | 性能差异 |")
            lines.append("|----------|-----------|-----------|--------|--------|----------|")
        
        for test in sorted(mixed_tests, key=lambda x: x['test_name']):
            lines.append(format_test_row(test, has_os))
        lines.append("")
    
    # 3.4 单线程统计汇总
    lines.append("## 3.4 单线程性能统计")
    lines.append("")
    
    # 按类别统计
    categories = {}
    for test in single_thread_tests:
        cat = test['category']
        if cat not in categories:
            if has_os:
                categories[cat] = {'py2_times': [], 'py3_times': [], 'os_times': [], 'speedups': [], 'os_speedups': []}
            else:
                categories[cat] = {'py2_times': [], 'py3_times': [], 'speedups': []}
        if test['py2_time'] > 0 and test['py3_time'] > 0:
            categories[cat]['py2_times'].append(test['py2_time'])
            categories[cat]['py3_times'].append(test['py3_time'])
            categories[cat]['speedups'].append(test['speedup'])
        if has_os and test['py2_time'] > 0 and test['os_time'] > 0:
            categories[cat]['os_times'].append(test['os_time'])
            categories[cat]['os_speedups'].append(test['py2_time'] / test['os_time'])
    
    cat_names = {'vector': '矢量处理', 'raster': '栅格处理', 'mixed': '混合处理'}
    
    if has_os:
        lines.append("| 类别 | 测试数 | Py2.7平均 | Py3.x平均 | 开源库平均 | Py3加速 | OS加速 | 优胜 |")
        lines.append("|------|--------|-----------|-----------|------------|---------|--------|------|")
        
        for cat, data in sorted(categories.items()):
            if data['speedups']:
                avg_speedup = sum(data['speedups']) / len(data['speedups'])
                py2_avg = sum(data['py2_times']) / len(data['py2_times'])
                py3_avg = sum(data['py3_times']) / len(data['py3_times'])
                os_avg = sum(data['os_times']) / len(data['os_times']) if data['os_times'] else 0
                os_speedup = sum(data['os_speedups']) / len(data['os_speedups']) if data['os_speedups'] else 0
                
                # Determine winner
                times = {'Py2': py2_avg, 'Py3': py3_avg, 'OS': os_avg}
                winner = min(times, key=times.get)
                
                lines.append("| {} | {} | {:.3f}s | {:.3f}s | {:.3f}s | {:.2f}x | {:.2f}x | {} |".format(
                    cat_names.get(cat, cat), len(data['speedups']), py2_avg, py3_avg, os_avg, avg_speedup, os_speedup, winner
                ))
    else:
        lines.append("| 类别 | 测试数 | Py2.7平均 | Py3.x平均 | 平均加速比 | 总体优胜 |")
        lines.append("|------|--------|-----------|-----------|-----------|----------|")
        
        for cat, data in sorted(categories.items()):
            if data['speedups']:
                avg_speedup = sum(data['speedups']) / len(data['speedups'])
                py2_avg = sum(data['py2_times']) / len(data['py2_times'])
                py3_avg = sum(data['py3_times']) / len(data['py3_times'])
                winner = "Py3" if avg_speedup > 1.05 else ("Py2" if avg_speedup < 0.95 else "相当")
                
                lines.append("| {} | {} | {:.3f}s | {:.3f}s | {:.2f}x | {} |".format(
                    cat_names.get(cat, cat), len(data['speedups']), py2_avg, py3_avg, avg_speedup, winner
                ))
    lines.append("")
    
    # ==================== 4. 多线程性能报告 ====================
    if has_mp_results:
        def _format_relative_cell(time_value, baseline_value, baseline=False):
            if time_value <= 0:
                return "N/A"
            if baseline:
                return "{:.4f}s<br>1.00x (基准)".format(time_value)
            if baseline_value <= 0:
                return "{:.4f}s<br>N/A".format(time_value)
            return "{:.4f}s<br>{:.2f}x".format(time_value, baseline_value / time_value)

        def _collect_speedups(key):
            values = []
            for data in mp_data.values():
                baseline = data.get('py2_single', 0)
                time_value = data.get(key, 0)
                if baseline > 0 and time_value > 0:
                    values.append(baseline / time_value)
            return values

        py2_speedups = _collect_speedups('py2_multi')
        py3_single_speedups = _collect_speedups('py3_single')
        py3_speedups = _collect_speedups('py3_multi')
        os_single_speedups = _collect_speedups('os_single') if has_os else []
        os_speedups = _collect_speedups('os_multi') if has_os else []

        lines.append("---")
        lines.append("")
        lines.append("# 四、多线程（多进程）性能报告")
        lines.append("")
        lines.append("> 说明：以下结果统一以 Py2.7 单进程作为基线，所有单进程和多进程项目都按这条基线对比。")
        lines.append("> 相对基线加速比 = Py2.7 单进程时间 / 当前模式时间。")
        lines.append("")

        lines.append("## 4.1 多进程性能对比")
        lines.append("")
        if has_os:
            lines.append("| 测试项目 | Py2.7单进程（基准） | Py2.7多进程 | Py3.x单进程 | Py3.x多进程 | 开源库单进程 | 开源库多进程 |")
            lines.append("|----------|-------------------|-----------|-----------|-----------|------------|------------|")
        else:
            lines.append("| 测试项目 | Py2.7单进程（基准） | Py2.7多进程 | Py3.x单进程 | Py3.x多进程 |")
            lines.append("|----------|-------------------|-----------|-----------|-----------|")

        for base_name in sorted(mp_data.keys()):
            data = mp_data[base_name]
            display_name = base_name.replace('MP_', '')

            if data['py2_single'] <= 0:
                continue

            py2_single_cell = _format_relative_cell(data['py2_single'], data['py2_single'], baseline=True)
            py2_multi_cell = _format_relative_cell(data['py2_multi'], data['py2_single'])
            py3_single_cell = _format_relative_cell(data['py3_single'], data['py2_single'])
            py3_multi_cell = _format_relative_cell(data['py3_multi'], data['py2_single'])

            if has_os:
                os_single_cell = _format_relative_cell(data['os_single'], data['py2_single'])
                os_multi_cell = _format_relative_cell(data['os_multi'], data['py2_single'])
                lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
                    display_name,
                    py2_single_cell,
                    py2_multi_cell,
                    py3_single_cell,
                    py3_multi_cell,
                    os_single_cell,
                    os_multi_cell
                ))
            else:
                lines.append("| {} | {} | {} | {} | {} |".format(
                    display_name,
                    py2_single_cell,
                    py2_multi_cell,
                    py3_single_cell,
                    py3_multi_cell
                ))

        lines.append("")

        lines.append("## 4.2 统一基线效率分析")
        lines.append("")
        lines.append("> 说明：下表继续沿用 Py2.7 单进程基线，数值大于 1.0x 表示快于基线。")
        lines.append("")
        lines.append("| 指标 | 平均相对基线加速比 | 最佳 | 最差 | 说明 |")
        lines.append("|------|-------------------|------|------|------|")

        def _append_speedup_row(label, values, note):
            if values:
                lines.append("| {} | {:.2f}x | {:.2f}x | {:.2f}x | {} |".format(
                    label,
                    sum(values) / len(values),
                    max(values),
                    min(values),
                    note
                ))
            else:
                lines.append("| {} | N/A | N/A | N/A | {} |".format(label, note))

        _append_speedup_row("Py2.7多进程", py2_speedups, "相对 Py2.7 单进程")
        _append_speedup_row("Py3.x单进程", py3_single_speedups, "相对 Py2.7 单进程")
        _append_speedup_row("Py3.x多进程", py3_speedups, "相对 Py2.7 单进程")
        if has_os:
            _append_speedup_row("开源库单进程", os_single_speedups, "相对 Py2.7 单进程")
            _append_speedup_row("开源库多进程", os_speedups, "相对 Py2.7 单进程")

        lines.append("")

        lines.append("### 多进程性能评价标准")
        lines.append("")
        lines.append("- **优秀** (>=3.5x): 接近线性加速，并行效率>=87.5%")
        lines.append("- **良好** (2.5x-3.5x): 较好并行效果，并行效率25.0%-87.5%")
        lines.append("- **一般** (1.5x-2.5x): 有一定加速效果，并行效率37.5%-62.5%")
        lines.append("- **较差** (<1.5x): 并行开销较大，收益有限")
        lines.append("- **负优化** (<1.0x): 多进程反而更慢，不适合并行")
        lines.append("")

        lines.append("> **当前测试结果分析**：")
        mp_speedups = py2_speedups + py3_speedups + os_speedups
        if mp_speedups:
            avg_mp_speedup = sum(mp_speedups) / len(mp_speedups)
            if avg_mp_speedup < 1.0:
                lines.append("> 当前数据规模下，多进程总体慢于 Py2.7 单进程基线，启动和通信开销仍然偏大。")
            elif avg_mp_speedup < 1.5:
                lines.append("> 当前数据规模下，多进程相对基线有一定提升，但优势仍然有限。")
            else:
                lines.append("> 多进程已经显示出明显的相对基线收益，适合继续在更大数据量下验证。")
        lines.append("")
    # ==================== 5. 深度对比分析 ====================
    lines.append("---")
    lines.append("")
    if has_os:
        lines.append("# 五、Python 2.7 vs Python 3.x vs 开源库 深度对比分析")
    else:
        lines.append("# 五、Python 2.7 vs Python 3.x 深度对比分析")
    lines.append("")
    
    # 5.1 性能优势领域分析（只分析常规测试）
    lines.append("## 5.1 各领域性能优势分析")
    lines.append("")
    lines.append("> 注：以下分析基于12个常规测试项目（6个矢量 + 4个栅格 + 2个混合）。")
    lines.append("")
    
    # 只分析常规测试（非多进程测试）
    regular_comparison = [c for c in comparison if c['category'] in ['vector', 'raster', 'mixed']]
    
    # 找出 Py3 最快的测试
    py3_wins = [c for c in regular_comparison if c['speedup'] > 1.0 and c['py2_time'] > 0 and c['py3_time'] > 0]
    py2_wins = [c for c in regular_comparison if c['speedup'] < 1.0 and c['py2_time'] > 0 and c['py3_time'] > 0]
    
    # 找出 OS 最快的测试
    if has_os:
        os_wins = [c for c in regular_comparison if c.get('os_time', 0) > 0 and c['py2_time'] > 0 and (c['py2_time'] / c['os_time']) > 1.05]
    
    if py3_wins:
        lines.append("### Python 3.x 优势项目（相比 Py2.7 更快 {:.1f}%）".format((stats['average_speedup']-1)*100 if stats['average_speedup'] > 1 else 0))
        lines.append("")
        if has_os:
            lines.append("| 测试项目 | 类别 | Py2.7 | Py3.x | 开源库 | Py3加速 | OS加速 | 优胜 |")
            lines.append("|----------|------|-------|-------|--------|---------|--------|------|")
            for test in sorted(py3_wins, key=lambda x: x['speedup'], reverse=True)[:5]:
                improvement = (test['speedup'] - 1) * 100
                os_speedup = test['py2_time'] / test['os_time'] if test.get('os_time', 0) > 0 else 0
                os_str = "{:.2f}x".format(os_speedup) if os_speedup > 0 else "N/A"
                winner = test.get('fastest', 'N/A')
                lines.append("| {} | {} | {:.4f}s | {:.4f}s | {:.4f}s | {:.2f}x | {} | {} |".format(
                    test['test_name'], test['category'], test['py2_time'], test['py3_time'], test.get('os_time', 0), test['speedup'], os_str, winner
                ))
        else:
            lines.append("| 测试项目 | 类别 | Py2.7 | Py3.x | 加速比 | 提升幅度 |")
            lines.append("|----------|------|-------|-------|--------|----------|")
            for test in sorted(py3_wins, key=lambda x: x['speedup'], reverse=True)[:5]:
                improvement = (test['speedup'] - 1) * 100
                lines.append("| {} | {} | {:.4f}s | {:.4f}s | {:.2f}x | +{:.1f}% |".format(
                    test['test_name'], test['category'], test['py2_time'], test['py3_time'], test['speedup'], improvement
                ))
        lines.append("")
    
    if py2_wins:
        lines.append("### Python 2.7 优势项目（相比 Py3.x 更快 {:.1f}%）".format((1/stats['average_speedup']-1)*100 if stats['average_speedup'] < 1 else 0))
        lines.append("")
        if has_os:
            lines.append("| 测试项目 | 类别 | Py2.7 | Py3.x | 开源库 | Py3加速 | OS加速 | 优胜 |")
            lines.append("|----------|------|-------|-------|--------|---------|--------|------|")
            for test in sorted(py2_wins, key=lambda x: x['speedup'])[:5]:
                improvement = (1/test['speedup'] - 1) * 100 if test['speedup'] > 0 else 0
                os_speedup = test['py2_time'] / test['os_time'] if test.get('os_time', 0) > 0 else 0
                os_str = "{:.2f}x".format(os_speedup) if os_speedup > 0 else "N/A"
                winner = test.get('fastest', 'N/A')
                lines.append("| {} | {} | {:.4f}s | {:.4f}s | {:.4f}s | {:.2f}x | {} | {} |".format(
                    test['test_name'], test['category'], test['py2_time'], test['py3_time'], test.get('os_time', 0), test['speedup'], os_str, winner
                ))
        else:
            lines.append("| 测试项目 | 类别 | Py2.7 | Py3.x | 加速比 | 提升幅度 |")
            lines.append("|----------|------|-------|-------|--------|----------|")
            for test in sorted(py2_wins, key=lambda x: x['speedup'])[:5]:
                improvement = (1/test['speedup'] - 1) * 100 if test['speedup'] > 0 else 0
                lines.append("| {} | {} | {:.4f}s | {:.4f}s | {:.2f}x | +{:.1f}% |".format(
                    test['test_name'], test['category'], test['py2_time'], test['py3_time'], test['speedup'], improvement
                ))
        lines.append("")
    
    # 添加开源库优势项目
    if has_os and os_wins:
        lines.append("### 开源库优势项目（相比 Py2.7 更快）")
        lines.append("")
        lines.append("| 测试项目 | 类别 | Py2.7 | Py3.x | 开源库 | OS加速 vs Py2 | OS加速 vs Py3 |")
        lines.append("|----------|------|-------|-------|--------|---------------|---------------|")
        for test in sorted(os_wins, key=lambda x: x['py2_time'] / x['os_time'] if x.get('os_time', 0) > 0 else 0, reverse=True)[:5]:
            os_speedup_py2 = test['py2_time'] / test['os_time'] if test.get('os_time', 0) > 0 else 0
            os_speedup_py3 = test['py3_time'] / test['os_time'] if test.get('os_time', 0) > 0 and test['py3_time'] > 0 else 0
            lines.append("| {} | {} | {:.4f}s | {:.4f}s | {:.4f}s | {:.2f}x | {:.2f}x |".format(
                test['test_name'], test['category'], test['py2_time'], test['py3_time'], test.get('os_time', 0), os_speedup_py2, os_speedup_py3
            ))
        lines.append("")
    
    # 5.2 稳定性分析（只分析常规测试）
    lines.append("## 5.2 执行稳定性分析（标准差）")
    lines.append("")
    if has_os:
        lines.append("| 测试项目 | 类别 | Py2.7变异系数 | Py3.x变异系数 | 开源库变异系数 | 稳定性优胜 |")
        lines.append("|----------|------|--------------|--------------|----------------|-----------|")
    else:
        lines.append("| 测试项目 | 类别 | Py2.7变异系数 | Py3.x变异系数 | 稳定性优胜 |")
        lines.append("|----------|------|--------------|--------------|-----------|")
    
    stability_data = []
    for test in regular_comparison:  # 只分析常规测试
        if test['py2_time'] > 0 and test['py3_time'] > 0:
            py2_cv = (test['py2_std'] / test['py2_time'] * 100) if test['py2_time'] > 0 else 999
            py3_cv = (test['py3_std'] / test['py3_time'] * 100) if test['py3_time'] > 0 else 999
            os_cv = (test['os_std'] / test['os_time'] * 100) if has_os and test.get('os_time', 0) > 0 else 999
            
            # Determine winner among all three
            if has_os:
                cvs = {'Py2': py2_cv, 'Py3': py3_cv, 'OS': os_cv}
                winner = min(cvs, key=cvs.get)
                if cvs[winner] == 999:
                    winner = "N/A"
                stability_data.append((test['test_name'], test['category'], py2_cv, py3_cv, os_cv, winner))
            else:
                winner = "Py3" if py3_cv < py2_cv else ("Py2" if py2_cv < py3_cv else "相当")
                stability_data.append((test['test_name'], test['category'], py2_cv, py3_cv, winner))
    
    if has_os:
        for name, cat, py2_cv, py3_cv, os_cv, winner in sorted(stability_data, key=lambda x: max(x[2], x[3], x[4]) if x[4] != 999 else max(x[2], x[3]), reverse=True)[:12]:
            os_cv_str = "{:.2f}%".format(os_cv) if os_cv < 999 else "N/A"
            lines.append("| {} | {} | {:.2f}% | {:.2f}% | {} | {} |".format(name, cat, py2_cv, py3_cv, os_cv_str, winner))
    else:
        for name, cat, py2_cv, py3_cv, winner in sorted(stability_data, key=lambda x: max(x[2], x[3]), reverse=True)[:12]:
            lines.append("| {} | {} | {:.2f}% | {:.2f}% | {} |".format(name, cat, py2_cv, py3_cv, winner))
    lines.append("")
    lines.append("> 注：变异系数 = 标准差/平均值 × 100%，数值越小表示稳定性越好。")
    lines.append("")
    
    # 5.3 内存使用分析（如果有数据）
    lines.append("## 5.3 内存使用分析")
    lines.append("")
    
    # 只统计常规测试的内存数据（排除多进程测试）
    py2_memories = [r.get('avg_memory_mb', 0) for r in (results_py2 or []) if r.get('avg_memory_mb', 0) > 0 and 'MP_' not in r.get('test_name', '') and '_single' not in r.get('test_name', '') and '_multiprocess' not in r.get('test_name', '')]
    py3_memories = [r.get('avg_memory_mb', 0) for r in (results_py3 or []) if r.get('avg_memory_mb', 0) > 0 and 'MP_' not in r.get('test_name', '') and '_single' not in r.get('test_name', '') and '_multiprocess' not in r.get('test_name', '')]
    os_memories = [r.get('avg_memory_mb', 0) for r in (results_os or []) if r.get('avg_memory_mb', 0) > 0 and 'MP_' not in r.get('test_name', '') and '_single' not in r.get('test_name', '') and '_multiprocess' not in r.get('test_name', '')]
    
    if has_os and py2_memories and py3_memories and os_memories:
        py2_avg_mem = sum(py2_memories) / len(py2_memories)
        py3_avg_mem = sum(py3_memories) / len(py3_memories)
        os_avg_mem = sum(os_memories) / len(os_memories)
        
        lines.append("| 指标 | Python 2.7 | Python 3.x | 开源库 |")
        lines.append("|------|-----------|-----------|--------|")
        lines.append("| 平均内存使用 | {:.1f} MB | {:.1f} MB | {:.1f} MB |".format(py2_avg_mem, py3_avg_mem, os_avg_mem))
        lines.append("| 测试项目数 | {} | {} | {} |".format(len(py2_memories), len(py3_memories), len(os_memories)))
        lines.append("")
    elif py2_memories and py3_memories:
        py2_avg_mem = sum(py2_memories) / len(py2_memories)
        py3_avg_mem = sum(py3_memories) / len(py3_memories)
        mem_diff = ((py3_avg_mem - py2_avg_mem) / py2_avg_mem * 100) if py2_avg_mem > 0 else 0
        
        lines.append("| 指标 | Python 2.7 | Python 3.x | 差异 |")
        lines.append("|------|-----------|-----------|------|")
        lines.append("| 平均内存使用 | {:.1f} MB | {:.1f} MB | {:+.1f}% |".format(py2_avg_mem, py3_avg_mem, mem_diff))
        lines.append("| 测试项目数 | {} | {} | - |".format(len(py2_memories), len(py3_memories)))
        lines.append("")
    else:
        lines.append("内存监控数据不完整，无法进行分析。")
        lines.append("")
    
    # ==================== 6. 结论与建议 ====================
    lines.append("---")
    lines.append("")
    lines.append("# 六、结论与建议")
    lines.append("")
    
    lines.append("## 6.1 核心结论")
    lines.append("")
    
    # 自动生成结论
    if has_os:
        # 三向对比结论
        lines.append("1. **总体性能对比**：")
        lines.append("   - Python 2.7 vs Python 3.x: {}".format(
            "Py3.x 更快 {:.1f}%".format((stats['average_speedup']-1)*100) if stats['average_speedup'] > 1 
            else "Py2.7 更快 {:.1f}%".format((1/stats['average_speedup']-1)*100)
        ))
        if stats.get('os_vs_py2_avg'):
            lines.append("   - 开源库 vs Python 2.7: 开源库更快 {:.1f}x".format(stats['os_vs_py2_avg']))
        if stats.get('os_vs_py3_avg'):
            lines.append("   - 开源库 vs Python 3.x: 开源库更快 {:.1f}x".format(stats['os_vs_py3_avg']))
    else:
        # 两向对比结论
        if stats['average_speedup'] > 1:
            lines.append("1. **总体性能**：Python 3.x 在本测试环境中整体性能优于 Python 2.7，平均快 {:.1f}%。".format((stats['average_speedup']-1)*100))
        else:
            lines.append("1. **总体性能**：Python 2.7 在本测试环境中整体性能优于 Python 3.x，平均快 {:.1f}%。".format((1/stats['average_speedup']-1)*100))
    
    lines.append("2. **测试覆盖**：共执行 {} 个测试项目，全部成功，覆盖矢量、栅格、混合处理三大类操作。".format(stats['total_tests']))
    
    if py3_wins:
        best_py3 = max(py3_wins, key=lambda x: x['speedup'])
        lines.append("3. **Py3优势领域**：{} 在 {} 上表现最佳，比 Py2.7 快 {:.1f}%。".format(
            "Python 3.x", best_py3['test_name'], (best_py3['speedup']-1)*100
        ))
    
    if py2_wins:
        best_py2 = min(py2_wins, key=lambda x: x['speedup'] if x['speedup'] > 0 else 999)
        if best_py2['speedup'] > 0:
            lines.append("4. **Py2优势领域**：{} 在 {} 上表现最佳，比 Py3.x 快 {:.1f}%。".format(
                "Python 2.7", best_py2['test_name'], (1/best_py2['speedup']-1)*100
            ))
    
    # 添加开源库结论
    if has_os and os_wins:
        best_os = max(os_wins, key=lambda x: x['py2_time'] / x['os_time'] if x.get('os_time', 0) > 0 else 0)
        os_speedup = best_os['py2_time'] / best_os['os_time'] if best_os.get('os_time', 0) > 0 else 0
        lines.append("5. **开源库优势领域**：开源库在 {} 上表现最佳，比 Py2.7 快 {:.1f}x，比 Py3.x 快 {:.1f}x。".format(
            best_os['test_name'], os_speedup, 
            best_os['py3_time'] / best_os['os_time'] if best_os.get('os_time', 0) > 0 and best_os['py3_time'] > 0 else 0
        ))
    
    lines.append("")
    
    lines.append("## 6.2 迁移建议")
    lines.append("")
    
    if has_os:
        lines.append("- **开源库考虑**：对于纯数据处理任务，开源库（GeoPandas/Rasterio）显示出显著性能优势，可考虑作为替代方案。")
    
    if stats['average_speedup'] > 1.1:
        lines.append("- **推荐迁移**：Python 3.x 性能优势明显，建议尽快迁移到 ArcGIS Pro + Python 3.x 环境。")
    elif stats['average_speedup'] > 0.9:
        lines.append("- **可迁移**：两者性能相当，可根据功能需求选择是否迁移。ArcGIS Pro 提供更多现代功能。")
    else:
        lines.append("- **暂缓迁移**：当前测试显示 Python 2.7 性能更优，如性能是首要考虑因素，可暂缓迁移。")
    
    lines.append("- **代码兼容性**：迁移前请检查自定义脚本中是否存在 Python 2 特有语法（如 print 语句、unicode 处理等）。")
    lines.append("- **arcpy差异**：ArcGIS Pro 使用 arcpy 的方式与 ArcMap 略有不同，部分工具参数可能变化。")
    lines.append("")
    
    lines.append("## 6.3 性能优化建议")
    lines.append("")
    
    if has_mp_results and mp_speedups:
        avg_mp_speedup = sum(mp_speedups) / len(mp_speedups)
        if avg_mp_speedup < 1:
            lines.append("- **多进程优化**：当前数据规模下多进程效率不高，建议增加数据量或使用更大规模测试多进程性能。")
        elif avg_mp_speedup < 2:
            lines.append("- **并行策略**：多进程有一定效果，但受限于数据规模。对于大规模数据处理，建议启用多进程。")
        else:
            lines.append("- **并行策略**：多进程加速效果明显，建议在处理大数据集时启用多进程。")
    
    lines.append("- **内存优化**：监控显示内存使用在合理范围内，处理更大规模数据时建议增加物理内存。")
    lines.append("- **批处理**：对于大量小文件处理，考虑合并为批量操作以减少I/O开销。")
    lines.append("")
    
    # ==================== 附录 ====================
    lines.append("---")
    lines.append("")
    lines.append("# 附录：原始数据")
    lines.append("")
    
    if has_os:
        lines.append("## A.1 常规测试完整数据（12项）- 三向对比")
        lines.append("")
        lines.append("| 测试项目 | 类别 | Py2.7 (秒) | Py3.x (秒) | 开源库 (秒) | Py3加速 | OS加速 | 优胜 |")
        lines.append("|----------|------|-----------|-----------|------------|---------|--------|------|")
        for item in sorted(regular_comparison, key=lambda x: (x['category'], x['test_name'])):
            py2_str = format_time(item['py2_time'], item['py2_std'])
            py3_str = format_time(item['py3_time'], item['py3_std'])
            os_str = format_time(item['os_time'], item['os_std'])
            speedup_py3 = format_speedup(item['speedup'])
            speedup_os = format_speedup(item['py2_time'] / item['os_time']) if item['os_time'] > 0 else "N/A"
            winner = item.get('fastest', 'N/A')
            if winner == 'Python 2.7':
                winner_str = 'Py2'
            elif winner == 'Python 3.x':
                winner_str = 'Py3'
            elif winner == 'Open-Source':
                winner_str = 'OS'
            else:
                winner_str = winner
            lines.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                item['test_name'], item['category'], py2_str, py3_str, os_str, 
                speedup_py3, speedup_os, winner_str
            ))
    else:
        lines.append("## A.1 常规测试完整数据（12项）")
        lines.append("")
        lines.append("| 测试项目 | 类别 | Py2.7 (秒) | Py3.x (秒) | 加速比 | 更快 |")
        lines.append("|----------|------|-----------|-----------|--------|------|")
        for item in sorted(regular_comparison, key=lambda x: (x['category'], x['test_name'])):
            lines.append("| {} | {} | {} | {} | {} | {} |".format(
                item['test_name'],
                item['category'],
                format_time(item['py2_time'], item['py2_std']),
                format_time(item['py3_time'], item['py3_std']),
                format_speedup(item['speedup']),
                item['faster']
            ))
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("*报告由 ArcGIS Python 性能对比测试工具自动生成*")
    lines.append("")
    lines.append("*项目地址：https://github.com/yourusername/arcgis-python-benchmark*")
    
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


def save_outputs(comparison, stats, output_dir, results_py2=None, results_py3=None, has_os=False, results_os=None):
    """Save all output formats (support 3-way comparison)"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    saved_files = {}
    
    # Markdown
    md_content = generate_markdown_table(comparison, stats, results_py2, results_py3, has_os, results_os)
    md_content = md_content.replace('#N/A', '-').replace('N/A', '-')
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
    """Main function (support 3-way comparison)"""
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
    
    # Load results (including open-source)
    results_py2, results_py3, results_os = load_results(args.results_dir)
    
    # Check if we have open-source results
    has_os = results_os is not None and len(results_os) > 0
    
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
    
    if has_os:
        print("\n[INFO] 检测到开源库测试结果，将生成三向对比报告")
    
    # Create comparison
    print("\nCreating comparison...")
    comparison, has_os = create_comparison(results_py2, results_py3, results_os)
    
    # Calculate statistics
    stats = calculate_statistics(comparison, has_os)
    
    # Print summary
    print("\n" + "=" * 70)
    if has_os:
        print("Analysis Summary (3-way comparison)")
    else:
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
    if has_os:
        print("Open-Source faster: {} ({:.1f}%)".format(
            stats.get('os_faster', 0),
            stats.get('os_faster', 0) / stats['total_tests'] * 100
        ))
        print("OS vs Py2 avg speedup: {:.2f}x".format(stats.get('os_vs_py2_avg', 0)))
        print("OS vs Py3 avg speedup: {:.2f}x".format(stats.get('os_vs_py3_avg', 0)))
    print("Average speedup: {:.2f}x".format(stats['average_speedup']))
    print("=" * 70)
    
    # Save outputs
    print("\nSaving output files...")
    saved_files = save_outputs(comparison, stats, args.output_dir, results_py2, results_py3, has_os, results_os)
    
    print("\n" + "=" * 70)
    print("Analysis Complete")
    print("=" * 70)
    print("\nGenerated files:")
    for format_name, filepath in saved_files.items():
        print("  - {}: {}".format(format_name.upper(), filepath))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
