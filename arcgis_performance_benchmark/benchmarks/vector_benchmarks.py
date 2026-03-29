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
except ImportError:
    print("Error: arcpy is not available")
    sys.exit(1)

from config import settings
from benchmarks.base_benchmark import BaseBenchmark


class VectorBenchmarks(object):
    """Collection of vector data benchmarks"""
    
    @staticmethod
    def get_all_benchmarks():
        """Get all vector benchmark instances"""
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
        self.rows = settings.VECTOR_CONFIG['fishnet_rows']
        self.cols = settings.VECTOR_CONFIG['fishnet_cols']
        self.output_fc = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
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
        arcpy.CreateFishnet_management(
            out_feature_class=self.output_fc,
            origin_coord="-180 -90",
            y_axis_coord="-180 -80",
            cell_width=0,
            cell_height=0,
            number_rows=self.rows,
            number_columns=self.cols,
            corner_coord="180 90",
            labels="NO_LABELS",
            template="",
            geometry_type="POLYGON"
        )
        
        # Add spatial reference
        sr = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
        arcpy.DefineProjection_management(self.output_fc, sr)
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count}


class V2_CreateRandomPoints(BaseBenchmark):
    """Benchmark: Create Random Points"""
    
    def __init__(self):
        super(V2_CreateRandomPoints, self).__init__("V2_CreateRandomPoints", "vector")
        self.num_points = settings.VECTOR_CONFIG['random_points']
        self.output_fc = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
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
        arcpy.CreateRandomPoints_management(
            out_path=settings.DATA_DIR,
            out_name="V2_random_points",
            constraining_extent="-180 -90 180 90",
            number_of_points_or_field=self.num_points,
            minimum_allowed_distance="0 DecimalDegrees"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count}


class V3_Buffer(BaseBenchmark):
    """Benchmark: Buffer Analysis"""
    
    def __init__(self):
        super(V3_Buffer, self).__init__("V3_Buffer", "vector")
        self.input_fc = None
        self.output_fc = None
        self.num_points = settings.VECTOR_CONFIG['buffer_points']
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        # Create input data if not exists
        self.input_fc = os.path.join(settings.DATA_DIR, "V3_buffer_input.shp")
        self.output_fc = os.path.join(settings.DATA_DIR, "V3_buffer_output.shp")
        
        if not arcpy.Exists(self.input_fc):
            print("    Creating input data...")
            arcpy.CreateRandomPoints_management(
                out_path=settings.DATA_DIR,
                out_name="V3_buffer_input",
                constraining_extent="-180 -90 180 90",
                number_of_points_or_field=self.num_points,
                minimum_allowed_distance="0 DecimalDegrees"
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
            buffer_distance_or_field="1 DecimalDegrees",
            line_side="FULL",
            line_end_type="ROUND",
            dissolve_option="NONE"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count}


class V4_Intersect(BaseBenchmark):
    """Benchmark: Intersect Analysis"""
    
    def __init__(self):
        super(V4_Intersect, self).__init__("V4_Intersect", "vector")
        self.input_a = None
        self.input_b = None
        self.output_fc = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
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
        return {'features_created': count}


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
        
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.target_features = os.path.join(gdb_path, "spatial_join_points")
        self.join_features = os.path.join(gdb_path, "spatial_join_polygons")
        self.output_fc = os.path.join(settings.DATA_DIR, "V5_spatial_join_output.shp")
    
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
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count}


class V6_CalculateField(BaseBenchmark):
    """Benchmark: Calculate Field"""
    
    def __init__(self):
        super(V6_CalculateField, self).__init__("V6_CalculateField", "vector")
        self.input_fc = None
        self.working_fc = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_fc = os.path.join(gdb_path, "calculate_field_fc")
        self.working_fc = os.path.join(settings.DATA_DIR, "V6_calculate_field.shp")
        
        # Add field if not exists
        if arcpy.Exists(self.input_fc):
            field_names = [f.name for f in arcpy.ListFields(self.input_fc)]
            if "calc_field" not in field_names:
                arcpy.AddField_management(self.input_fc, "calc_field", "DOUBLE")
    
    def teardown(self):
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
        
        # Clean up
        arcpy.Delete_management(self.working_fc)
        
        count = int(arcpy.GetCount_management(self.input_fc)[0])
        return {'features_processed': count}


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
