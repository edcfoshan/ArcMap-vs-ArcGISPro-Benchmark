#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main script to run ArcGIS Performance Benchmarks
Compatible with Python 2.7 and 3.x

Usage:
    Python 2.7: C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py [--category vector|raster|mixed|all]
    Python 3.x: "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py [--category vector|raster|mixed|all]
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
    
    print("\n" + "=" * 70)
    print("Starting Benchmark Suite")
    print("=" * 70)
    print("Total benchmarks: {}".format(len(benchmarks)))
    print("Runs per benchmark: {} (+ {} warmup)".format(num_runs, warmup_runs))
    print("=" * 70)
    
    for i, benchmark in enumerate(benchmarks, 1):
        print("\n[{}/{}] Running: {}".format(i, len(benchmarks), benchmark.name))
        
        try:
            stats = benchmark.run(num_runs=num_runs, warmup_runs=warmup_runs)
            results.append(stats)
            
            if stats.get('success'):
                print("  Status: SUCCESS")
                print("  Mean time: {:.4f}s (±{:.4f}s)".format(
                    stats.get('mean_time', 0),
                    stats.get('std_time', 0)
                ))
            else:
                print("  Status: FAILED")
                print("  Error: {}".format(stats.get('error', 'Unknown')))
        
        except Exception as e:
            print("  Status: ERROR")
            print("  Exception: {}".format(str(e)))
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
    
    # Print summary
    print_summary(results)
    
    # Save results
    print("\nSaving results...")
    output_files = save_results(results, output_dir)
    
    print("\n" + "=" * 70)
    print("Benchmark Complete")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Run this script with the other Python version")
    print("2. Run analyze_results.py to generate comparison tables")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
