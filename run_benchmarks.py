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
from benchmarks.vector_benchmarks import VectorBenchmarks
from benchmarks.raster_benchmarks import RasterBenchmarks
from benchmarks.mixed_benchmarks import MixedBenchmarks
from benchmarks.multiprocess_tests import get_multiprocess_benchmarks


def check_arcpy():
    """Check if arcpy is available"""
    try:
        import arcpy
        return True
    except ImportError:
        return False


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
        from data.generate_test_data import TestDataGenerator
        generator = TestDataGenerator()
        datasets = generator.generate_all()
        print("\nTest data generated successfully")
        return True
    except Exception as e:
        print("\nError generating test data: {}".format(str(e)))
        return False


def get_benchmarks(category):
    """Get benchmarks for specified category"""
    benchmarks = []
    
    if category in ['vector', 'all']:
        benchmarks.extend(VectorBenchmarks.get_all_benchmarks())
    
    if category in ['raster', 'all']:
        benchmarks.extend(RasterBenchmarks.get_all_benchmarks())
    
    if category in ['mixed', 'all']:
        benchmarks.extend(MixedBenchmarks.get_all_benchmarks())
    
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


def save_results(results, output_dir):
    """Save results to files"""
    exporter = ResultExporter(output_dir)
    
    # Determine Python version for filename
    py_version = "py{}".format(sys.version_info[0])
    
    # Export to JSON
    json_file = exporter.export_json(
        results,
        "benchmark_results_{}.json".format(py_version)
    )
    print("\nJSON results saved to: {}".format(json_file))
    
    # Export to Markdown
    md_file = exporter.export_markdown(
        results,
        "benchmark_results_{}.md".format(py_version),
        title="Benchmark Results ({})".format(py_version)
    )
    print("Markdown report saved to: {}".format(md_file))
    
    # Export to CSV
    csv_file = exporter.export_csv(
        results,
        "benchmark_results_{}.csv".format(py_version)
    )
    print("CSV results saved to: {}".format(csv_file))
    
    return {
        'json': json_file,
        'markdown': md_file,
        'csv': csv_file
    }


def run_multiprocess_benchmarks(num_runs, warmup_runs, num_workers):
    """Run multiprocess comparison benchmarks"""
    print("\n" + "=" * 70)
    print("Running Multiprocess Comparison Benchmarks")
    print("Workers: {}".format(num_workers))
    print("=" * 70)
    
    from benchmarks.multiprocess_tests import get_multiprocess_benchmarks
    
    # Determine Python version prefix for naming
    py_version = "Py{}".format(sys.version_info[0])
    
    mp_benchmarks = get_multiprocess_benchmarks()
    mp_results = []
    
    for i, benchmark in enumerate(mp_benchmarks, 1):
        print("\n" + "-" * 70)
        print("[{}/{}] Running multiprocess comparison: {}".format(
            i, len(mp_benchmarks), benchmark.name
        ))
        print("-" * 70)
        
        # Run single process version
        print("\n  [1/2] Single process version...")
        try:
            benchmark.setup()
            stats_single = benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs, 
                                         use_multiprocess=False)
            benchmark.teardown()
            
            # Add Python version prefix to test name
            stats_single['test_name'] = "{}_{}_single".format(py_version, benchmark.name)
            
            if stats_single.get('success'):
                print("    [OK] Single process: {:.4f}s".format(stats_single.get('mean_time', 0)))
            else:
                print("    [FAILED] Single process: {}".format(stats_single.get('error', 'Unknown')))
        except Exception as e:
            print("    [ERROR] Single process: {}".format(str(e)))
            stats_single = {
                'test_name': "{}_{}_single".format(py_version, benchmark.name),
                'success': False,
                'error': str(e)
            }
        
        mp_results.append(stats_single)
        
        # Run multiprocess version
        print("\n  [2/2] Multiprocess version ({} workers)...".format(num_workers))
        try:
            benchmark.setup()
            stats_mp = benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs,
                                     use_multiprocess=True)
            benchmark.teardown()
            
            # Add Python version prefix to test name
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
    if not check_arcpy():
        print("\nERROR: arcpy is not available!")
        print("Please run this script with an ArcGIS Python interpreter:")
        print("  - ArcGIS Desktop: C:\\Python27\\ArcGIS10.8\\python.exe")
        print("  - ArcGIS Pro: \"C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe\"")
        return 1
    
    # Print environment info
    env = ArcGISEnvironment()
    env.print_info()
    
    # Print configuration
    settings.print_config()
    
    # Generate test data if requested
    if args.generate_data:
        if not generate_test_data():
            print("\nWarning: Failed to generate test data. Continuing anyway...")
    
    # Get benchmarks
    benchmarks = get_benchmarks(args.category)
    
    if not benchmarks:
        print("\nNo benchmarks to run for category: {}".format(args.category))
        return 1
    
    # Get run parameters
    num_runs = args.runs if args.runs is not None else settings.TEST_RUNS
    warmup_runs = args.warmup if args.warmup is not None else settings.WARMUP_RUNS
    output_dir = args.output_dir if args.output_dir else settings.RAW_RESULTS_DIR
    
    # Run benchmarks
    results = run_benchmarks(benchmarks, num_runs, warmup_runs)
    
    # Run multiprocess benchmarks if requested
    mp_results = []
    if args.multiprocess:
        mp_results = run_multiprocess_benchmarks(num_runs, warmup_runs, args.mp_workers)
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
