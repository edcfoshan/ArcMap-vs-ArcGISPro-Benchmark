# -*- coding: utf-8 -*-
"""
Mixed (vector-raster) benchmarks using open-source libraries
Compatible with Python 3.x only
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import open-source libraries
try:
    import geopandas as gpd
    import rasterio
    from rasterio import features
    from rasterio.transform import from_bounds
    from shapely.geometry import Point
    HAS_OS_LIBS = True
except ImportError:
    HAS_OS_LIBS = False

from config import settings
from benchmarks.base_benchmark import BaseBenchmark


class MixedBenchmarksOS(object):
    """Collection of mixed vector-raster benchmarks using open-source libraries"""
    
    @staticmethod
    def get_all_benchmarks():
        """Get all open-source mixed benchmark instances"""
        if not HAS_OS_LIBS:
            return []
        return [
            M1_PolygonToRaster_OS(),
            M2_RasterToPoint_OS(),
        ]


class M1_PolygonToRaster_OS(BaseBenchmark):
    """Benchmark: Polygon to Raster Conversion using Rasterio"""
    
    def __init__(self):
        super(M1_PolygonToRaster_OS, self).__init__("M1_PolygonToRaster_OS", "mixed_os")
        self.gdb_path = None
        self.input_layer = None
        self.output_path = None
        self.cell_size = None
    
    def setup(self):
        self.gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_layer = "test_polygons_a"
        self.output_path = os.path.join(settings.DATA_DIR, "M1_poly_to_ras_os.tif")
        
        # Calculate cell size
        raster_size = settings.RASTER_CONFIG['constant_raster_size']
        self.cell_size = 360.0 / raster_size
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Read polygons (using layer parameter)
        gdf = gpd.read_file(self.gdb_path, layer=self.input_layer)
        
        # Rasterize
        raster_size = settings.RASTER_CONFIG['constant_raster_size']
        transform = from_bounds(-180, -90, 180, 90, raster_size, raster_size)
        
        # Create shapes for rasterization (geometry, value pairs)
        shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf['poly_id']))
        
        # Rasterize
        result = features.rasterize(
            shapes=shapes,
            out_shape=(raster_size, raster_size),
            transform=transform,
            fill=0,
            dtype=np.int32
        )
        
        # Write to GeoTIFF
        profile = {
            'driver': 'GTiff',
            'height': raster_size,
            'width': raster_size,
            'count': 1,
            'dtype': result.dtype,
            'crs': 'EPSG:4326',
            'transform': transform,
            'compress': 'lzw'
        }
        
        with rasterio.open(self.output_path, 'w', **profile) as dst:
            dst.write(result, 1)
        
        return {'output_width': raster_size, 'output_height': raster_size}


class M2_RasterToPoint_OS(BaseBenchmark):
    """Benchmark: Raster to Points using Rasterio and GeoPandas"""
    
    def __init__(self):
        super(M2_RasterToPoint_OS, self).__init__("M2_RasterToPoint_OS", "mixed_os")
        self.input_path = None
        self.output_path = None
    
    def setup(self):
        # First create a raster if not exists
        self.input_path = os.path.join(settings.DATA_DIR, "R1_constant_raster_os.tif")
        self.output_path = os.path.join(settings.DATA_DIR, "M2_raster_to_point_os.gpkg")
        
        # Create input if not exists (don't teardown - keep for other tests)
        if not os.path.exists(self.input_path):
            from benchmarks.raster_benchmarks_os import R1_CreateConstantRaster_OS
            r1 = R1_CreateConstantRaster_OS()
            r1.setup()
            r1.run_single()  # Keep the file, don't call teardown()
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Read raster
        with rasterio.open(self.input_path) as src:
            data = src.read(1)
            transform = src.transform
            
            # Get coordinates of each pixel center
            rows, cols = np.where(data > 0)  # Get non-zero pixels
            
            # Sample to get coordinates
            xs, ys = rasterio.transform.xy(transform, rows, cols)
            
            # Create points
            points = [Point(x, y) for x, y in zip(xs, ys)]
            values = data[rows, cols]
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame({'value': values}, geometry=points, crs="EPSG:4326")
        
        # Save to GeoPackage
        gdf.to_file(self.output_path, driver="GPKG")
        
        return {'features_created': len(gdf)}


if __name__ == '__main__':
    if not HAS_OS_LIBS:
        print("Open-source libraries not available. Please install:")
        print("  pip install geopandas rasterio shapely")
        sys.exit(1)
    
    print("Testing open-source mixed benchmarks...")
    benchmarks = MixedBenchmarksOS.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: {}".format(bm.name))
        try:
            stats = bm.run(num_runs=1, warmup_runs=0)
            print("  Success: {}".format(stats.get('success')))
            print("  Mean time: {:.4f}s".format(stats.get('mean_time', 0)))
        except Exception as e:
            print("  Error: {}".format(str(e)))
