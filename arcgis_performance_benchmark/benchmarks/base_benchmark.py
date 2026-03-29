# -*- coding: utf-8 -*-
"""
Base class for all benchmarks
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import json
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from utils.timer import BenchmarkTimer


class BaseBenchmark(object):
    """
    Abstract base class for all benchmarks
    """
    def __init__(self, name, category="general"):
        self.name = name
        self.category = category
        self.results = []
        self.warmup_results = []
        self.env_info = {}
        self.timer = None
        
        # Import arcpy if available
        self.arcpy = None
        try:
            import arcpy
            self.arcpy = arcpy
        except ImportError:
            raise RuntimeError("arcpy is required for benchmarks")
    
    def setup(self):
        """Setup before benchmark - override in subclass"""
        pass
    
    def teardown(self):
        """Cleanup after benchmark - override in subclass"""
        pass
    
    def run_single(self):
        """
        Run a single benchmark iteration - must be implemented by subclass
        Returns: dict with at least 'success' key
        """
        raise NotImplementedError("Subclasses must implement run_single()")
    
    def run(self, num_runs=None, warmup_runs=None):
        """
        Run benchmark with multiple iterations
        
        Args:
            num_runs: Number of iterations (default from settings)
            warmup_runs: Number of warmup iterations (default from settings)
        """
        if num_runs is None:
            num_runs = settings.TEST_RUNS
        if warmup_runs is None:
            warmup_runs = settings.WARMUP_RUNS
        
        print("\n" + "=" * 60)
        print("Running Benchmark: {}".format(self.name))
        print("Category: {}".format(self.category))
        print("=" * 60)
        
        # Setup
        self.setup()
        
        try:
            # Warmup runs
            if warmup_runs > 0:
                print("\nWarmup runs ({} iterations)...".format(warmup_runs))
                for i in range(warmup_runs):
                    print("  Warmup {}/{}...".format(i + 1, warmup_runs))
                    result = self._run_single_iteration()
                    self.warmup_results.append(result)
            
            # Actual benchmark runs
            print("\nBenchmark runs ({} iterations)...".format(num_runs))
            for i in range(num_runs):
                print("  Run {}/{}...".format(i + 1, num_runs))
                result = self._run_single_iteration()
                self.results.append(result)
                
                if result.get('success'):
                    print("    Time: {:.4f}s".format(result.get('elapsed_seconds', 0)))
                else:
                    print("    FAILED: {}".format(result.get('error', 'Unknown error')))
        
        finally:
            # Teardown
            self.teardown()
        
        # Calculate statistics
        return self.get_statistics()
    
    def _run_single_iteration(self):
        """Run a single iteration with timing"""
        with BenchmarkTimer(name=self.name, monitor_memory=settings.ENABLE_MEMORY_MONITORING) as bt:
            try:
                # Run the actual benchmark
                result = self.run_single()
                result['success'] = True
            except Exception as e:
                result = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        
        # Combine timing results with benchmark result
        timing_results = bt.get_results()
        result.update(timing_results)
        
        return result
    
    def get_statistics(self):
        """Calculate statistics from results"""
        successful = [r for r in self.results if r.get('success')]
        
        if not successful:
            return {
                'test_name': self.name,
                'category': self.category,
                'success': False,
                'error': 'All runs failed',
                'total_runs': len(self.results),
                'successful_runs': 0
            }
        
        # Extract timing values
        times = [r['elapsed_seconds'] for r in successful]
        
        # Calculate statistics
        mean_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        # Standard deviation
        if len(times) > 1:
            variance = sum((t - mean_time) ** 2 for t in times) / (len(times) - 1)
            std_time = variance ** 0.5
        else:
            std_time = 0
        
        # Memory statistics
        if settings.ENABLE_MEMORY_MONITORING:
            peak_memories = [r.get('memory_mb', {}).get('peak_mb', 0) for r in successful if 'memory_mb' in r]
            avg_memory = sum(peak_memories) / len(peak_memories) if peak_memories else 0
        else:
            avg_memory = 0
        
        stats = {
            'test_name': self.name,
            'category': self.category,
            'success': True,
            'total_runs': len(self.results),
            'successful_runs': len(successful),
            'failed_runs': len(self.results) - len(successful),
            'mean_time': mean_time,
            'std_time': std_time,
            'min_time': min_time,
            'max_time': max_time,
            'cv_percent': (std_time / mean_time * 100) if mean_time > 0 else 0,
            'avg_memory_mb': avg_memory,
            'all_times': times,
            'python_version': "{}.{}.{}".format(
                sys.version_info[0],
                sys.version_info[1],
                sys.version_info[2]
            )
        }
        
        return stats
    
    def get_raw_results(self):
        """Get all raw results"""
        return self.results
    
    def save_results(self, output_dir=None):
        """Save results to file"""
        if output_dir is None:
            output_dir = settings.RAW_RESULTS_DIR
        
        stats = self.get_statistics()
        
        filename = "{}_{}.json".format(
            self.name,
            "py{}".format(sys.version_info[0])
        )
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({
                'statistics': stats,
                'raw_results': self.results,
                'warmup_results': self.warmup_results
            }, f, indent=2)
        
        print("\nResults saved to: {}".format(filepath))
        return filepath


class BenchmarkSuite(object):
    """
    Suite of multiple benchmarks
    """
    def __init__(self, name="Benchmark Suite"):
        self.name = name
        self.benchmarks = []
        self.results = []
    
    def add(self, benchmark):
        """Add a benchmark to the suite"""
        self.benchmarks.append(benchmark)
    
    def run_all(self, num_runs=None, warmup_runs=None):
        """Run all benchmarks in the suite"""
        print("\n" + "=" * 70)
        print("Running Benchmark Suite: {}".format(self.name))
        print("Total benchmarks: {}".format(len(self.benchmarks)))
        print("=" * 70)
        
        self.results = []
        for i, benchmark in enumerate(self.benchmarks, 1):
            print("\n[{}/{}]".format(i, len(self.benchmarks)))
            stats = benchmark.run(num_runs, warmup_runs)
            self.results.append(stats)
            benchmark.save_results()
        
        print("\n" + "=" * 70)
        print("Benchmark Suite Complete")
        print("=" * 70)
        
        return self.results
    
    def get_summary(self):
        """Get summary of all results"""
        return {
            'suite_name': self.name,
            'total_benchmarks': len(self.benchmarks),
            'successful': len([r for r in self.results if r.get('success')]),
            'failed': len([r for r in self.results if not r.get('success')]),
            'results': self.results
        }


if __name__ == '__main__':
    # Test base benchmark
    class TestBenchmark(BaseBenchmark):
        def run_single(self):
            time.sleep(0.1)
            return {'operation': 'test'}
    
    test = TestBenchmark("TestBenchmark", "test")
    stats = test.run(num_runs=3, warmup_runs=1)
    print("\nStatistics:")
    for key, value in stats.items():
        print("  {}: {}".format(key, value))
