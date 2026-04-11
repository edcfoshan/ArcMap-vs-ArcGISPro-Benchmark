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
from utils.gis_cleanup import clear_workspace_cache, remove_dataset_artifacts
from utils.benchmark_inputs import (
    get_analysis_boundary_extent,
    get_analysis_crs,
    get_analysis_raster_path,
)
from utils.benchmark_shapes import derive_block_size
from utils.raster_utils import create_constant_raster, create_block_pattern_raster, double_raster, expected_clip_dimension


def _constant_raster_extent(size):
    """Return the synthetic local extent used by raster benchmarks."""
    size = int(size)
    return "0 0 {0} {0}".format(size)


def _analysis_extent(size):
    """Return the projected analysis extent used for patterned raster fallbacks."""
    extent = get_analysis_boundary_extent(settings.DATA_DIR)
    if extent:
        return extent
    half = float(size) / 2.0
    return (-half, -half, half, half)


def _ensure_analysis_raster(output_path, raster_size):
    """Create a patterned raster when the generated analysis raster is missing."""
    if os.path.exists(output_path):
        try:
            desc = arcpy.Describe(output_path)
            if int(getattr(desc, 'width', 0) or 0) == int(raster_size) and int(getattr(desc, 'height', 0) or 0) == int(raster_size):
                return output_path
        except Exception:
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
    try:
        create_block_pattern_raster(
            output_path,
            cell_size=max(1.0, float(extent[2] - extent[0]) / float(raster_size)),
            extent=extent,
            block_size=block_size,
            levels=8,
            spatial_reference=sr
        )
    except RuntimeError as exc:
        # If the file already exists but ArcPy momentarily refuses to recreate it,
        # reuse the existing raster when it still matches the requested size.
        if os.path.exists(output_path):
            try:
                desc = arcpy.Describe(output_path)
                if int(getattr(desc, 'width', 0) or 0) == int(raster_size) and int(getattr(desc, 'height', 0) or 0) == int(raster_size):
                    return output_path
            except Exception:
                pass
        raise
    return output_path


def _get_raster_min_max(raster_path):
    """Return raster min/max values as floats."""
    min_value = float(arcpy.GetRasterProperties_management(raster_path, "MINIMUM")[0])
    max_value = float(arcpy.GetRasterProperties_management(raster_path, "MAXIMUM")[0])
    return min_value, max_value


def _validated_raster_result(raster_path, expected_width, expected_height, metric_name, expected_min=None, expected_max=None):
    """Validate raster dimensions and optional value range."""
    desc = arcpy.Describe(raster_path)
    actual_width = int(desc.width)
    actual_height = int(desc.height)

    if actual_width != int(expected_width) or actual_height != int(expected_height):
        raise RuntimeError(
            "{} 鏍￠獙澶辫触: 鏈熸湜 {}x{}锛屽疄闄?{}x{}".format(
                metric_name, int(expected_width), int(expected_height), actual_width, actual_height
            )
        )

    observed_value = "{}x{}".format(actual_width, actual_height)
    expected_value = "{}x{}".format(int(expected_width), int(expected_height))

    if expected_min is not None or expected_max is not None:
        min_value, max_value = _get_raster_min_max(raster_path)
        if expected_min is not None and abs(min_value - float(expected_min)) > 1e-6:
            raise RuntimeError(
                "{} 鏍￠獙澶辫触: MINIMUM 鏈熸湜 {}锛屽疄闄?{}".format(metric_name, float(expected_min), min_value)
            )
        if expected_max is not None and abs(max_value - float(expected_max)) > 1e-6:
            raise RuntimeError(
                "{} 鏍￠獙澶辫触: MAXIMUM 鏈熸湜 {}锛屽疄闄?{}".format(metric_name, float(expected_max), max_value)
            )
        expected_value = "{}; value={}..{}".format(expected_value, expected_min, expected_max)
        observed_value = "{}; value={:.1f}..{:.1f}".format(observed_value, min_value, max_value)

    return {
        'output_width': actual_width,
        'output_height': actual_height,
        'validation_metric': metric_name,
        'validation_expected': expected_value,
        'validation_observed': observed_value,
        'validation_passed': True,
    }


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
        cfg = settings.get_raster_config_for_test('R1')
        self.size = cfg['constant_raster_size']
        self.output_raster = None
    
    def setup(self):
        clear_workspace_cache(settings.DATA_DIR)
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        self.output_raster = os.path.join(
            settings.DATA_DIR,
            "R1_constant_raster.tif"
        )
    
    def teardown(self):
        if self.output_raster:
            remove_dataset_artifacts(self.output_raster)
    
    def run_single(self):
        # Delete if exists
        remove_dataset_artifacts(self.output_raster)
        
        cell_size = 1
        extent = _constant_raster_extent(self.size)
        sr = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
        create_constant_raster(
            self.output_raster,
            cell_size=cell_size,
            extent=extent,
            value=1,
            spatial_reference=sr,
            use_spatial_analyst=False
        )

        return _validated_raster_result(
            self.output_raster,
            self.size,
            self.size,
            "constant_raster_dimensions",
            expected_min=1,
            expected_max=1
        )


class R2_Resample(BaseBenchmark):
    """Benchmark: Raster Resample"""
    
    def __init__(self):
        super(R2_Resample, self).__init__("R2_Resample", "raster")
        cfg = settings.get_raster_config_for_test('R2')
        self.source_size = cfg.get('resample_source_size', cfg.get('analysis_raster_size'))
        self.target_size = cfg.get('resample_target_size', cfg.get('analysis_raster_target_size'))
        self.input_raster = None
        self.output_raster = None
    
    def setup(self):
        clear_workspace_cache(settings.DATA_DIR)
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        # Use a dedicated source raster so standard can tune R2 without affecting other tests.
        self.input_raster = os.path.join(settings.DATA_DIR, "analysis_raster_R2.tif")
        self.output_raster = os.path.join(settings.DATA_DIR, "R2_resample_output.tif")
        
        if not arcpy.Exists(self.input_raster):
            _ensure_analysis_raster(self.input_raster, self.source_size)
    
    def teardown(self):
        if self.output_raster:
            remove_dataset_artifacts(self.output_raster)
    
    def run_single(self):
        # Delete if exists
        remove_dataset_artifacts(self.output_raster)

        # Scale by the input raster's real cell size so the output stays at the
        # requested pixel dimensions even when the geographic extent changes.
        input_desc = arcpy.Describe(self.input_raster)
        input_cell_size = float(getattr(input_desc, 'meanCellWidth', 1.0) or 1.0)
        new_cell_size = input_cell_size * float(self.source_size) / float(self.target_size)
        
        # Resample
        arcpy.Resample_management(
            in_raster=self.input_raster,
            out_raster=self.output_raster,
            cell_size=new_cell_size,
            resampling_type="NEAREST"
        )
        
        result = _validated_raster_result(
            self.output_raster,
            self.target_size,
            self.target_size,
            "resample_raster_dimensions",
            expected_min=_get_raster_min_max(self.input_raster)[0],
            expected_max=_get_raster_min_max(self.input_raster)[1]
        )
        result['cell_size'] = new_cell_size
        return result


class R3_Clip(BaseBenchmark):
    """Benchmark: Raster Clip"""
    
    def __init__(self):
        super(R3_Clip, self).__init__("R3_Clip", "raster")
        cfg = settings.get_raster_config_for_test('R3')
        self.clip_ratio = cfg.get('analysis_raster_clip_ratio', cfg.get('clip_ratio'))
        self.input_raster = None
        self.output_raster = None
        self.clip_extent = None
    
    def setup(self):
        clear_workspace_cache(settings.DATA_DIR)
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        # Use a dedicated source raster so standard can tune R3 without affecting other tests.
        self.input_raster = os.path.join(settings.DATA_DIR, "analysis_raster_R3.tif")
        self.output_raster = os.path.join(settings.DATA_DIR, "R3_clip_output.tif")
        
        self.clip_extent = None
        if not arcpy.Exists(self.input_raster):
            cfg = settings.get_raster_config_for_test('R3')
            _ensure_analysis_raster(self.input_raster, cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size')))
    
    def teardown(self):
        if self.output_raster:
            remove_dataset_artifacts(self.output_raster)
    
    def run_single(self):
        # Delete if exists
        remove_dataset_artifacts(self.output_raster)

        input_desc = arcpy.Describe(self.input_raster)
        input_width = int(input_desc.width)
        input_height = int(input_desc.height)
        expected_width = expected_clip_dimension(input_width, self.clip_ratio)
        expected_height = expected_clip_dimension(input_height, self.clip_ratio)
        start_x = max(0, int(round((input_width - expected_width) / 2.0)))
        start_y = max(0, int(round((input_height - expected_height) / 2.0)))
        end_x = start_x + expected_width
        end_y = start_y + expected_height

        # Use an explicit centered cell window so Py2 and Py3 keep the same
        # dimensions. ArcPy Clip_management can return an off-by-one column on
        # some installations, while RasterToNumPyArray preserves the exact
        # window size we want for the benchmark contract.
        raster_array = arcpy.RasterToNumPyArray(self.input_raster)
        clipped_array = raster_array[start_y:end_y, start_x:end_x]
        lower_left = arcpy.Point(
            float(input_desc.extent.XMin) + start_x * float(getattr(input_desc, 'meanCellWidth', 1.0) or 1.0),
            float(input_desc.extent.YMin) + start_y * float(getattr(input_desc, 'meanCellHeight', 1.0) or 1.0)
        )
        clipped_raster = arcpy.NumPyArrayToRaster(
            clipped_array,
            lower_left,
            float(getattr(input_desc, 'meanCellWidth', 1.0) or 1.0),
            float(getattr(input_desc, 'meanCellHeight', 1.0) or 1.0)
        )
        clipped_raster.save(self.output_raster)
        if hasattr(input_desc, 'spatialReference') and input_desc.spatialReference:
            try:
                arcpy.DefineProjection_management(self.output_raster, input_desc.spatialReference)
            except Exception:
                pass

        return _validated_raster_result(
            self.output_raster,
            expected_width,
            expected_height,
            "clip_raster_dimensions",
            expected_min=_get_raster_min_max(self.input_raster)[0],
            expected_max=_get_raster_min_max(self.input_raster)[1]
        )


class R4_RasterCalculator(BaseBenchmark):
    """Benchmark: Raster Calculator"""
    
    def __init__(self):
        super(R4_RasterCalculator, self).__init__("R4_RasterCalculator", "raster")
        self.input_raster = None
        self.output_raster = None
    
    def setup(self):
        clear_workspace_cache(settings.DATA_DIR)
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        # Use a dedicated source raster so standard can tune R4 without affecting other tests.
        self.input_raster = os.path.join(settings.DATA_DIR, "analysis_raster_R4.tif")
        self.output_raster = os.path.join(settings.DATA_DIR, "R4_calc_output.tif")
        if not arcpy.Exists(self.input_raster):
            cfg = settings.get_raster_config_for_test('R4')
            _ensure_analysis_raster(self.input_raster, cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size')))
    
    def teardown(self):
        if self.output_raster:
            remove_dataset_artifacts(self.output_raster)
    
    def run_single(self):
        # Delete if exists
        remove_dataset_artifacts(self.output_raster)
        double_raster(self.input_raster, self.output_raster, use_spatial_analyst=False)

        input_desc = arcpy.Describe(self.input_raster)
        input_min, input_max = _get_raster_min_max(self.input_raster)
        return _validated_raster_result(
            self.output_raster,
            int(input_desc.width),
            int(input_desc.height),
            "raster_calculator_dimensions",
            expected_min=input_min * 2,
            expected_max=input_max * 2
        )


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
