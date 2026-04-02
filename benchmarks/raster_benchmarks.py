# -*- coding: utf-8 -*-
"""
Raster data benchmarks
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
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False
    arcpy = None

from config import settings
from benchmarks.base_benchmark import BaseBenchmark


class RasterBenchmarks(object):
    """Collection of raster data benchmarks"""

    @staticmethod
    def get_all_benchmarks():
        """Get all raster benchmark instances"""
        if not HAS_ARCPY:
            return []
        return [
            R1_CreateConstantRaster(),
            R2_Resample(),
            R3_Clip(),
            R4_RasterCalculator(),
        ]


class R1_CreateConstantRaster(BaseBenchmark):
    """Benchmark: Create Constant Raster"""
    
    def __init__(self):
        super(R1_CreateConstantRaster, self).__init__("R1_CreateConstantRaster", "raster")
        self.size = settings.RASTER_CONFIG['constant_raster_size']
        self.output_raster = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        self.output_raster = os.path.join(
            settings.DATA_DIR,
            "R1_constant_raster.tif"
        )
    
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
        
        # Create constant raster using arcpy.sa (pure arcpy, no numpy)
        cell_size = 360.0 / self.size
        extent = "-180 -90 180 90"
        
        try:
            # ArcGIS Pro style: CreateConstantRaster is a function in arcpy.sa
            out_raster = CreateConstantRaster(1, "INTEGER", cell_size, extent)
            out_raster.save(self.output_raster)
        except:
            # ArcGIS Desktop style: use arcpy.CreateConstantRaster_sa
            arcpy.CreateConstantRaster_sa(
                self.output_raster,
                1,
                "INTEGER",
                cell_size,
                extent
            )
        
        # Add projection
        sr = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
        arcpy.DefineProjection_management(self.output_raster, sr)
        
        # Get raster info
        desc = arcpy.Describe(self.output_raster)
        return {
            'width': desc.width,
            'height': desc.height,
            'cell_size': desc.meanCellWidth
        }


class R2_Resample(BaseBenchmark):
    """Benchmark: Raster Resample"""
    
    def __init__(self):
        super(R2_Resample, self).__init__("R2_Resample", "raster")
        self.source_size = settings.RASTER_CONFIG['resample_source_size']
        self.target_size = settings.RASTER_CONFIG['resample_target_size']
        self.input_raster = None
        self.output_raster = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        # Use file-based raster instead of GDB raster (GDB has issues with rasters)
        self.input_raster = os.path.join(settings.DATA_DIR, "constant_raster.tif")
        self.output_raster = os.path.join(settings.DATA_DIR, "R2_resample_output.tif")
        
        # Input raster should already exist from data generation
        # If not, we create it using arcpy.sa (pure arcpy)
        if not arcpy.Exists(self.input_raster):
            print("    Warning: input raster not found, creating with arcpy.sa...")
            try:
                cell_size = 360.0 / self.source_size
                extent = "-180 -90 180 90"
                out_raster = CreateConstantRaster(1, "INTEGER", cell_size, extent)
                out_raster.save(self.input_raster)
                sr = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
                arcpy.DefineProjection_management(self.input_raster, sr)
            except Exception as e:
                # Python 2/3 compatible error printing
                try:
                    error_msg = str(e)
                except UnicodeEncodeError:
                    error_msg = unicode(e).encode('utf-8', errors='replace')
                print("    Error creating raster: {}".format(error_msg))
    
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
        
        # Calculate new cell size
        new_cell_size = 360.0 / self.target_size
        
        # Resample
        arcpy.Resample_management(
            in_raster=self.input_raster,
            out_raster=self.output_raster,
            cell_size=new_cell_size,
            resampling_type="NEAREST"
        )
        
        # Get raster info
        desc = arcpy.Describe(self.output_raster)
        return {
            'output_width': desc.width,
            'output_height': desc.height,
            'cell_size': desc.meanCellWidth
        }


class R3_Clip(BaseBenchmark):
    """Benchmark: Raster Clip"""
    
    def __init__(self):
        super(R3_Clip, self).__init__("R3_Clip", "raster")
        self.clip_ratio = settings.RASTER_CONFIG['clip_ratio']
        self.input_raster = None
        self.output_raster = None
        self.clip_extent = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        # Use file-based raster instead of GDB raster
        self.input_raster = os.path.join(settings.DATA_DIR, "constant_raster.tif")
        self.output_raster = os.path.join(settings.DATA_DIR, "R3_clip_output.tif")
        
        # Calculate clip extent (center 50%)
        # Original: -180, -90, 180, 90
        x_range = 360 * self.clip_ratio
        y_range = 180 * self.clip_ratio
        x_min = -x_range / 2
        y_min = -y_range / 2
        x_max = x_range / 2
        y_max = y_range / 2
        self.clip_extent = "{} {} {} {}".format(x_min, y_min, x_max, y_max)
    
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
        
        # Clip raster
        arcpy.Clip_management(
            in_raster=self.input_raster,
            rectangle=self.clip_extent,
            out_raster=self.output_raster,
            nodata_value=None,
            clipping_geometry="NONE",
            maintain_clipping_extent="NO_MAINTAIN_EXTENT"
        )
        
        # Get raster info
        desc = arcpy.Describe(self.output_raster)
        return {
            'output_width': desc.width,
            'output_height': desc.height
        }


class R4_RasterCalculator(BaseBenchmark):
    """Benchmark: Raster Calculator"""
    
    def __init__(self):
        super(R4_RasterCalculator, self).__init__("R4_RasterCalculator", "raster")
        self.input_raster = None
        self.output_raster = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        # Use file-based raster instead of GDB raster
        self.input_raster = os.path.join(settings.DATA_DIR, "constant_raster.tif")
        self.output_raster = os.path.join(settings.DATA_DIR, "R4_calc_output.tif")
    
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

        # Try multiple approaches for compatibility with both ArcGIS Desktop and Pro
        last_error = None

        try:
            # Method 1: ArcGIS Pro style using arcpy.sa.Raster
            from arcpy.sa import Raster, Int, Times
            in_ras = Raster(self.input_raster)
            out_ras = Int(Times(in_ras, 2))
            out_ras.save(self.output_raster)
        except Exception as e1:
            last_error = e1
            try:
                # Method 2: Use arcpy.sa Times and Int directly
                import arcpy.sa as sa
                in_ras = sa.Raster(self.input_raster)
                out_ras = sa.Int(in_ras * 2)
                out_ras.save(self.output_raster)
            except Exception as e2:
                last_error = e2
                try:
                    # Method 3: Alternative using RasterCalculator tool (if available)
                    arcpy.env.workspace = os.path.dirname(self.output_raster)
                    out_name = os.path.basename(self.output_raster)
                    # Check if tool exists before calling
                    if hasattr(arcpy, 'gp') and hasattr(arcpy.gp, 'RasterCalculator_sa'):
                        arcpy.gp.RasterCalculator_sa('"{}" * 2'.format(self.input_raster), self.output_raster)
                    elif hasattr(arcpy, 'management') and hasattr(arcpy.management, 'RasterCalculator'):
                        arcpy.management.RasterCalculator('"{}" * 2'.format(self.input_raster), self.output_raster)
                    else:
                        # Fallback: use Con tool to create modified raster
                        import arcpy.sa as sa
                        in_ras = sa.Raster(self.input_raster)
                        out_ras = sa.Con(in_ras >= 0, in_ras * 2, in_ras * 2)
                        out_ras.save(self.output_raster)
                except Exception as e3:
                    last_error = e3
                    # Re-raise the last error to fail the benchmark
                    raise last_error

        # Get raster info
        desc = arcpy.Describe(self.output_raster)
        return {
            'output_width': desc.width,
            'output_height': desc.height
        }


if __name__ == '__main__':
    # Test individual benchmarks
    print("Testing Raster Benchmarks...")
    
    benchmarks = RasterBenchmarks.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: {}".format(bm.name))
        try:
            stats = bm.run(num_runs=1, warmup_runs=0)
            print("  Success: {}".format(stats.get('success')))
            print("  Mean time: {:.4f}s".format(stats.get('mean_time', 0)))
        except Exception as e:
            # Python 2/3 compatible error printing
            try:
                error_msg = str(e)
            except UnicodeEncodeError:
                error_msg = unicode(e).encode('utf-8', errors='replace')
            print("  Error: {}".format(error_msg))
