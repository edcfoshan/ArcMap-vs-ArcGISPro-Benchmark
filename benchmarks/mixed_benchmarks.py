# -*- coding: utf-8 -*-
"""
Mixed (vector-raster) benchmarks
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import arcpy
    from arcpy.sa import *
except ImportError:
    print("Error: arcpy or arcpy.sa is not available")
    sys.exit(1)

from config import settings
from benchmarks.base_benchmark import BaseBenchmark


class MixedBenchmarks(object):
    """Collection of mixed vector-raster benchmarks"""
    
    @staticmethod
    def get_all_benchmarks():
        """Get all mixed benchmark instances"""
        return [
            M1_PolygonToRaster(),
            M2_RasterToPoint(),
        ]


class M1_PolygonToRaster(BaseBenchmark):
    """Benchmark: Polygon to Raster Conversion"""
    
    def __init__(self):
        super(M1_PolygonToRaster, self).__init__("M1_PolygonToRaster", "mixed")
        self.input_fc = None
        self.output_raster = None
        self.cell_size = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_fc = os.path.join(gdb_path, "test_polygons_a")
        # Use version-specific output to avoid lock conflicts between Py2/Py3
        py_version = "py2" if sys.version_info[0] < 3 else "py3"
        self.output_raster = os.path.join(settings.DATA_DIR, "M1_poly_to_ras_{}.tif".format(py_version))
        
        # Calculate cell size based on data extent
        raster_size = settings.RASTER_CONFIG['constant_raster_size']
        self.cell_size = 360.0 / raster_size
    
    def teardown(self):
        if self.output_raster and arcpy.Exists(self.output_raster):
            try:
                arcpy.Delete_management(self.output_raster)
            except Exception:
                pass
    
    def run_single(self):
        # Delete if exists
        if arcpy.Exists(self.output_raster):
            arcpy.Delete_management(self.output_raster)
        
        # Polygon to raster conversion
        arcpy.PolygonToRaster_conversion(
            in_features=self.input_fc,
            value_field="poly_id",
            out_rasterdataset=self.output_raster,
            cell_assignment="CELL_CENTER",
            priority_field="NONE",
            cellsize=self.cell_size
        )
        
        # Get raster info
        desc = arcpy.Describe(self.output_raster)
        return {
            'output_width': desc.width,
            'output_height': desc.height,
            'cell_size': desc.meanCellWidth
        }


class M2_RasterToPoint(BaseBenchmark):
    """Benchmark: Raster to Point Conversion"""
    
    def __init__(self):
        super(M2_RasterToPoint, self).__init__("M2_RasterToPoint", "mixed")
        self.input_raster = None
        self.output_fc = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_raster = os.path.join(gdb_path, "constant_raster")
        self.output_fc = os.path.join(settings.DATA_DIR, "M2_ras_to_point.shp")
    
    def teardown(self):
        if self.output_fc and arcpy.Exists(self.output_fc):
            try:
                arcpy.Delete_management(self.output_fc)
            except Exception:
                pass
    
    def run_single(self):
        # Delete if exists
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        # Raster to point conversion
        # Note: This can create a lot of points for large rasters
        # Using SAMPLE to reduce the number of points for performance
        arcpy.RasterToPoint_conversion(
            in_raster=self.input_raster,
            out_point_features=self.output_fc,
            raster_field="Value"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count}


if __name__ == '__main__':
    # Test individual benchmarks
    print("Testing Mixed Benchmarks...")
    
    benchmarks = MixedBenchmarks.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: {}".format(bm.name))
        try:
            stats = bm.run(num_runs=1, warmup_runs=0)
            print("  Success: {}".format(stats.get('success')))
            print("  Mean time: {:.4f}s".format(stats.get('mean_time', 0)))
        except Exception as e:
            print("  Error: {}".format(str(e)))
