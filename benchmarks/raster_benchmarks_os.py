# -*- coding: utf-8 -*-
"""
Raster data benchmarks using open-source libraries
Compatible with Python 3.x only
Uses Rasterio and NumPy
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import open-source libraries
try:
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject, Resampling
    from rasterio.mask import mask
    from rasterio import features
    HAS_OS_LIBS = True
except ImportError:
    HAS_OS_LIBS = False

from config import settings
from benchmarks.base_benchmark import BaseBenchmark


class RasterBenchmarksOS(object):
    """Collection of raster data benchmarks using open-source libraries"""
    
    @staticmethod
    def get_all_benchmarks():
        """Get all open-source raster benchmark instances"""
        if not HAS_OS_LIBS:
            return []
        return [
            R1_CreateConstantRaster_OS(),
            R2_Resample_OS(),
            R3_Clip_OS(),
            R4_RasterCalculator_OS(),
        ]


class R1_CreateConstantRaster_OS(BaseBenchmark):
    """Benchmark: Create Constant Raster using Rasterio"""
    
    def __init__(self):
        super(R1_CreateConstantRaster_OS, self).__init__("R1_CreateConstantRaster_OS", "raster_os")
        self.size = settings.RASTER_CONFIG['constant_raster_size']
        self.output_path = None
    
    def setup(self):
        self.output_path = os.path.join(settings.DATA_DIR, "R1_constant_raster_os.tif")
    
    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass
    
    def run_single(self):
        # Create constant raster using NumPy and Rasterio
        height = self.size
        width = self.size
        
        # Create transform (georeferencing)
        transform = from_bounds(-180, -90, 180, 90, width, height)
        
        # Create constant data
        data = np.ones((height, width), dtype=np.uint8)
        
        # Write to GeoTIFF
        profile = {
            'driver': 'GTiff',
            'height': height,
            'width': width,
            'count': 1,
            'dtype': data.dtype,
            'crs': 'EPSG:4326',
            'transform': transform,
            'compress': 'lzw'
        }
        
        with rasterio.open(self.output_path, 'w', **profile) as dst:
            dst.write(data, 1)
        
        return {'width': width, 'height': height}


class R2_Resample_OS(BaseBenchmark):
    """Benchmark: Raster Resample using Rasterio"""
    
    def __init__(self):
        super(R2_Resample_OS, self).__init__("R2_Resample_OS", "raster_os")
        self.source_size = settings.RASTER_CONFIG['resample_source_size']
        self.target_size = settings.RASTER_CONFIG['resample_target_size']
        self.input_path = None
        self.output_path = None
    
    def setup(self):
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        # Use the constant raster as input
        self.input_path = os.path.join(settings.DATA_DIR, "R1_constant_raster_os.tif")
        self.output_path = os.path.join(settings.DATA_DIR, "R2_resample_output_os.tif")
        
        # Create input if not exists (don't teardown - keep for other tests)
        if not os.path.exists(self.input_path):
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
        # Read input raster
        with rasterio.open(self.input_path) as src:
            data = src.read(1)
            src_crs = src.crs
            src_transform = src.transform
            
            # Calculate new transform
            dst_transform = from_bounds(-180, -90, 180, 90, self.target_size, self.target_size)
            
            # Create output array
            dst_data = np.empty((self.target_size, self.target_size), dtype=data.dtype)
            
            # Reproject/resample
            reproject(
                source=data,
                destination=dst_data,
                src_transform=src_transform,
                src_crs=src_crs,
                dst_transform=dst_transform,
                dst_crs=src_crs,
                resampling=Resampling.nearest
            )
        
        # Write output
        profile = {
            'driver': 'GTiff',
            'height': self.target_size,
            'width': self.target_size,
            'count': 1,
            'dtype': dst_data.dtype,
            'crs': src_crs,
            'transform': dst_transform,
            'compress': 'lzw'
        }
        
        with rasterio.open(self.output_path, 'w', **profile) as dst:
            dst.write(dst_data, 1)
        
        return {'output_width': self.target_size, 'output_height': self.target_size}


class R3_Clip_OS(BaseBenchmark):
    """Benchmark: Raster Clip using Rasterio"""
    
    def __init__(self):
        super(R3_Clip_OS, self).__init__("R3_Clip_OS", "raster_os")
        self.clip_ratio = settings.RASTER_CONFIG['clip_ratio']
        self.input_path = None
        self.output_path = None
    
    def setup(self):
        self.input_path = os.path.join(settings.DATA_DIR, "R1_constant_raster_os.tif")
        self.output_path = os.path.join(settings.DATA_DIR, "R3_clip_output_os.tif")
        
        # Create input if not exists (don't teardown - keep for other tests)
        if not os.path.exists(self.input_path):
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
        # Define clip extent (center 50%)
        x_range = 360 * self.clip_ratio
        y_range = 180 * self.clip_ratio
        x_min = -x_range / 2
        y_min = -y_range / 2
        x_max = x_range / 2
        y_max = y_range / 2
        
        # Create clip geometry
        from shapely.geometry import box
        clip_geom = box(x_min, y_min, x_max, y_max)
        
        # Clip raster
        with rasterio.open(self.input_path) as src:
            out_image, out_transform = mask(src, [clip_geom], crop=True)
            out_meta = src.meta.copy()
            
            # Update metadata
            out_meta.update({
                'driver': 'GTiff',
                'height': out_image.shape[1],
                'width': out_image.shape[2],
                'transform': out_transform,
                'compress': 'lzw'
            })
        
        # Write output
        with rasterio.open(self.output_path, 'w', **out_meta) as dst:
            dst.write(out_image)
        
        return {'output_width': out_image.shape[2], 'output_height': out_image.shape[1]}


class R4_RasterCalculator_OS(BaseBenchmark):
    """Benchmark: Raster Calculator using Rasterio/NumPy"""
    
    def __init__(self):
        super(R4_RasterCalculator_OS, self).__init__("R4_RasterCalculator_OS", "raster_os")
        self.input_path = None
        self.output_path = None
    
    def setup(self):
        self.input_path = os.path.join(settings.DATA_DIR, "R1_constant_raster_os.tif")
        self.output_path = os.path.join(settings.DATA_DIR, "R4_calc_output_os.tif")
        
        # Create input if not exists (don't teardown - keep for other tests)
        if not os.path.exists(self.input_path):
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
        # Read input
        with rasterio.open(self.input_path) as src:
            data = src.read(1).astype(np.float32)
            meta = src.meta.copy()
            
            # Perform calculation: Int(raster * 2)
            result = (data * 2).astype(np.uint8)
            
            # Update metadata
            meta.update({
                'dtype': result.dtype,
                'compress': 'lzw'
            })
        
        # Write output
        with rasterio.open(self.output_path, 'w', **meta) as dst:
            dst.write(result, 1)
        
        return {'output_width': result.shape[1], 'output_height': result.shape[0]}


if __name__ == '__main__':
    if not HAS_OS_LIBS:
        print("Open-source libraries not available. Please install:")
        print("  pip install rasterio numpy")
        sys.exit(1)
    
    print("Testing open-source raster benchmarks...")
    benchmarks = RasterBenchmarksOS.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: {}".format(bm.name))
        try:
            stats = bm.run(num_runs=1, warmup_runs=0)
            print("  Success: {}".format(stats.get('success')))
            print("  Mean time: {:.4f}s".format(stats.get('mean_time', 0)))
        except Exception as e:
            print("  Error: {}".format(str(e)))
