# -*- coding: utf-8 -*-
"""
Vector data benchmarks using open-source libraries
Compatible with Python 3.x only
Uses GeoPandas, Shapely, and Pyogrio
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import numpy as np
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import open-source libraries
try:
    import geopandas as gpd
    from shapely.geometry import Polygon, Point, box
    from shapely.ops import unary_union
    import pyogrio
    HAS_OS_LIBS = True
except ImportError:
    HAS_OS_LIBS = False

from config import settings
from benchmarks.base_benchmark import BaseBenchmark


BUFFER_PROJECTED_CRS = "EPSG:3857"


def buffer_in_projected_crs(gdf, buffer_distance_meters, projected_crs=BUFFER_PROJECTED_CRS):
    """Buffer geometries in a projected CRS and return to the source CRS."""
    source_crs = gdf.crs
    if source_crs is None:
        raise RuntimeError("Input GeoDataFrame must define a CRS for buffer benchmarking")

    projected = gdf.to_crs(projected_crs)
    projected['geometry'] = projected.buffer(buffer_distance_meters)
    return projected.to_crs(source_crs)


class VectorBenchmarksOS(object):
    """Collection of vector data benchmarks using open-source libraries"""
    
    @staticmethod
    def get_all_benchmarks():
        """Get all open-source vector benchmark instances"""
        if not HAS_OS_LIBS:
            return []
        return [
            V1_CreateFishnet_OS(),
            V2_CreateRandomPoints_OS(),
            V3_Buffer_OS(),
            V4_Intersect_OS(),
            V5_SpatialJoin_OS(),
            V6_CalculateField_OS(),
        ]


class V1_CreateFishnet_OS(BaseBenchmark):
    """Benchmark: Create Fishnet using GeoPandas"""
    
    def __init__(self):
        super(V1_CreateFishnet_OS, self).__init__("V1_CreateFishnet_OS", "vector_os")
        self.rows = settings.VECTOR_CONFIG['fishnet_rows']
        self.cols = settings.VECTOR_CONFIG['fishnet_cols']
        self.output_path = None
    
    def setup(self):
        self.output_path = os.path.join(settings.DATA_DIR, "V1_fishnet_output_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Create fishnet grid using GeoPandas/Shapely
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
        
        # Save to GeoPackage
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(polygons)}


class V2_CreateRandomPoints_OS(BaseBenchmark):
    """Benchmark: Create Random Points using GeoPandas"""
    
    def __init__(self):
        super(V2_CreateRandomPoints_OS, self).__init__("V2_CreateRandomPoints_OS", "vector_os")
        self.num_points = settings.VECTOR_CONFIG['random_points']
        self.output_path = None
    
    def setup(self):
        self.output_path = os.path.join(settings.DATA_DIR, "V2_random_points_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Generate random points
        np.random.seed(42)  # For reproducibility
        x_coords = np.random.uniform(-180, 180, self.num_points)
        y_coords = np.random.uniform(-90, 90, self.num_points)
        
        points = [Point(x, y) for x, y in zip(x_coords, y_coords)]
        gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")
        
        # Save to GeoPackage
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(points)}


class V3_Buffer_OS(BaseBenchmark):
    """Benchmark: Buffer Analysis using GeoPandas"""
    
    def __init__(self):
        super(V3_Buffer_OS, self).__init__("V3_Buffer_OS", "vector_os")
        self.gdb_path = None
        self.input_layer = None
        self.output_path = None
        self.buffer_distance = 1000.0  # meters
    
    def setup(self):
        self.gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_layer = "buffer_points"
        self.output_path = os.path.join(settings.DATA_DIR, "V3_buffer_output_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Read input points from GDB (using layer parameter)
        gdf = gpd.read_file(self.gdb_path, layer=self.input_layer)
        
        # Buffer in a projected CRS so the 1 km distance matches the ArcPy benchmark.
        gdf = buffer_in_projected_crs(gdf, self.buffer_distance)
        
        # Save output
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(gdf)}


class V4_Intersect_OS(BaseBenchmark):
    """Benchmark: Intersect Analysis using GeoPandas"""
    
    def __init__(self):
        super(V4_Intersect_OS, self).__init__("V4_Intersect_OS", "vector_os")
        self.gdb_path = None
        self.input_a_layer = None
        self.input_b_layer = None
        self.output_path = None
    
    def setup(self):
        self.gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_a_layer = "test_polygons_a"
        self.input_b_layer = "test_polygons_b"
        self.output_path = os.path.join(settings.DATA_DIR, "V4_intersect_output_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Read input layers (using layer parameter)
        gdf_a = gpd.read_file(self.gdb_path, layer=self.input_a_layer)
        gdf_b = gpd.read_file(self.gdb_path, layer=self.input_b_layer)
        
        # Perform intersection
        result = gpd.overlay(gdf_a, gdf_b, how='intersection')
        
        # Save output
        result.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(result)}


class V5_SpatialJoin_OS(BaseBenchmark):
    """Benchmark: Spatial Join using GeoPandas"""
    
    def __init__(self):
        super(V5_SpatialJoin_OS, self).__init__("V5_SpatialJoin_OS", "vector_os")
        self.gdb_path = None
        self.target_layer = None
        self.join_layer = None
        self.output_path = None
    
    def setup(self):
        self.gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.target_layer = "spatial_join_points"
        self.join_layer = "spatial_join_polygons"
        self.output_path = os.path.join(settings.DATA_DIR, "V5_spatial_join_output_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Read input layers (using layer parameter)
        target = gpd.read_file(self.gdb_path, layer=self.target_layer)
        join = gpd.read_file(self.gdb_path, layer=self.join_layer)
        
        # Perform spatial join
        result = gpd.sjoin(target, join, how='left', predicate='within')
        
        # Save output
        result.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(result)}


class V6_CalculateField_OS(BaseBenchmark):
    """Benchmark: Calculate Field using GeoPandas"""
    
    def __init__(self):
        super(V6_CalculateField_OS, self).__init__("V6_CalculateField_OS", "vector_os")
        self.gdb_path = None
        self.input_layer = None
        self.output_path = None
    
    def setup(self):
        self.gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_layer = "calculate_field_fc"
        self.output_path = os.path.join(settings.DATA_DIR, "V6_calculate_field_os.gpkg")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Read input (using layer parameter)
        gdf = gpd.read_file(self.gdb_path, layer=self.input_layer)
        
        # Perform field calculation (vectorized)
        gdf['calc_field'] = gdf['poly_id'] * 2.5 + 100
        
        # Save output
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_processed': len(gdf)}


if __name__ == '__main__':
    if not HAS_OS_LIBS:
        print("Open-source libraries not available. Please install:")
        print("  pip install geopandas shapely pyogrio")
        sys.exit(1)
    
    print("Testing open-source vector benchmarks...")
    benchmarks = VectorBenchmarksOS.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: {}".format(bm.name))
        try:
            stats = bm.run(num_runs=1, warmup_runs=0)
            print("  Success: {}".format(stats.get('success')))
            print("  Mean time: {:.4f}s".format(stats.get('mean_time', 0)))
        except Exception as e:
            print("  Error: {}".format(str(e)))
