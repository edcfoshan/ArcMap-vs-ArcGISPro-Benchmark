#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Main script to run ArcGIS Performance Benchmarks
Compatible with Python 2.7 and 3.x

Usage:
    Python 2.7: C:\\Python27\\ArcGIS10.8\\python.exe run_benchmarks.py [--category vector|raster|mixed|all]
    Python 3.x: "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe" run_benchmarks.py [--category vector|raster|mixed|all]
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import argparse
import json

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from utils.arcgis_env import ArcGISEnvironment
from utils.result_exporter import ResultExporter

# Import ArcGIS-based benchmarks (may fail if arcpy not available)
try:
    from benchmarks.vector_benchmarks import VectorBenchmarks
    from benchmarks.raster_benchmarks import RasterBenchmarks
    from benchmarks.mixed_benchmarks import MixedBenchmarks
    from benchmarks.multiprocess_tests import get_multiprocess_benchmarks
    HAS_ARCPY_BENCHMARKS = True
except ImportError:
    HAS_ARCPY_BENCHMARKS = False
    VectorBenchmarks = None
    RasterBenchmarks = None
    MixedBenchmarks = None
    get_multiprocess_benchmarks = None

# Import open-source benchmarks (Python 3.x only)
try:
    from benchmarks.vector_benchmarks_os import VectorBenchmarksOS
    from benchmarks.raster_benchmarks_os import RasterBenchmarksOS
    from benchmarks.mixed_benchmarks_os import MixedBenchmarksOS
    HAS_OS_BENCHMARKS = True
except ImportError:
    HAS_OS_BENCHMARKS = False


def check_arcpy():
    """Check if arcpy is available"""
    try:
        import arcpy
        return True
    except ImportError:
        return False


def _is_timestamp_name(name):
    """Check whether a folder name looks like YYYYMMDD_HHMMSS."""
    return (
        len(name) == 15 and
        name[8] == '_' and
        name[:8].isdigit() and
        name[9:].isdigit()
    )


def _extract_timestamp_root(output_dir):
    """Extract timestamp root and its base temp directory from an output path."""
    normalized_output_dir = os.path.normpath(output_dir)
    base_name = os.path.basename(normalized_output_dir)

    if _is_timestamp_name(base_name):
        timestamp_dir = normalized_output_dir
        return timestamp_dir, os.path.dirname(timestamp_dir)

    parent_dir = os.path.dirname(normalized_output_dir)
    grandparent_dir = os.path.dirname(parent_dir)

    if base_name.lower() in ['raw', 'tables', 'results'] and _is_timestamp_name(os.path.basename(parent_dir)):
        timestamp_dir = parent_dir
        return timestamp_dir, os.path.dirname(timestamp_dir)

    if base_name.lower() == 'raw' and os.path.basename(parent_dir).lower() == 'results' and _is_timestamp_name(os.path.basename(grandparent_dir)):
        timestamp_dir = grandparent_dir
        return timestamp_dir, os.path.dirname(timestamp_dir)

    if base_name.lower() == 'tables' and os.path.basename(parent_dir).lower() == 'results' and _is_timestamp_name(os.path.basename(grandparent_dir)):
        timestamp_dir = grandparent_dir
        return timestamp_dir, os.path.dirname(timestamp_dir)

    return None, None


def _is_opensource_benchmark(benchmark):
    """Return True when the benchmark belongs to the open-source set."""
    name = getattr(benchmark, 'name', '')
    category = getattr(benchmark, 'category', '')
    return name.endswith('_OS') or category.endswith('_os')


def _build_group_output_dir(output_root, group_name):
    """Build a version-specific output directory under the session root."""
    return os.path.join(output_root, 'data', group_name)


def _activate_group_output_dir(output_root, group_name):
    """Switch benchmark globals to the group-specific working directory."""
    group_dir = _build_group_output_dir(output_root, group_name)
    if not os.path.exists(group_dir):
        os.makedirs(group_dir)

    settings.DATA_DIR = group_dir
    settings.RAW_RESULTS_DIR = group_dir
    settings.SCRATCH_WORKSPACE = os.path.join(group_dir, 'scratch')
    if not os.path.exists(settings.SCRATCH_WORKSPACE):
        os.makedirs(settings.SCRATCH_WORKSPACE)

    return group_dir


def _split_benchmark_groups(benchmarks):
    """Split benchmarks into ArcPy and open-source groups."""
    arcpy_benchmarks = []
    opensource_benchmarks = []

    for benchmark in benchmarks:
        if _is_opensource_benchmark(benchmark):
            opensource_benchmarks.append(benchmark)
        else:
            arcpy_benchmarks.append(benchmark)

    return arcpy_benchmarks, opensource_benchmarks


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='ArcGIS Python Performance Benchmark',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  Run all benchmarks:
    python run_benchmarks.py
  
  Run only vector benchmarks:
    python run_benchmarks.py --category vector
  
  Run with custom iterations:
    python run_benchmarks.py --runs 10 --warmup 2
        '''
    )
    
    parser.add_argument(
        '--category',
        choices=['vector', 'raster', 'mixed', 'all'],
        default='all',
        help='Benchmark category to run (default: all)'
    )
    
    parser.add_argument(
        '--scale',
        choices=['tiny', 'small', 'standard', 'medium', 'large'],
        default=None,
        help='Data scale for testing (default: from settings.py)'
    )
    
    parser.add_argument(
        '--runs',
        type=int,
        default=None,
        help='Number of benchmark runs (default: from settings.py)'
    )
    
    parser.add_argument(
        '--warmup',
        type=int,
        default=None,
        help='Number of warmup runs (default: from settings.py)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for results (default: from settings.py)'
    )
    
    parser.add_argument(
        '--generate-data',
        action='store_true',
        help='Generate test data before running benchmarks'
    )
    
    parser.add_argument(
        '--multiprocess',
        action='store_true',
        help='Run multiprocess comparison benchmarks'
    )
    
    parser.add_argument(
        '--mp-workers',
        type=int,
        default=4,
        help='Number of worker processes for multiprocess tests (default: 4)'
    )
    
    parser.add_argument(
        '--opensource',
        action='store_true',
        help='Run open-source library benchmarks (Python 3.x only)'
    )
    
    # Python 2/3 compatibility for argparse
    if len(sys.argv) == 1:
        return parser.parse_args([])
    
    return parser.parse_args()


def generate_test_data():
    """Generate test data"""
    print("\n" + "=" * 60)
    print("Generating Test Data")
    print("=" * 60)

    try:
        # Add script directory to path to ensure data module can be imported
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        from data.generate_test_data import TestDataGenerator
        generator = TestDataGenerator()
        datasets = generator.generate_all()
        print("\nTest data generated successfully")
        return True
    except Exception as e:
        print("\nError generating test data: {}".format(str(e)))
        import traceback
        traceback.print_exc()
        return False


def get_benchmarks(category, include_opensource=False):
    """Get benchmarks for specified category"""
    benchmarks = []

    if HAS_ARCPY_BENCHMARKS:
        if category in ['vector', 'all']:
            benchmarks.extend(VectorBenchmarks.get_all_benchmarks())

        if category in ['raster', 'all']:
            benchmarks.extend(RasterBenchmarks.get_all_benchmarks())

        if category in ['mixed', 'all']:
            benchmarks.extend(MixedBenchmarks.get_all_benchmarks())
    else:
        print("\n[信息] 跳过 ArcGIS 基准测试 (arcpy 不可用)")

    # Open-source benchmarks (Python 3.x only)
    if include_opensource and HAS_OS_BENCHMARKS:
        if category in ['vector', 'all']:
            benchmarks.extend(VectorBenchmarksOS.get_all_benchmarks())

        if category in ['raster', 'all']:
            benchmarks.extend(RasterBenchmarksOS.get_all_benchmarks())

        if category in ['mixed', 'all']:
            benchmarks.extend(MixedBenchmarksOS.get_all_benchmarks())

    return benchmarks


def run_benchmarks(benchmarks, num_runs, warmup_runs):
    """Run all benchmarks"""
    results = []
    
    # 显示 Python 版本信息
    py_version = "Python {}.{}.{}".format(
        sys.version_info[0], sys.version_info[1], sys.version_info[2]
    )
    py_type = "ArcGIS Desktop (Python 2)" if sys.version_info[0] == 2 else "ArcGIS Pro (Python 3)"
    
    print("\n" + "=" * 70)
    print("开始执行基准测试 - {} ({})".format(py_version, py_type))
    print("=" * 70)
    print("测试项目总数: {}".format(len(benchmarks)))
    print("每项测试循环: {} 次正式 + {} 次预热".format(num_runs, warmup_runs))
    print("=" * 70)
    
    for i, benchmark in enumerate(benchmarks, 1):
        print("\n" + "-" * 70)
        print("[{}/{}] 正在执行: {} (类别: {})".format(
            i, len(benchmarks), benchmark.name, benchmark.category
        ))
        print("-" * 70)
        
        try:
            stats = benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs)
            results.append(stats)
            
            if stats.get('success'):
                print("\n  [OK] 测试完成: {}".format(benchmark.name))
                print("    平均耗时: {:.4f}秒".format(stats.get('mean_time', 0)))
                print("    标准差: ±{:.4f}秒".format(stats.get('std_time', 0)))
                print("    最快: {:.4f}秒 | 最慢: {:.4f}秒".format(
                    stats.get('min_time', 0),
                    stats.get('max_time', 0)
                ))
            else:
                print("\n  [FAILED] 测试失败: {}".format(benchmark.name))
                print("    错误: {}".format(stats.get('error', 'Unknown')))
        
        except Exception as e:
            print("\n  [ERROR] 执行异常: {}".format(benchmark.name))
            print("    异常信息: {}".format(str(e)))
            results.append({
                'test_name': benchmark.name,
                'success': False,
                'error': str(e)
            })
    
    return results


def save_results(results, output_dir, result_tag=None):
    """Save results to files"""
    exporter = ResultExporter(output_dir)
    
    # Determine file tag for the current result group
    if not result_tag:
        result_tag = "py{}".format(sys.version_info[0])
    result_tag = result_tag.lower()
    if result_tag == 'os':
        title = "Open-Source Benchmark Results"
    else:
        title = "Benchmark Results ({})".format(result_tag)
    
    # Export to JSON
    json_file = exporter.export_json(
        results,
        "benchmark_results_{}.json".format(result_tag)
    )
    print("\nJSON results saved to: {}".format(json_file))
    
    # Export to Markdown
    md_file = exporter.export_markdown(
        results,
        "benchmark_results_{}.md".format(result_tag),
        title=title
    )
    print("Markdown report saved to: {}".format(md_file))
    
    # Export to CSV
    csv_file = exporter.export_csv(
        results,
        "benchmark_results_{}.csv".format(result_tag)
    )
    print("CSV results saved to: {}".format(csv_file))
    
    return {
        'json': json_file,
        'markdown': md_file,
        'csv': csv_file
    }


def run_multiprocess_benchmarks(num_runs, warmup_runs, num_workers, include_opensource=False):
    """Run multiprocess comparison benchmarks"""
    print("\n" + "=" * 70)
    print("Running Multiprocess Comparison Benchmarks")
    print("Workers: {}".format(num_workers))
    if include_opensource:
        print("Include Open-Source: Yes")
    print("=" * 70)

    mp_results = []

    # Run arcpy multiprocess benchmarks if available
    if HAS_ARCPY_BENCHMARKS:
        from benchmarks.multiprocess_tests import get_multiprocess_benchmarks

        # Determine Python version prefix for naming
        py_version = "Py{}".format(sys.version_info[0])

        mp_benchmarks = get_multiprocess_benchmarks()

        for i, benchmark in enumerate(mp_benchmarks, 1):
            print("\n" + "-" * 70)
            print("[{}/{}] Running multiprocess comparison: {}".format(
                i, len(mp_benchmarks), benchmark.name
            ))
            print("-" * 70)

            # Run single process version
            print("\n  [1/2] Single process version...")
            stats_single = None
            try:
                # Create fresh instance for single process test
                fresh_benchmark = benchmark.__class__()
                stats_single = fresh_benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs,
                                             use_multiprocess=False)

                stats_single['test_name'] = "{}_{}_single".format(py_version, benchmark.name)

                if stats_single.get('success'):
                    print("    [OK] Single process: {:.4f}s".format(stats_single.get('mean_time', 0)))
                else:
                    print("    [FAILED] Single process: {}".format(stats_single.get('error', 'Unknown')))
            except Exception as e:
                print("    [ERROR] Single process: {}".format(str(e)))
                import traceback
                print(traceback.format_exc())
                stats_single = {
                    'test_name': "{}_{}_single".format(py_version, benchmark.name),
                    'success': False,
                    'error': str(e)
                }

            mp_results.append(stats_single)

            # Run multiprocess version
            print("\n  [2/2] Multiprocess version ({} workers)...".format(num_workers))
            try:
                # Create fresh instance for multiprocess test
                fresh_benchmark = benchmark.__class__()
                stats_mp = fresh_benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs,
                                         use_multiprocess=True)

                stats_mp['test_name'] = "{}_{}_multiprocess".format(py_version, benchmark.name)

                if stats_mp.get('success'):
                    print("    [OK] Multiprocess: {:.4f}s".format(stats_mp.get('mean_time', 0)))

                    # Calculate speedup
                    if stats_single.get('success'):
                        speedup = stats_single['mean_time'] / stats_mp['mean_time'] \
                                  if stats_mp['mean_time'] > 0 else 0
                        efficiency = speedup / num_workers * 100 if num_workers > 0 else 0
                        print("    Speedup: {:.2f}x (Efficiency: {:.1f}%)".format(speedup, efficiency))
                else:
                    print("    [FAILED] Multiprocess: {}".format(stats_mp.get('error', 'Unknown')))
            except Exception as e:
                print("    [ERROR] Multiprocess: {}".format(str(e)))
                import traceback
                print(traceback.format_exc())
                stats_mp = {
                    'test_name': "{}_{}_multiprocess".format(py_version, benchmark.name),
                    'success': False,
                    'error': str(e)
                }

            # Add multiprocess metadata
            stats_mp['execution_mode'] = 'multiprocess'
            stats_mp['num_workers'] = num_workers
            if stats_single.get('success') and stats_mp.get('success'):
                stats_mp['speedup_vs_single'] = stats_single['mean_time'] / stats_mp['mean_time'] \
                                                if stats_mp['mean_time'] > 0 else 0
                stats_mp['parallel_efficiency'] = stats_mp['speedup_vs_single'] / num_workers * 100

            mp_results.append(stats_mp)
    else:
        print("\n[信息] 跳过 ArcGIS 多进程基准测试 (arcpy 不可用)")

    # Import open-source multiprocess tests if available
    has_os_mp = False
    if include_opensource and sys.version_info[0] >= 3:
        try:
            from benchmarks.multiprocess_tests_os import MultiprocessTestsOS
            has_os_mp = True
        except ImportError:
            print("[Warning] Open-source multiprocess tests not available")

    # Run open-source multiprocess benchmarks if available
    if has_os_mp:
        print("\n" + "=" * 70)
        print("Running Open-Source Multiprocess Benchmarks")
        print("=" * 70)
        
        os_mp_benchmarks = MultiprocessTestsOS.get_all_benchmarks()
        for i, benchmark in enumerate(os_mp_benchmarks, 1):
            print("\n" + "-" * 70)
            print("[OS {}/{}] Running multiprocess comparison: {}".format(
                i, len(os_mp_benchmarks), benchmark.name
            ))
            print("-" * 70)
            
            # Run single process version
            print("\n  [1/2] Single process version...")
            stats_single = None
            try:
                fresh_benchmark = benchmark.__class__()
                stats_single = fresh_benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs, 
                                             use_multiprocess=False)

                os_name = benchmark.name.replace('_OS', '')
                stats_single['test_name'] = "OS_{}_single".format(os_name)

                if stats_single.get('success'):
                    print("    [OK] Single process: {:.4f}s".format(stats_single.get('mean_time', 0)))
                else:
                    print("    [FAILED] Single process: {}".format(stats_single.get('error', 'Unknown')))
            except Exception as e:
                print("    [ERROR] Single process: {}".format(str(e)))
                os_name = benchmark.name.replace('_OS', '')
                stats_single = {
                    'test_name': "OS_{}_single".format(os_name),
                    'success': False,
                    'error': str(e)
                }
            
            mp_results.append(stats_single)
            
            # Run multiprocess version
            print("\n  [2/2] Multiprocess version ({} workers)...".format(num_workers))
            try:
                fresh_benchmark = benchmark.__class__()
                stats_mp = fresh_benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs,
                                         use_multiprocess=True)

                os_name = benchmark.name.replace('_OS', '')
                stats_mp['test_name'] = "OS_{}_multiprocess".format(os_name)

                if stats_mp.get('success'):
                    print("    [OK] Multiprocess: {:.4f}s".format(stats_mp.get('mean_time', 0)))
                    
                    if stats_single.get('success'):
                        speedup = stats_single['mean_time'] / stats_mp['mean_time'] \
                                  if stats_mp['mean_time'] > 0 else 0
                        efficiency = speedup / num_workers * 100 if num_workers > 0 else 0
                        print("    Speedup: {:.2f}x (Efficiency: {:.1f}%)".format(speedup, efficiency))
                else:
                    print("    [FAILED] Multiprocess: {}".format(stats_mp.get('error', 'Unknown')))
            except Exception as e:
                print("    [ERROR] Multiprocess: {}".format(str(e)))
                os_name = benchmark.name.replace('_OS', '')
                stats_mp = {
                    'test_name': "OS_{}_multiprocess".format(os_name),
                    'success': False,
                    'error': str(e)
                }
            
            # Add multiprocess metadata
            stats_mp['execution_mode'] = 'multiprocess'
            stats_mp['num_workers'] = num_workers
            if stats_single.get('success') and stats_mp.get('success'):
                stats_mp['speedup_vs_single'] = stats_single['mean_time'] / stats_mp['mean_time'] \
                                                if stats_mp['mean_time'] > 0 else 0
                stats_mp['parallel_efficiency'] = stats_mp['speedup_vs_single'] / num_workers * 100
            
            mp_results.append(stats_mp)
    
    return mp_results


def run_multiprocess_benchmarks_group(num_runs, warmup_runs, num_workers, group_mode='arcpy'):
    """Run multiprocess benchmarks for a single result group."""
    mp_results = []

    if group_mode not in ['arcpy', 'opensource']:
        return mp_results

    print("\n" + "=" * 70)
    if group_mode == 'arcpy':
        print("Running ArcPy Multiprocess Benchmarks")
    else:
        print("Running Open-Source Multiprocess Benchmarks")
    print("Workers: {}".format(num_workers))
    print("=" * 70)

    if group_mode == 'arcpy':
        if not HAS_ARCPY_BENCHMARKS:
            print("\n[信息] 跳过 ArcGIS 多进程基准测试(arcpy 不可用)")
            return mp_results

        from benchmarks.multiprocess_tests import get_multiprocess_benchmarks
        py_version = "Py{}".format(sys.version_info[0])
        mp_benchmarks = get_multiprocess_benchmarks()

        for i, benchmark in enumerate(mp_benchmarks, 1):
            print("\n" + "-" * 70)
            print("[{}/{}] Running multiprocess comparison: {}".format(
                i, len(mp_benchmarks), benchmark.name
            ))
            print("-" * 70)

            print("\n  [1/2] Single process version...")
            stats_single = None
            try:
                fresh_benchmark = benchmark.__class__()
                stats_single = fresh_benchmark.run(
                    num_runs=num_runs,
                    warmup_runs=warmup_runs,
                    use_multiprocess=False
                )
                stats_single['test_name'] = "{}_{}_single".format(py_version, benchmark.name)
                if stats_single.get('success'):
                    print("    [OK] Single process: {:.4f}s".format(stats_single.get('mean_time', 0)))
                else:
                    print("    [FAILED] Single process: {}".format(stats_single.get('error', 'Unknown')))
            except Exception as e:
                print("    [ERROR] Single process: {}".format(str(e)))
                import traceback
                print(traceback.format_exc())
                stats_single = {
                    'test_name': "{}_{}_single".format(py_version, benchmark.name),
                    'success': False,
                    'error': str(e)
                }

            mp_results.append(stats_single)

            print("\n  [2/2] Multiprocess version ({} workers)...".format(num_workers))
            try:
                fresh_benchmark = benchmark.__class__()
                stats_mp = fresh_benchmark.run(
                    num_runs=num_runs,
                    warmup_runs=warmup_runs,
                    use_multiprocess=True
                )
                stats_mp['test_name'] = "{}_{}_multiprocess".format(py_version, benchmark.name)

                if stats_mp.get('success'):
                    print("    [OK] Multiprocess: {:.4f}s".format(stats_mp.get('mean_time', 0)))
                    if stats_single.get('success'):
                        speedup = stats_single['mean_time'] / stats_mp['mean_time'] if stats_mp['mean_time'] > 0 else 0
                        efficiency = speedup / num_workers * 100 if num_workers > 0 else 0
                        print("    Speedup: {:.2f}x (Efficiency: {:.1f}%)".format(speedup, efficiency))
                else:
                    print("    [FAILED] Multiprocess: {}".format(stats_mp.get('error', 'Unknown')))
            except Exception as e:
                print("    [ERROR] Multiprocess: {}".format(str(e)))
                import traceback
                print(traceback.format_exc())
                stats_mp = {
                    'test_name': "{}_{}_multiprocess".format(py_version, benchmark.name),
                    'success': False,
                    'error': str(e)
                }

            stats_mp['execution_mode'] = 'multiprocess'
            stats_mp['num_workers'] = num_workers
            if stats_single.get('success') and stats_mp.get('success'):
                stats_mp['speedup_vs_single'] = stats_single['mean_time'] / stats_mp['mean_time'] if stats_mp['mean_time'] > 0 else 0
                stats_mp['parallel_efficiency'] = stats_mp['speedup_vs_single'] / num_workers * 100

            mp_results.append(stats_mp)

        return mp_results

    if sys.version_info[0] < 3:
        print("\n[信息] 跳过开源库多进程测试，Python 3.x 环境不可用")
        return mp_results

    try:
        from benchmarks.multiprocess_tests_os import MultiprocessTestsOS
    except ImportError:
        print("[Warning] Open-source multiprocess tests not available")
        return mp_results

    os_mp_benchmarks = MultiprocessTestsOS.get_all_benchmarks()
    for i, benchmark in enumerate(os_mp_benchmarks, 1):
        print("\n" + "-" * 70)
        print("[OS {}/{}] Running multiprocess comparison: {}".format(
            i, len(os_mp_benchmarks), benchmark.name
        ))
        print("-" * 70)

        print("\n  [1/2] Single process version...")
        stats_single = None
        try:
            fresh_benchmark = benchmark.__class__()
            stats_single = fresh_benchmark.run(
                num_runs=num_runs,
                warmup_runs=warmup_runs,
                use_multiprocess=False
            )
            os_name = benchmark.name.replace('_OS', '')
            stats_single['test_name'] = "OS_{}_single".format(os_name)
            if stats_single.get('success'):
                print("    [OK] Single process: {:.4f}s".format(stats_single.get('mean_time', 0)))
            else:
                print("    [FAILED] Single process: {}".format(stats_single.get('error', 'Unknown')))
        except Exception as e:
            print("    [ERROR] Single process: {}".format(str(e)))
            os_name = benchmark.name.replace('_OS', '')
            stats_single = {
                'test_name': "OS_{}_single".format(os_name),
                'success': False,
                'error': str(e)
            }

        mp_results.append(stats_single)

        print("\n  [2/2] Multiprocess version ({} workers)...".format(num_workers))
        try:
            fresh_benchmark = benchmark.__class__()
            stats_mp = fresh_benchmark.run(
                num_runs=num_runs,
                warmup_runs=warmup_runs,
                use_multiprocess=True
            )

            os_name = benchmark.name.replace('_OS', '')
            stats_mp['test_name'] = "OS_{}_multiprocess".format(os_name)

            if stats_mp.get('success'):
                print("    [OK] Multiprocess: {:.4f}s".format(stats_mp.get('mean_time', 0)))
                if stats_single.get('success'):
                    speedup = stats_single['mean_time'] / stats_mp['mean_time'] if stats_mp['mean_time'] > 0 else 0
                    efficiency = speedup / num_workers * 100 if num_workers > 0 else 0
                    print("    Speedup: {:.2f}x (Efficiency: {:.1f}%)".format(speedup, efficiency))
            else:
                print("    [FAILED] Multiprocess: {}".format(stats_mp.get('error', 'Unknown')))
        except Exception as e:
            print("    [ERROR] Multiprocess: {}".format(str(e)))
            os_name = benchmark.name.replace('_OS', '')
            stats_mp = {
                'test_name': "OS_{}_multiprocess".format(os_name),
                'success': False,
                'error': str(e)
            }

        stats_mp['execution_mode'] = 'multiprocess'
        stats_mp['num_workers'] = num_workers
        if stats_single.get('success') and stats_mp.get('success'):
            stats_mp['speedup_vs_single'] = stats_single['mean_time'] / stats_mp['mean_time'] if stats_mp['mean_time'] > 0 else 0
            stats_mp['parallel_efficiency'] = stats_mp['speedup_vs_single'] / num_workers * 100

        mp_results.append(stats_mp)

    return mp_results


def print_summary(results):
    """Print summary of results"""
    print("\n" + "=" * 70)
    print("Benchmark Summary")
    print("=" * 70)
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print("Total: {} | Success: {} | Failed: {}".format(
        len(results),
        len(successful),
        len(failed)
    ))
    
    if successful:
        print("\nSuccessful Benchmarks:")
        for r in successful:
            print("  {:30s} {:.4f}s (±{:.4f}s)".format(
                r['test_name'] + ':',
                r.get('mean_time', 0),
                r.get('std_time', 0)
            ))
    
    if failed:
        print("\nFailed Benchmarks:")
        for r in failed:
            print("  {}: {}".format(r['test_name'], r.get('error', 'Unknown')))
    
    print("=" * 70)


def main():
    """Main function"""
    # Parse arguments
    args = parse_args()

    # Print banner
    print("=" * 70)
    print("ArcGIS Python Performance Benchmark")
    print("=" * 70)

    # Check arcpy
    has_arcpy = check_arcpy()
    if not has_arcpy:
        print("\n[警告] arcpy 不可用！")
        print("只有开源测试将被运行（如果可用）")
        print("要使用 ArcGIS 测试，请使用 ArcGIS Python 解释器运行：")
        print("  - ArcGIS Desktop: C:\\Python27\\ArcGIS10.8\\python.exe")
        print("  - ArcGIS Pro: \"C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe\"")

        # If only opensource tests requested, we can continue
        if not args.opensource:
            print("\n错误: 未指定 --opensource 标志，且 arcpy 不可用")
            print("请添加 --opensource 以仅运行开源测试")
            return 1
    
    # Print environment info
    if has_arcpy:
        env = ArcGISEnvironment()
        env.print_info()
    else:
        print("\n[环境] 跳过 ArcGIS 环境信息 (arcpy 不可用)")
    
    # Print configuration
    settings.print_config()

    # Apply scale setting if specified
    if args.scale:
        settings.set_scale(args.scale)
        print("\n[信息] 数据规模已设置为: {}".format(args.scale.upper()))

    # Propagate multiprocess worker count to benchmark classes.
    # The benchmark constructors read from settings at instantiation time.
    if args.mp_workers < 1:
        print("\nERROR: --mp-workers must be at least 1")
        return 1
    settings.MULTIPROCESS_CONFIG['num_workers'] = args.mp_workers
    settings.MULTIPROCESS_WORKERS = args.mp_workers

    # ===== 关键修复: 先设置时间戳目录，再生成数据 =====
    # Set output directory - keep runtime outputs in a flat timestamp root
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
        # Accept either <base>/<timestamp> or legacy nested result folders.
        try:
            timestamp_dir, base_data_dir = _extract_timestamp_root(output_dir)
            if timestamp_dir:
                timestamp = os.path.basename(timestamp_dir)
                settings.set_timestamped_dirs(timestamp, base_data_dir=base_data_dir)
                output_dir = settings.DATA_DIR
                print("\n[Info] Using timestamped root directory: {}".format(settings.DATA_DIR))
        except Exception:
            pass  # If extraction fails, just use the provided output_dir
    else:
        # Use timestamped directory in temp folder
        settings.set_timestamped_dirs()
        output_dir = settings.DATA_DIR
        print("\n[Info] Results will be saved to: {}".format(settings.DATA_DIR))

    # Determine whether open-source benchmarks should be included.
    include_opensource = False
    if args.opensource:
        if sys.version_info[0] < 3:
            print("\n[注意] 开源库基准测试需要 Python 3.x，当前为 Python 2.x，已跳过")
        elif not HAS_OS_BENCHMARKS:
            print("\n[注意] 未找到开源库模块 (geopandas, rasterio 等)，已跳过")
        else:
            include_opensource = True
            print("\n[信息] 将包含开源库 (GeoPandas/Rasterio) 基准测试")

    # Group benchmarks so each version gets its own folder.
    benchmarks = get_benchmarks(args.category, include_opensource)
    arcpy_benchmarks, opensource_benchmarks = _split_benchmark_groups(benchmarks)

    if not arcpy_benchmarks and not opensource_benchmarks:
        print("\nNo benchmarks to run for category: {}".format(args.category))
        return 1

    # Get run parameters
    num_runs = args.runs if args.runs is not None else settings.TEST_RUNS
    warmup_runs = args.warmup if args.warmup is not None else settings.WARMUP_RUNS

    def run_group(group_name, group_benchmarks, mp_mode=None):
        """Run one benchmark family in its own folder."""
        if not group_benchmarks:
            return []

        group_output_dir = _activate_group_output_dir(output_dir, group_name)
        print("\n[Info] Group output directory: {}".format(group_output_dir))

        if args.generate_data:
            if not generate_test_data():
                raise RuntimeError("Failed to generate test data for group: {}".format(group_name))

        group_results = run_benchmarks(group_benchmarks, num_runs, warmup_runs)

        if args.multiprocess and mp_mode:
            group_results.extend(run_multiprocess_benchmarks_group(
                num_runs,
                warmup_runs,
                args.mp_workers,
                group_mode=mp_mode
            ))

        print("\nSaving results for group: {}".format(group_name))
        save_results(group_results, group_output_dir, result_tag=group_name)
        return group_results

    all_results = []
    try:
        if arcpy_benchmarks:
            arcpy_group_name = "py{}".format(sys.version_info[0])
            all_results.extend(run_group(arcpy_group_name, arcpy_benchmarks, mp_mode='arcpy'))

        if opensource_benchmarks:
            all_results.extend(run_group('os', opensource_benchmarks, mp_mode='opensource'))
    except RuntimeError as e:
        print("\nERROR: {}".format(str(e)))
        return 1

    print_summary(all_results)

    print("\n" + "=" * 70)
    print("Benchmark Complete")
    print("=" * 70)

    if args.multiprocess:
        print("\nMultiprocess comparison completed!")
        print("Check the results for single vs multiprocess speedup data.")
    else:
        print("\nNext steps:")
        print("1. Run this script with the other Python version")
        print("2. Run analyze_results.py to generate comparison tables")

    return 0

    # Generate test data if requested (现在会使用正确的时间戳目录)
    if args.generate_data:
        if not generate_test_data():
            print("\nERROR: Failed to generate test data. Aborting benchmark run to avoid partial results.")
            return 1

    # Get benchmarks
    # Check if opensource flag is valid (Python 3.x only)
    include_opensource = False
    if args.opensource:
        if sys.version_info[0] < 3:
            print("\n[注意] 开源库基准测试需要 Python 3.x，在 Python 2.x 环境下跳过")
        elif not HAS_OS_BENCHMARKS:
            print("\n[注意] 未找到开源库模块 (geopandas, rasterio等)，跳过")
        else:
            include_opensource = True
            print("\n[信息] 将包含开源库 (GeoPandas/Rasterio) 基准测试")

    benchmarks = get_benchmarks(args.category, include_opensource)

    if not benchmarks:
        print("\nNo benchmarks to run for category: {}".format(args.category))
        return 1

    # Get run parameters
    num_runs = args.runs if args.runs is not None else settings.TEST_RUNS
    warmup_runs = args.warmup if args.warmup is not None else settings.WARMUP_RUNS
    
    # Run benchmarks
    results = run_benchmarks(benchmarks, num_runs, warmup_runs)
    
    # Run multiprocess benchmarks if requested
    mp_results = []
    if args.multiprocess:
        mp_results = run_multiprocess_benchmarks(num_runs, warmup_runs, args.mp_workers, include_opensource)
        results.extend(mp_results)
    
    # Print summary
    print_summary(results)
    
    # Save results
    print("\nSaving results...")
    output_files = save_results(results, output_dir)
    
    print("\n" + "=" * 70)
    print("Benchmark Complete")
    print("=" * 70)
    
    if args.multiprocess:
        print("\nMultiprocess comparison completed!")
        print("Check the results for single vs multiprocess speedup data.")
    else:
        print("\nNext steps:")
        print("1. Run this script with the other Python version")
        print("2. Run analyze_results.py to generate comparison tables")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
