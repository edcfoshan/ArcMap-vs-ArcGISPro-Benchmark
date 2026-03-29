#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convenience script to run benchmarks on both Python versions
This script runs the benchmarks on both Python 2.7 and Python 3.x automatically
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import subprocess
import time

# Python interpreters
PYTHON27 = r"C:\Python27\ArcGIS10.8\python.exe"
PYTHON3 = r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def check_python_installations():
    """Check if both Python installations exist"""
    installations = []
    
    if os.path.exists(PYTHON27):
        installations.append(("Python 2.7", PYTHON27))
    else:
        print("WARNING: Python 2.7 not found at: {}".format(PYTHON27))
    
    if os.path.exists(PYTHON3):
        installations.append(("Python 3.x", PYTHON3))
    else:
        print("WARNING: Python 3.x not found at: {}".format(PYTHON3))
    
    return installations


def run_benchmark(python_exe, name, generate_data=False):
    """Run benchmarks with specified Python interpreter"""
    print("\n" + "=" * 70)
    print("Running benchmarks with {}".format(name))
    print("Interpreter: {}".format(python_exe))
    print("=" * 70)
    
    cmd = [
        python_exe,
        os.path.join(SCRIPT_DIR, "run_benchmarks.py")
    ]
    
    if generate_data:
        cmd.append("--generate-data")
    
    start_time = time.time()
    
    try:
        result = subprocess.call(cmd)
        elapsed = time.time() - start_time
        
        if result == 0:
            print("\n{} benchmarks completed in {:.1f} minutes".format(
                name, elapsed / 60
            ))
            return True
        else:
            print("\n{} benchmarks failed with code: {}".format(name, result))
            return False
    
    except Exception as e:
        print("\nError running {} benchmarks: {}".format(name, str(e)))
        return False


def run_analysis():
    """Run result analysis"""
    print("\n" + "=" * 70)
    print("Running result analysis")
    print("=" * 70)
    
    # Use current Python for analysis
    cmd = [
        sys.executable,
        os.path.join(SCRIPT_DIR, "analyze_results.py")
    ]
    
    try:
        result = subprocess.call(cmd)
        return result == 0
    except Exception as e:
        print("Error running analysis: {}".format(str(e)))
        return False


def main():
    """Main function"""
    print("=" * 70)
    print("ArcGIS Python Performance Benchmark - Dual Version Runner")
    print("=" * 70)
    
    # Check installations
    installations = check_python_installations()
    
    if len(installations) < 2:
        print("\nERROR: Both Python versions are required!")
        print("Please ensure both interpreters are installed:")
        print("  - Python 2.7: {}".format(PYTHON27))
        print("  - Python 3.x: {}".format(PYTHON3))
        return 1
    
    print("\nFound {} Python installation(s):".format(len(installations)))
    for name, path in installations:
        print("  - {}: {}".format(name, path))
    
    # Run benchmarks on both versions
    results = {}
    
    for name, python_exe in installations:
        # Generate data only on first run
        generate_data = (name == installations[0][0])
        
        success = run_benchmark(python_exe, name, generate_data=generate_data)
        results[name] = success
    
    # Print summary
    print("\n" + "=" * 70)
    print("Benchmark Run Summary")
    print("=" * 70)
    
    for name, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print("  {}: {}".format(name, status))
    
    # Run analysis if both succeeded
    if all(results.values()):
        print("\nRunning analysis...")
        if run_analysis():
            print("\n" + "=" * 70)
            print("All tasks completed successfully!")
            print("=" * 70)
            print("\nResults are available in: results/tables/")
            return 0
        else:
            print("\nAnalysis failed!")
            return 1
    else:
        print("\nSome benchmarks failed. Analysis skipped.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
