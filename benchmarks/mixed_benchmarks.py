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
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False
    arcpy = None

from config import settings
from benchmarks.base_benchmark import BaseBenchmark
from utils.benchmark_inputs import (
    get_analysis_boundary_extent,
    get_analysis_crs,
    get_analysis_raster_path,
    get_benchmark_gdb_path,
    get_input_feature_path,
)
from utils.benchmark_shapes import derive_block_size
from utils.gis_cleanup import clear_workspace_cache, remove_dataset_artifacts
from utils.raster_utils import create_constant_raster, create_block_pattern_raster


def _analysis_extent(default_size):
    """Return a square projected extent for fallback raster generation."""
    extent = get_analysis_boundary_extent(settings.DATA_DIR)
    if extent:
        return extent
    half = float(default_size) / 2.0
    return (-half, -half, half, half)


def _ensure_analysis_raster(output_path, raster_size):
    """Create a patterned analysis raster when the generated input is missing."""
    if arcpy.Exists(output_path):
        try:
            desc = arcpy.Describe(output_path)
            if int(getattr(desc, 'width', 0) or 0) == int(raster_size) and int(getattr(desc, 'height', 0) or 0) == int(raster_size):
                return output_path
        except Exception:
            pass

    extent = _analysis_extent(raster_size)
    sr = arcpy.SpatialReference(get_analysis_crs(settings.DATA_DIR))
    block_size = derive_block_size(int(raster_size), target_blocks_per_side=60, min_block_size=8)
    create_block_pattern_raster(
        output_path,
        cell_size=max(1.0, float(extent[2] - extent[0]) / float(raster_size)),
        extent=extent,
        block_size=block_size,
        levels=8,
        spatial_reference=sr
    )
    return output_path


def _get_raster_min_max(raster_path):
    """Return raster min/max values as floats."""
    r = arcpy.Raster(raster_path)
    return float(r.minimum), float(r.maximum)


class MixedBenchmarks(object):
    """Collection of mixed vector-raster benchmarks"""

    @staticmethod
    def get_all_benchmarks():
        """Get all mixed benchmark instances"""
        if not HAS_ARCPY:
            return []
        return [
            M1_PolygonToRaster(),
            M2_RasterToPoint(),
        ]


class M1_PolygonToRaster(BaseBenchmark):
    """Benchmark: Polygon to Raster Conversion"""

    def __init__(self, output_format='SHP'):
        super(M1_PolygonToRaster, self).__init__("M1_PolygonToRaster", "mixed")
        self.input_fc = None
        self.output_raster = None
        self.cell_size = None
        self.output_format = output_format
    
    def setup(self):
        clear_workspace_cache(settings.DATA_DIR)
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = get_benchmark_gdb_path(settings.DATA_DIR)
        self.input_fc = get_input_feature_path("test_polygons_a", settings.DATA_DIR)
        # Use version-specific output to avoid lock conflicts between Py2/Py3
        py_version = "py2" if sys.version_info[0] < 3 else "py3"
        self.output_raster = os.path.join(settings.DATA_DIR, "M1_poly_to_ras_{}.tif".format(py_version))
        
        # Calculate cell size based on data extent
        cfg = settings.get_raster_config_for_test('M1')
        raster_size = cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size'))
        extent = get_analysis_boundary_extent(settings.DATA_DIR)
        if extent:
            self.cell_size = max(1.0, float(extent[2] - extent[0]) / float(raster_size))
        else:
            self.cell_size = 1.0
    
    def teardown(self):
        if self.output_raster:
            remove_dataset_artifacts(self.output_raster)
    
    def run_single(self):
        # Delete if exists
        remove_dataset_artifacts(self.output_raster)

        input_desc = arcpy.Describe(self.input_fc)
        input_extent = input_desc.extent
        input_width = float(input_extent.XMax) - float(input_extent.XMin)
        input_height = float(input_extent.YMax) - float(input_extent.YMin)
        cfg = settings.get_raster_config_for_test('M1')
        raster_size = int(cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size')))
        self.cell_size = max(input_width, input_height) / float(raster_size)
        expected_width = int(round(input_width / self.cell_size))
        expected_height = int(round(input_height / self.cell_size))
        
        # Polygon to raster conversion
        arcpy.PolygonToRaster_conversion(
            in_features=self.input_fc,
            value_field="poly_id",
            out_rasterdataset=self.output_raster,
            cell_assignment="CELL_CENTER",
            priority_field="NONE",
            cellsize=self.cell_size
        )

        desc = arcpy.Describe(self.output_raster)
        output_width = int(desc.width)
        output_height = int(desc.height)
        if output_width != expected_width or output_height != expected_height:
            raise RuntimeError(
                "M1_PolygonToRaster 鏍￠獙澶辫触: 鏈熸湜 {}x{}锛屽疄闄?{}x{}".format(
                    expected_width, expected_height, output_width, output_height
                )
            )

        _, max_value = _get_raster_min_max(self.output_raster)
        if max_value <= 0:
            raise RuntimeError("M1_PolygonToRaster 鏍￠獙澶辫触: 杈撳嚭鏍呮牸涓虹┖鎴栧叏閮?0")

        return {
            'output_width': output_width,
            'output_height': output_height,
            'cell_size': desc.meanCellWidth,
            'validation_metric': 'polygon_to_raster_dimensions',
            'validation_expected': "{}x{}; max>0".format(expected_width, expected_height),
            'validation_observed': "{}x{}; max={:.1f}".format(output_width, output_height, max_value),
            'validation_passed': True,
        }


class M2_RasterToPoint(BaseBenchmark):
    """Benchmark: Raster to Point Conversion"""
    
    def __init__(self):
        super(M2_RasterToPoint, self).__init__("M2_RasterToPoint", "mixed")
        self.input_raster = None
        self.output_fc = None
    
    def setup(self):
        clear_workspace_cache(settings.DATA_DIR)
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        self.input_raster = get_analysis_raster_path(settings.DATA_DIR)
        self.output_fc = os.path.join(settings.DATA_DIR, "M2_ras_to_point.shp")

        # Keep this benchmark runnable without generating the full vector dataset.
        cfg = settings.get_raster_config_for_test('M2')
        expected_size = int(cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size')))
        needs_regen = True
        if arcpy.Exists(self.input_raster):
            try:
                desc = arcpy.Describe(self.input_raster)
                if int(getattr(desc, 'width', 0) or 0) == expected_size and int(getattr(desc, 'height', 0) or 0) == expected_size:
                    needs_regen = False
            except Exception:
                needs_regen = True

        if needs_regen:
            _ensure_analysis_raster(self.input_raster, expected_size)

    def _get_input_raster_stats(self):
        """Return input raster dimensions and the expected output count."""
        desc = arcpy.Describe(self.input_raster)
        input_width = int(getattr(desc, 'width', 0) or 0)
        input_height = int(getattr(desc, 'height', 0) or 0)

        if input_width <= 0 or input_height <= 0:
            raise RuntimeError(
                "M2_RasterToPoint 无法读取输入栅格尺寸: {}".format(self.input_raster)
            )

        cfg = settings.get_raster_config_for_test('M2')
        expected_size = int(cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size')))
        if input_width != expected_size or input_height != expected_size:
            raise RuntimeError(
                "M2_RasterToPoint 输入栅格尺寸不符合当前规模: 实际 {}x{}, 期望 {}x{}".format(
                    input_width, input_height, expected_size, expected_size
                )
            )

        expected_features = input_width * input_height
        return input_width, input_height, expected_features
    
    def teardown(self):
        if self.output_fc:
            remove_dataset_artifacts(self.output_fc)
    
    def run_single(self):
        # Delete if exists
        remove_dataset_artifacts(self.output_fc)

        input_width, input_height, expected_features = self._get_input_raster_stats()
        
        # Raster to point conversion. This should emit one point per valid raster cell.
        arcpy.RasterToPoint_conversion(
            in_raster=self.input_raster,
            out_point_features=self.output_fc,
            raster_field="Value"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        if count != expected_features:
            raise RuntimeError(
                "M2_RasterToPoint 输出数量校验失败: 输入 {}x{} 期望 {} 个点, 实际 {} 个点".format(
                    input_width,
                    input_height,
                    expected_features,
                    count
                )
            )

        return {
            'features_created': count,
            'expected_features': expected_features,
            'input_width': input_width,
            'input_height': input_height,
            'validation_metric': 'raster_to_point_feature_count',
            'validation_expected': expected_features,
            'validation_observed': count,
            'validation_passed': True,
        }


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
