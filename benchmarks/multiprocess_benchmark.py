# -*- coding: utf-8 -*-
"""
Multiprocess benchmark base class and utilities
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import multiprocessing
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.base_benchmark import BaseBenchmark
from config import settings
from utils.timer import ProgressHeartbeat
from utils.raster_utils import create_constant_raster


def worker_create_fishnet(args):
    """Worker function for creating fishnet in parallel"""
    import arcpy
    worker_id, rows, cols, row_start, row_end, output_path = args
    
    try:
        arcpy.env.overwriteOutput = True
        
        # Calculate geometry for this partition
        total_width = 360.0  # -180 to 180
        total_height = 180.0  # -90 to 90
        
        cell_width = total_width / cols
        cell_height = total_height / rows
        
        # Calculate origin for this partition
        origin_y = 90 - (row_start * cell_height)
        corner_y = 90 - (row_end * cell_height)
        
        # Create fishnet for this partition
        arcpy.CreateFishnet_management(
            out_feature_class=output_path,
            origin_coord="-180 {}".format(origin_y),
            y_axis_coord="-180 {}".format(origin_y + 10),
            cell_width=cell_width,
            cell_height=cell_height,
            number_rows=(row_end - row_start),
            number_columns=cols,
            corner_coord="180 {}".format(corner_y),
            labels="NO_LABELS",
            template="",
            geometry_type="POLYGON"
        )
        
        # Add spatial reference
        sr = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
        arcpy.DefineProjection_management(output_path, sr)
        
        return {'success': True, 'worker_id': worker_id, 'output': output_path}
    except Exception as e:
        return {'success': False, 'worker_id': worker_id, 'error': str(e)}


def worker_create_random_points(args):
    """Worker function for creating random points in parallel"""
    import arcpy
    worker_id, num_points, extent, output_path = args
    
    try:
        arcpy.env.overwriteOutput = True
        
        # Create random points for this partition
        arcpy.CreateRandomPoints_management(
            out_path=os.path.dirname(output_path),
            out_name=os.path.basename(output_path).replace('.shp', ''),
            constraining_extent=extent,
            number_of_points_or_field=num_points,
            minimum_allowed_distance="0 DecimalDegrees"
        )
        
        return {'success': True, 'worker_id': worker_id, 'output': output_path}
    except Exception as e:
        return {'success': False, 'worker_id': worker_id, 'error': str(e)}


def worker_buffer(args):
    """Worker function for buffer analysis in parallel"""
    import arcpy
    worker_id, input_fc, output_fc, buffer_distance = args
    
    try:
        arcpy.env.overwriteOutput = True
        
        arcpy.Buffer_analysis(
            in_features=input_fc,
            out_feature_class=output_fc,
            buffer_distance_or_field=buffer_distance,
            line_side="FULL",
            line_end_type="ROUND",
            dissolve_option="NONE"
        )
        
        return {'success': True, 'worker_id': worker_id, 'output': output_fc}
    except Exception as e:
        return {'success': False, 'worker_id': worker_id, 'error': str(e)}


def worker_intersect(args):
    """Worker function for intersect analysis in parallel"""
    import arcpy
    worker_id, input_a, input_b, output_fc = args
    
    try:
        arcpy.env.overwriteOutput = True
        
        arcpy.Intersect_analysis(
            in_features=[input_a, input_b],
            out_feature_class=output_fc,
            join_attributes="ALL",
            output_type="INPUT"
        )
        
        return {'success': True, 'worker_id': worker_id, 'output': output_fc}
    except Exception as e:
        return {'success': False, 'worker_id': worker_id, 'error': str(e)}


def worker_create_raster(args):
    """Worker function for creating constant raster in parallel"""
    import arcpy
    worker_id, cell_size, extent, output_raster = args
    
    try:
        arcpy.env.overwriteOutput = True
        create_constant_raster(output_raster, cell_size, extent, value=1, use_spatial_analyst=False)
        
        return {'success': True, 'worker_id': worker_id, 'output': output_raster}
    except Exception as e:
        return {'success': False, 'worker_id': worker_id, 'error': str(e)}


class MultiprocessBenchmark(BaseBenchmark):
    """
    Base class for benchmarks that support both single and multiprocess execution
    """
    
    def __init__(self, name, category="general"):
        super(MultiprocessBenchmark, self).__init__(name, category)
        self.num_workers = getattr(settings, 'MULTIPROCESS_WORKERS', 4)
        self.temp_outputs = []
        self._temp_dir = None
    
    def __del__(self):
        """Destructor to ensure cleanup of temporary files"""
        try:
            self.cleanup_temp_files()
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir, ignore_errors=True)
        except:
            pass
    
    def run_single(self):
        """Single process version - must be implemented by subclass"""
        raise NotImplementedError("Subclasses must implement run_single()")
    
    def run_multiprocess(self, num_workers=None):
        """Multiprocess version - must be implemented by subclass"""
        raise NotImplementedError("Subclasses must implement run_multiprocess()")
    
    def run(self, num_runs=None, warmup_runs=None, use_multiprocess=False):
        """
        Run benchmark with optional multiprocessing
        
        Args:
            num_runs: Number of iterations
            warmup_runs: Number of warmup iterations
            use_multiprocess: If True, use multiprocess version
        """
        if use_multiprocess:
            return self._run_multiprocess_benchmark(num_runs, warmup_runs)
        else:
            return super(MultiprocessBenchmark, self).run(num_runs, warmup_runs)
    
    def _run_multiprocess_benchmark(self, num_runs=None, warmup_runs=None):
        """Run benchmark using multiprocessing"""
        if num_runs is None:
            num_runs = settings.TEST_RUNS
        if warmup_runs is None:
            warmup_runs = settings.WARMUP_RUNS
        
        py_version = "Py{}.{}".format(sys.version_info[0], sys.version_info[1])
        mp_label = "[多进程 {}进程]".format(self.num_workers)
        
        print("\n  [{}] {} 初始化测试: {}".format(py_version, mp_label, self.name))
        print("  类别: {}".format(self.category))
        
        # Setup
        print("  执行 setup()...")
        with ProgressHeartbeat("{} setup()".format(self.name)):
            self.setup()
        print("  [OK] setup() 完成")
        
        try:
            # Warmup runs (single process for warmup)
            if warmup_runs > 0:
                print("  预热运行 ({} 次，单进程)...".format(warmup_runs))
                for i in range(warmup_runs):
                    print("    预热 {}/{}...".format(i + 1, warmup_runs))
                    result = self._run_single_iteration()
                    self.warmup_results.append(result)
            
            # Actual benchmark runs (multiprocess)
            print("  正式测试运行 ({} 次，多进程)...".format(num_runs))
            for i in range(num_runs):
                print("    运行 {}/{}...".format(i + 1, num_runs))
                
                # Time the multiprocess execution
                import time
                start_time = time.time()
                
                try:
                    heartbeat_label = "{} - 正式 {}/{} (多进程)".format(self.name, i + 1, num_runs)
                    with ProgressHeartbeat(heartbeat_label):
                        result = self.run_multiprocess(self.num_workers)
                    result['success'] = True
                except Exception as e:
                    import traceback
                    result = {
                        'success': False,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
                
                elapsed = time.time() - start_time
                result['elapsed_seconds'] = elapsed
                
                self.results.append(result)
                
                if result.get('success'):
                    print("      [OK] 耗时: {:.4f}秒".format(elapsed))
                else:
                    print("      [FAILED] {}".format(result.get('error', 'Unknown error')))
        
        finally:
            # Teardown
            print("  执行 teardown()...")
            with ProgressHeartbeat("{} teardown()".format(self.name)):
                self.teardown()
            print("  [OK] teardown() 完成")
        
        # Calculate statistics
        return self.get_statistics()
    
    def cleanup_temp_files(self):
        """Clean up temporary files created by workers"""
        for temp_file in self.temp_outputs:
            try:
                if os.path.exists(temp_file):
                    if os.path.isdir(temp_file):
                        shutil.rmtree(temp_file)
                    else:
                        os.remove(temp_file)
            except Exception:
                pass
        self.temp_outputs = []


class MultiprocessBenchmarkSuite(object):
    """
    Suite for running both single and multiprocess versions of benchmarks
    """
    
    def __init__(self, name="Multiprocess Benchmark Suite"):
        self.name = name
        self.benchmarks = []
        self.single_process_results = []
        self.multiprocess_results = []
    
    def add(self, benchmark_class, *args, **kwargs):
        """Add a benchmark class to the suite"""
        self.benchmarks.append({
            'class': benchmark_class,
            'args': args,
            'kwargs': kwargs
        })
    
    def run_comparison(self, num_runs=None, warmup_runs=None, num_workers=4):
        """
        Run both single and multiprocess versions and return comparison
        """
        print("\n" + "=" * 70)
        print("多进程性能对比测试")
        print("进程数: {}".format(num_workers))
        print("=" * 70)
        
        comparison_results = []
        
        for i, bench_info in enumerate(self.benchmarks, 1):
            print("\n[{}/{}] 测试: {}".format(i, len(self.benchmarks), 
                  bench_info['class'].__name__))
            
            # Run single process version
            print("\n  [1/2] 单进程版本...")
            single_bench = bench_info['class'](*bench_info['args'], **bench_info['kwargs'])
            single_stats = single_bench.run(num_runs=num_runs, warmup_runs=warmup_runs)
            single_stats['execution_mode'] = 'single'
            self.single_process_results.append(single_stats)
            
            # Run multiprocess version
            print("\n  [2/2] 多进程版本 ({}进程)...".format(num_workers))
            mp_bench = bench_info['class'](*bench_info['args'], **bench_info['kwargs'])
            mp_bench.num_workers = num_workers
            mp_stats = mp_bench.run(num_runs=num_runs, warmup_runs=warmup_runs, 
                                    use_multiprocess=True)
            mp_stats['execution_mode'] = 'multiprocess'
            mp_stats['num_workers'] = num_workers
            self.multiprocess_results.append(mp_stats)
            
            # Calculate speedup
            if single_stats.get('success') and mp_stats.get('success'):
                speedup = single_stats['mean_time'] / mp_stats['mean_time'] \
                          if mp_stats['mean_time'] > 0 else 0
                efficiency = speedup / num_workers * 100 if num_workers > 0 else 0
                
                comparison_results.append({
                    'test_name': single_stats['test_name'],
                    'single_time': single_stats['mean_time'],
                    'multiprocess_time': mp_stats['mean_time'],
                    'speedup': speedup,
                    'efficiency': efficiency,
                    'num_workers': num_workers
                })
                
                print("\n  结果对比:")
                print("    单进程:   {:.4f}秒".format(single_stats['mean_time']))
                print("    多进程:   {:.4f}秒".format(mp_stats['mean_time']))
                print("    加速比:   {:.2f}x".format(speedup))
                print("    并行效率: {:.1f}%".format(efficiency))
        
        print("\n" + "=" * 70)
        print("多进程对比测试完成")
        print("=" * 70)
        
        return comparison_results


if __name__ == '__main__':
    # Test multiprocess benchmark
    class TestMultiprocessBenchmark(MultiprocessBenchmark):
        def run_single(self):
            import time
            time.sleep(0.1)
            return {'operation': 'test_single'}
        
        def run_multiprocess(self, num_workers):
            import time
            time.sleep(0.05)  # Simulate faster execution
            return {'operation': 'test_multiprocess', 'workers': num_workers}
    
    test = TestMultiprocessBenchmark("TestMPBenchmark", "test")
    
    print("Testing single process...")
    stats_single = test.run(num_runs=2, use_multiprocess=False)
    print("\nTesting multiprocess...")
    stats_mp = test.run(num_runs=2, use_multiprocess=True)
    
    print("\nSingle process stats:", stats_single.get('mean_time'))
    print("Multiprocess stats:", stats_mp.get('mean_time'))
