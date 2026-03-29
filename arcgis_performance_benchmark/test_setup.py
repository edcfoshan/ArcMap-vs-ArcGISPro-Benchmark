#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify the benchmark framework setup
Run this before running full benchmarks to check everything is configured correctly
"""
from __future__ import print_function, division, absolute_import
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    errors = []
    
    try:
        from config import settings
        print("  ✓ config.settings")
    except Exception as e:
        errors.append(("config.settings", str(e)))
        print("  ✗ config.settings: {}".format(e))
    
    try:
        from utils.timer import Timer, MemoryMonitor, BenchmarkTimer
        print("  ✓ utils.timer")
    except Exception as e:
        errors.append(("utils.timer", str(e)))
        print("  ✗ utils.timer: {}".format(e))
    
    try:
        from utils.arcgis_env import ArcGISEnvironment
        print("  ✓ utils.arcgis_env")
    except Exception as e:
        errors.append(("utils.arcgis_env", str(e)))
        print("  ✗ utils.arcgis_env: {}".format(e))
    
    try:
        from utils.result_exporter import ResultExporter
        print("  ✓ utils.result_exporter")
    except Exception as e:
        errors.append(("utils.result_exporter", str(e)))
        print("  ✗ utils.result_exporter: {}".format(e))
    
    try:
        from benchmarks.base_benchmark import BaseBenchmark
        print("  ✓ benchmarks.base_benchmark")
    except Exception as e:
        errors.append(("benchmarks.base_benchmark", str(e)))
        print("  ✗ benchmarks.base_benchmark: {}".format(e))
    
    return len(errors) == 0, errors


def test_arcpy():
    """Test if arcpy is available"""
    print("\nTesting arcpy availability...")
    
    try:
        import arcpy
        print("  ✓ arcpy is available")
        print("  Product: {}".format(arcpy.GetInstallInfo()['ProductName']))
        print("  Version: {}".format(arcpy.GetInstallInfo()['Version']))
        return True
    except ImportError:
        print("  ✗ arcpy is NOT available")
        print("  Please run this script with an ArcGIS Python interpreter")
        return False


def test_directories():
    """Test if all required directories exist"""
    print("\nTesting directories...")
    
    from config import settings
    
    dirs_to_check = [
        ("DATA_DIR", settings.DATA_DIR),
        ("RAW_RESULTS_DIR", settings.RAW_RESULTS_DIR),
        ("TABLES_DIR", settings.TABLES_DIR),
        ("FIGURES_DIR", settings.FIGURES_DIR),
    ]
    
    all_exist = True
    for name, path in dirs_to_check:
        if os.path.exists(path):
            print("  ✓ {}: {}".format(name, path))
        else:
            print("  ✗ {}: {} (will be created)".format(name, path))
            all_exist = False
    
    return all_exist


def test_timer():
    """Test timer functionality"""
    print("\nTesting timer...")
    
    from utils.timer import Timer
    import time
    
    try:
        with Timer("Test") as t:
            time.sleep(0.1)
        
        if t.elapsed and t.elapsed > 0.05:
            print("  ✓ Timer working (elapsed: {:.4f}s)".format(t.elapsed))
            return True
        else:
            print("  ✗ Timer not working correctly")
            return False
    except Exception as e:
        print("  ✗ Timer error: {}".format(e))
        return False


def test_memory_monitor():
    """Test memory monitor"""
    print("\nTesting memory monitor...")
    
    from utils.timer import MemoryMonitor
    import time
    
    try:
        mm = MemoryMonitor(interval=0.1)
        mm.start()
        time.sleep(0.3)
        mm.stop()
        
        if mm.peak_memory_mb > 0:
            print("  ✓ Memory monitor working (peak: {:.2f} MB)".format(mm.peak_memory_mb))
            return True
        else:
            print("  ⚠ Memory monitor may not be working (no data collected)")
            return True  # Not a critical error
    except Exception as e:
        print("  ✗ Memory monitor error: {}".format(e))
        return False


def main():
    """Main test function"""
    print("=" * 70)
    print("ArcGIS Performance Benchmark - Setup Test")
    print("=" * 70)
    print("Python {}.{}.{}".format(
        sys.version_info[0],
        sys.version_info[1],
        sys.version_info[2]
    ))
    print("")
    
    results = {}
    
    # Run tests
    results['imports'], import_errors = test_imports()
    results['arcpy'] = test_arcpy()
    results['directories'] = test_directories()
    results['timer'] = test_timer()
    results['memory'] = test_memory_monitor()
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print("  {} {}: {}".format(symbol, test_name.upper(), status))
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("All tests passed! Framework is ready to use.")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Run: python run_benchmarks.py --generate-data")
        print("2. Run with both Python versions")
        print("3. Run: python analyze_results.py")
        return 0
    else:
        print("Some tests failed. Please fix the issues above.")
        print("=" * 70)
        
        if import_errors:
            print("\nImport errors:")
            for module, error in import_errors:
                print("  - {}: {}".format(module, error))
        
        if not results['arcpy']:
            print("\nNote: arcpy is only available in ArcGIS Python interpreters.")
            print("Please run this script with one of the following:")
            print("  C:\\Python27\\ArcGIS10.8\\python.exe test_setup.py")
            print("  \"C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3\\python.exe\" test_setup.py")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
