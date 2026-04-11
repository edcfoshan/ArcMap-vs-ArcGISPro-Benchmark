# -*- coding: utf-8 -*-
"""
Vector data benchmarks
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import random

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import arcpy
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False
    arcpy = None

from config import settings
from benchmarks.base_benchmark import BaseBenchmark
from utils.benchmark_inputs import (
    get_analysis_boundary_extent,
    get_analysis_boundary_path,
    get_analysis_crs,
    get_benchmark_gdb_path,
)
from utils.benchmark_shapes import factor_grid_dimensions, expected_offset_grid_intersections


def _validated_count_result(actual_count, expected_count, metric_name):
    """Return a validated benchmark payload for deterministic feature counts."""
    if int(actual_count) != int(expected_count):
        raise RuntimeError(
            "{} 鏍￠獙澶辫触: 鏈熸湜 {}锛屽疄闄?{}".format(metric_name, int(expected_count), int(actual_count))
        )

    return {
        'features_created': int(actual_count),
        'expected_features': int(expected_count),
        'validation_metric': metric_name,
        'validation_expected': int(expected_count),
        'validation_observed': int(actual_count),
        'validation_passed': True,
    }


def _format_extent(extent, default_extent=(-500000.0, -500000.0, 500000.0, 500000.0)):
    """Format an extent tuple for ArcPy geoprocessing calls."""
    values = extent or default_extent
    return "{} {} {} {}".format(float(values[0]), float(values[1]), float(values[2]), float(values[3]))


class VectorBenchmarks(object):
    """Collection of vector data benchmarks"""

    @staticmethod
    def get_all_benchmarks():
        """Get all vector benchmark instances"""
        if not HAS_ARCPY:
            return []
        return [
            V1_CreateFishnet(),
            V2_CreateRandomPoints(),
            V3_Buffer(),
            V4_Intersect(),
            V5_SpatialJoin(),
            V6_CalculateField(),
        ]


class V1_CreateFishnet(BaseBenchmark):
    """Benchmark: Create Fishnet"""
    
    def __init__(self):
        super(V1_CreateFishnet, self).__init__("V1_CreateFishnet", "vector")
        cfg = settings.get_vector_config_for_test('V1')
        self.rows = cfg['fishnet_rows']
        self.cols = cfg['fishnet_cols']
        self.output_fc = None
        self.boundary_fc = None
        self.boundary_extent = None
        self.spatial_reference = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        self.boundary_fc = get_analysis_boundary_path(settings.DATA_DIR)
        self.boundary_extent = get_analysis_boundary_extent(settings.DATA_DIR)
        self.spatial_reference = arcpy.SpatialReference(get_analysis_crs(settings.DATA_DIR))
        self.output_fc = os.path.join(
            settings.DATA_DIR,
            "V1_fishnet_output.shp"
        )
    
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
        
        # Create fishnet
        extent_values = self.boundary_extent or (-500000.0, -500000.0, 500000.0, 500000.0)
        arcpy.CreateFishnet_management(
            out_feature_class=self.output_fc,
            origin_coord="{} {}".format(extent_values[0], extent_values[1]),
            y_axis_coord="{} {}".format(extent_values[0], extent_values[1] + 10.0),
            cell_width=0,
            cell_height=0,
            number_rows=self.rows,
            number_columns=self.cols,
            corner_coord="{} {}".format(extent_values[2], extent_values[3]),
            labels="NO_LABELS",
            template="",
            geometry_type="POLYGON"
        )
        
        # Add spatial reference
        arcpy.DefineProjection_management(self.output_fc, self.spatial_reference or arcpy.SpatialReference(get_analysis_crs(settings.DATA_DIR)))
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return _validated_count_result(count, self.rows * self.cols, "fishnet_feature_count")


class V2_CreateRandomPoints(BaseBenchmark):
    """Benchmark: Create Random Points"""
    
    def __init__(self):
        super(V2_CreateRandomPoints, self).__init__("V2_CreateRandomPoints", "vector")
        cfg = settings.get_vector_config_for_test('V2')
        self.num_points = cfg['random_points']
        self.output_fc = None
        self.boundary_fc = None
        self.boundary_extent = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        self.boundary_fc = get_analysis_boundary_path(settings.DATA_DIR)
        self.boundary_extent = get_analysis_boundary_extent(settings.DATA_DIR)
        self.output_fc = os.path.join(
            settings.DATA_DIR,
            "V2_random_points.shp"
        )
    
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
        
        # Create random points
        create_kwargs = {
            'out_path': settings.DATA_DIR,
            'out_name': "V2_random_points",
            'number_of_points_or_field': self.num_points,
            'minimum_allowed_distance': "0 Meters",
        }
        if self.boundary_fc and arcpy.Exists(self.boundary_fc):
            create_kwargs['constraining_feature_class'] = self.boundary_fc
        else:
            create_kwargs['constraining_extent'] = _format_extent(self.boundary_extent)
        arcpy.CreateRandomPoints_management(**create_kwargs)
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return _validated_count_result(count, self.num_points, "random_point_count")


class V3_Buffer(BaseBenchmark):
    """Benchmark: Buffer Analysis"""
    
    def __init__(self):
        super(V3_Buffer, self).__init__("V3_Buffer", "vector")
        self.input_fc = None
        self.output_fc = None
        cfg = settings.get_vector_config_for_test('V3')
        self.num_points = cfg['buffer_points']
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = get_benchmark_gdb_path(settings.DATA_DIR)
        self.input_fc = os.path.join(gdb_path, "buffer_points")
        self.output_fc = os.path.join(settings.DATA_DIR, "V3_buffer_output.shp")

        if not arcpy.Exists(self.input_fc):
            arcpy.CreateRandomPoints_management(
                out_path=gdb_path,
                out_name="buffer_points",
                constraining_extent=_format_extent(get_analysis_boundary_extent(settings.DATA_DIR)),
                number_of_points_or_field=self.num_points,
                minimum_allowed_distance="0 Meters"
            )
    
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
        
        # Buffer analysis
        arcpy.Buffer_analysis(
            in_features=self.input_fc,
            out_feature_class=self.output_fc,
            buffer_distance_or_field="1000 Meters",
            line_side="FULL",
            line_end_type="ROUND",
            dissolve_option="NONE"
        )
        
        expected_count = int(arcpy.GetCount_management(self.input_fc)[0])
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return _validated_count_result(count, expected_count, "buffer_feature_count")


class V4_Intersect(BaseBenchmark):
    """Benchmark: Intersect Analysis"""
    
    def __init__(self):
        super(V4_Intersect, self).__init__("V4_Intersect", "vector")
        self.input_a = None
        self.input_b = None
        self.output_fc = None
        cfg = settings.get_vector_config_for_test('V4')
        rows_a, cols_a = factor_grid_dimensions(cfg['intersect_features_a'])
        rows_b, cols_b = factor_grid_dimensions(cfg['intersect_features_b'])
        self.expected_features = expected_offset_grid_intersections(rows_a, cols_a, rows_b, cols_b)
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = get_benchmark_gdb_path(settings.DATA_DIR)
        self.input_a = os.path.join(gdb_path, "test_polygons_a")
        self.input_b = os.path.join(gdb_path, "test_polygons_b")
        self.output_fc = os.path.join(settings.DATA_DIR, "V4_intersect_output.shp")
    
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
        
        # Intersect analysis
        arcpy.Intersect_analysis(
            in_features=[self.input_a, self.input_b],
            out_feature_class=self.output_fc,
            join_attributes="ALL",
            cluster_tolerance=None,
            output_type="INPUT"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return _validated_count_result(count, self.expected_features, "intersect_feature_count")


class V5_SpatialJoin(BaseBenchmark):
    """Benchmark: Spatial Join"""
    
    def __init__(self):
        super(V5_SpatialJoin, self).__init__("V5_SpatialJoin", "vector")
        self.target_features = None
        self.join_features = None
        self.output_fc = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = get_benchmark_gdb_path(settings.DATA_DIR)
        self.target_features = os.path.join(gdb_path, "spatial_join_points")
        self.join_features = os.path.join(gdb_path, "spatial_join_polygons")
        # Use version-specific output to avoid lock conflicts between Py2/Py3
        py_version = "py2" if sys.version_info[0] < 3 else "py3"
        self.output_fc = os.path.join(settings.DATA_DIR, "V5_spatial_join_output_{}.shp".format(py_version))
    
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
        
        # Spatial join
        arcpy.SpatialJoin_analysis(
            target_features=self.target_features,
            join_features=self.join_features,
            out_feature_class=self.output_fc,
            join_operation="JOIN_ONE_TO_ONE",
            join_type="KEEP_ALL"
        )
        
        expected_count = int(arcpy.GetCount_management(self.target_features)[0])
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return _validated_count_result(count, expected_count, "spatial_join_feature_count")


class V6_CalculateField(BaseBenchmark):
    """Benchmark: Calculate Field"""
    
    def __init__(self):
        super(V6_CalculateField, self).__init__("V6_CalculateField", "vector")
        self.input_fc = None
        self.working_fc = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = get_benchmark_gdb_path(settings.DATA_DIR)
        self.input_fc = os.path.join(gdb_path, "calculate_field_fc")
        self.working_fc = os.path.join(settings.DATA_DIR, "V6_calculate_field.shp")
        
        # Add field if not exists
        if arcpy.Exists(self.input_fc):
            field_names = [f.name for f in arcpy.ListFields(self.input_fc)]
            if "calc_field" not in field_names:
                arcpy.AddField_management(self.input_fc, "calc_field", "DOUBLE")
    
    def teardown(self):
        if self.working_fc and arcpy.Exists(self.working_fc):
            try:
                arcpy.Delete_management(self.working_fc)
            except Exception:
                pass
    
    def run_single(self):
        # Copy to working feature class
        if arcpy.Exists(self.working_fc):
            arcpy.Delete_management(self.working_fc)
        arcpy.CopyFeatures_management(self.input_fc, self.working_fc)
        
        # Add field if not exists
        field_names = [f.name for f in arcpy.ListFields(self.working_fc)]
        if "calc_field" not in field_names:
            arcpy.AddField_management(self.working_fc, "calc_field", "DOUBLE")
        
        # Calculate field with expression
        expression = "!poly_id! * 2.5 + 100"
        
        arcpy.CalculateField_management(
            in_table=self.working_fc,
            field="calc_field",
            expression=expression,
            expression_type="PYTHON"
        )

        count = int(arcpy.GetCount_management(self.working_fc)[0])
        sample_values = []
        with arcpy.da.SearchCursor(self.working_fc, ["poly_id", "calc_field"]) as cursor:
            for index, row in enumerate(cursor):
                poly_id = int(row[0])
                calc_value = float(row[1])
                expected_value = poly_id * 2.5 + 100.0
                if abs(calc_value - expected_value) > 1e-6:
                    raise RuntimeError(
                        "calculate_field_sample 鏍￠獙澶辫触: poly_id={} 鏈熸湜 {}锛屽疄闄?{}".format(
                            poly_id, expected_value, calc_value
                        )
                    )
                sample_values.append("{}->{:.1f}".format(poly_id, calc_value))
                if index >= 4:
                    break

        arcpy.Delete_management(self.working_fc)

        return {
            'features_processed': count,
            'expected_features': count,
            'validation_metric': 'calculate_field_samples',
            'validation_expected': "{} records; sample formula matches".format(count),
            'validation_observed': "; ".join(sample_values),
            'validation_passed': True,
        }


if __name__ == '__main__':
    # Test individual benchmarks
    print("Testing Vector Benchmarks...")
    
    benchmarks = VectorBenchmarks.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: {}".format(bm.name))
        try:
            stats = bm.run(num_runs=1, warmup_runs=0)
            print("  Success: {}".format(stats.get('success')))
            print("  Mean time: {:.4f}s".format(stats.get('mean_time', 0)))
        except Exception as e:
            print("  Error: {}".format(str(e)))
