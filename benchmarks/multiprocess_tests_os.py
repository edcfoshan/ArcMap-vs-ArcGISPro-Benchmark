# -*- coding: utf-8 -*-
"""
Multiprocess benchmark tests for Open-Source libraries
Compatible with Python 3.x only
Uses multiprocessing with GeoPandas and Rasterio
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import tempfile
import shutil
import multiprocessing as mp
from functools import partial

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import open-source libraries
try:
    import geopandas as gpd
    from shapely.geometry import box
    import numpy as np
    HAS_OS_LIBS = True
except ImportError:
    HAS_OS_LIBS = False

from config import settings
from benchmarks.base_benchmark import BaseBenchmark
from utils.timer import ProgressHeartbeat


def create_fishnet_chunk(args):
    """Worker function for creating fishnet chunk"""
    start_row, end_row, cols, cell_width, cell_height = args
    polygons = []
    for row in range(start_row, end_row):
        for col in range(cols):
            x_min = -180.0 + col * cell_width
            x_max = x_min + cell_width
            y_max = 90.0 - row * cell_height
            y_min = y_max - cell_height
            poly = box(x_min, y_min, x_max, y_max)
            polygons.append(poly)
    return polygons


def buffer_features_chunk(features_chunk, buffer_distance=1.0):
    """Worker function for buffer operation on chunk"""
    gdf_chunk = features_chunk.copy()
    gdf_chunk['geometry'] = gdf_chunk.buffer(buffer_distance)
    return gdf_chunk


def generate_points_chunk(args):
    """Worker function for generating random points chunk"""
    seed_offset, count = args
    np.random.seed(42 + seed_offset)
    x_coords = np.random.uniform(-180, 180, count)
    y_coords = np.random.uniform(-90, 90, count)
    from shapely.geometry import Point
    return [Point(x, y) for x, y in zip(x_coords, y_coords)]


class MultiprocessBenchmarkOS(BaseBenchmark):
    """Base class for open-source multiprocess benchmarks"""
    
    def __init__(self, name, category="general"):
        super(MultiprocessBenchmarkOS, self).__init__(name, category)
        self.num_workers = settings.get_multiprocess_workers() if hasattr(settings, 'get_multiprocess_workers') else 4
    
    def run(self, num_runs=None, warmup_runs=None, use_multiprocess=False):
        """Run benchmark with optional multiprocessing"""
        if num_runs is None:
            num_runs = settings.TEST_RUNS
        if warmup_runs is None:
            warmup_runs = settings.WARMUP_RUNS
        
        py_version = "Py%d.%d" % (sys.version_info[0], sys.version_info[1])
        
        if use_multiprocess:
            print("\n  [%s] [OS多进程 %d进程] 初始化测试: %s" % (py_version, self.num_workers, self.name))
        else:
            print("\n  [%s] [OS单进程] 初始化测试: %s" % (py_version, self.name))
        
        print("  类别: %s" % self.category)
        
        # Setup
        print("  执行 setup()...")
        with ProgressHeartbeat("{} setup()".format(self.name)):
            self.setup()
        print("  [OK] setup() 完成")
        
        try:
            # Warmup runs
            if warmup_runs > 0:
                print("  预热运行 (%d 次)..." % warmup_runs)
                for i in range(warmup_runs):
                    result = self._run_single_iteration(
                        use_multiprocess=False,
                        progress_label="预热 %d/%d" % (i + 1, warmup_runs)
                    )
                    self.warmup_results.append(result)
            
            # Actual benchmark runs
            print("  正式测试运行 (%d 次)..." % num_runs)
            for i in range(num_runs):
                print("    运行 %d/%d..." % (i + 1, num_runs))
                mode_label = "多进程" if use_multiprocess else "单进程"
                result = self._run_single_iteration(
                    use_multiprocess=use_multiprocess,
                    progress_label="正式 %d/%d (%s)" % (i + 1, num_runs, mode_label)
                )
                self.results.append(result)
                
                if result.get('success'):
                    elapsed = result.get('elapsed_seconds', 0)
                    mode = result.get('mode', 'single')
                    print("      [OK] 耗时: %.4f秒 [%s]" % (elapsed, mode))
                else:
                    print("      [FAILED] %s" % result.get('error', 'Unknown error'))
        
        finally:
            # Teardown
            print("  执行 teardown()...")
            with ProgressHeartbeat("{} teardown()".format(self.name)):
                self.teardown()
            print("  [OK] teardown() 完成")
        
        # Add num_workers to statistics
        stats = self.get_statistics()
        stats['num_workers'] = self.num_workers if use_multiprocess else 1
        return stats
    
    def _run_single_iteration(self, use_multiprocess=False, progress_label=None):
        """Run a single iteration"""
        from utils.timer import BenchmarkTimer

        heartbeat_label = self.name
        if progress_label:
            heartbeat_label = "%s - %s" % (self.name, progress_label)

        with BenchmarkTimer(name=self.name, monitor_memory=settings.ENABLE_MEMORY_MONITORING) as bt:
            with ProgressHeartbeat(heartbeat_label):
                try:
                    if use_multiprocess:
                        result = self.run_multiprocess(self.num_workers)
                        result['mode'] = 'multiprocess'
                    else:
                        result = self.run_single()
                        result['mode'] = 'single'
                    result['success'] = True
                except Exception as e:
                    import traceback
                    result = {
                        'success': False,
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'mode': 'multiprocess' if use_multiprocess else 'single'
                    }
        
        timing_results = bt.get_results()
        result.update(timing_results)
        return result
    
    def run_single(self):
        raise NotImplementedError("Subclasses must implement run_single()")
    
    def run_multiprocess(self, num_workers):
        raise NotImplementedError("Subclasses must implement run_multiprocess()")


class MP_V1_CreateFishnet_OS(MultiprocessBenchmarkOS):
    """Multiprocess benchmark: Create Fishnet using GeoPandas"""
    
    def __init__(self):
        super(MP_V1_CreateFishnet_OS, self).__init__("MP_V1_CreateFishnet_OS", "vector_multiprocess")
        self.rows = settings.VECTOR_CONFIG['fishnet_rows']
        self.cols = settings.VECTOR_CONFIG['fishnet_cols']
        self.output_path = None
    
    def setup(self):
        self.output_path = os.path.join(settings.DATA_DIR, "MP_V1_fishnet_output_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Create fishnet grid using single process
        total_width = 360.0
        total_height = 180.0
        cell_width = total_width / self.cols
        cell_height = total_height / self.rows
        
        polygons = []
        for row in range(self.rows):
            for col in range(self.cols):
                x_min = -180.0 + col * cell_width
                x_max = x_min + cell_width
                y_max = 90.0 - row * cell_height
                y_min = y_max - cell_height
                poly = box(x_min, y_min, x_max, y_max)
                polygons.append(poly)
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(polygons), 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # Split work among workers
        total_width = 360.0
        total_height = 180.0
        cell_width = total_width / self.cols
        cell_height = total_height / self.rows
        
        # Calculate rows per worker
        rows_per_worker = self.rows // num_workers
        chunks = []
        for i in range(num_workers):
            start_row = i * rows_per_worker
            end_row = start_row + rows_per_worker if i < num_workers - 1 else self.rows
            chunks.append((start_row, end_row, self.cols, cell_width, cell_height))
        
        # Process in parallel
        with mp.Pool(processes=num_workers) as pool:
            results = pool.map(create_fishnet_chunk, chunks)
        
        # Combine results
        all_polygons = []
        for chunk_polygons in results:
            all_polygons.extend(chunk_polygons)
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(geometry=all_polygons, crs="EPSG:4326")
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(all_polygons), 'mode': 'multiprocess', 'workers': num_workers}


class MP_V2_CreateRandomPoints_OS(MultiprocessBenchmarkOS):
    """Multiprocess benchmark: Create Random Points using GeoPandas"""
    
    def __init__(self):
        super(MP_V2_CreateRandomPoints_OS, self).__init__("MP_V2_CreateRandomPoints_OS", "vector_multiprocess")
        self.num_points = settings.VECTOR_CONFIG['random_points']
        self.output_path = None
    
    def setup(self):
        self.output_path = os.path.join(settings.DATA_DIR, "MP_V2_random_points_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        np.random.seed(42)
        x_coords = np.random.uniform(-180, 180, self.num_points)
        y_coords = np.random.uniform(-90, 90, self.num_points)
        
        from shapely.geometry import Point
        points = [Point(x, y) for x, y in zip(x_coords, y_coords)]
        gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(points), 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # Generate points in parallel
        points_per_worker = self.num_points // num_workers

        # Create args list for worker function
        args_list = [(i, points_per_worker) for i in range(num_workers)]

        with mp.Pool(processes=num_workers) as pool:
            results = pool.map(generate_points_chunk, args_list)

        # Combine results
        all_points = []
        for chunk_points in results:
            all_points.extend(chunk_points)

        gdf = gpd.GeoDataFrame(geometry=all_points, crs="EPSG:4326")
        gdf.to_file(self.output_path, driver="GPKG")

        return {'features_created': len(all_points), 'mode': 'multiprocess', 'workers': num_workers}


class MP_V3_Buffer_OS(MultiprocessBenchmarkOS):
    """Multiprocess benchmark: Buffer Analysis using GeoPandas"""
    
    def __init__(self):
        super(MP_V3_Buffer_OS, self).__init__("MP_V3_Buffer_OS", "vector_multiprocess")
        self.gdb_path = None
        self.input_layer = None
        self.output_path = None
        self.buffer_distance = 1.0
    
    def setup(self):
        self.gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_layer = "buffer_points"
        self.output_path = os.path.join(settings.DATA_DIR, "MP_V3_buffer_output_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        gdf = gpd.read_file(self.gdb_path, layer=self.input_layer)
        gdf['geometry'] = gdf.buffer(self.buffer_distance)
        gdf.to_file(self.output_path, driver="GPKG")
        return {'features_created': len(gdf), 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # Read data
        gdf = gpd.read_file(self.gdb_path, layer=self.input_layer)
        
        # Split into chunks
        chunk_size = len(gdf) // num_workers
        chunks = []
        for i in range(num_workers):
            start = i * chunk_size
            end = start + chunk_size if i < num_workers - 1 else len(gdf)
            chunks.append(gdf.iloc[start:end].copy())
        
        # Process in parallel
        with mp.Pool(processes=num_workers) as pool:
            results = pool.map(partial(buffer_features_chunk, buffer_distance=self.buffer_distance), chunks)
        
        # Combine results
        import pandas as pd
        result_gdf = pd.concat(results, ignore_index=True)
        result_gdf = gpd.GeoDataFrame(result_gdf, crs=gdf.crs)
        result_gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(result_gdf), 'mode': 'multiprocess', 'workers': num_workers}


class MultiprocessTestsOS(object):
    """Collection of open-source multiprocess benchmarks"""
    
    @staticmethod
    def get_all_benchmarks():
        """Get all open-source multiprocess benchmark instances"""
        if not HAS_OS_LIBS:
            return []
        return [
            MP_V1_CreateFishnet_OS(),
            MP_V2_CreateRandomPoints_OS(),
            MP_V3_Buffer_OS(),
        ]


if __name__ == '__main__':
    if not HAS_OS_LIBS:
        print("Open-source libraries not available. Please install:")
        print("  pip install geopandas shapely")
        sys.exit(1)
    
    print("Testing open-source multiprocess benchmarks...")
    benchmarks = MultiprocessTestsOS.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: %s" % bm.name)
        try:
            # Test single process
            print("  Single process:")
            stats = bm.run(num_runs=1, warmup_runs=0, use_multiprocess=False)
            print("    Success: %s, Time: %.4fs" % (stats.get('success'), stats.get('mean_time', 0)))
            
            # Test multiprocess
            print("  Multiprocess (%d workers):" % bm.num_workers)
            stats = bm.run(num_runs=1, warmup_runs=0, use_multiprocess=True)
            print("    Success: %s, Time: %.4fs" % (stats.get('success'), stats.get('mean_time', 0)))
        except Exception as e:
            print("    Error: %s" % str(e))
