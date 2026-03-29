#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate test data for ArcGIS performance benchmark
Compatible with both Python 2.7 and Python 3.x
"""
from __future__ import print_function, division, absolute_import
import os
import sys
import time
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arcpy
from config import settings


class TestDataGenerator(object):
    """Generate test data for performance benchmarks"""
    
    def __init__(self):
        self.data_dir = settings.DATA_DIR
        self.gdb_name = settings.DEFAULT_GDB_NAME
        self.gdb_path = os.path.join(self.data_dir, self.gdb_name)
        self.spatial_ref = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
        self.vector_config = settings.VECTOR_CONFIG
        self.raster_config = settings.RASTER_CONFIG
        
        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _safe_delete_gdb(self, gdb_path):
        """Safely delete geodatabase with retry logic"""
        if not arcpy.Exists(gdb_path):
            return True
        
        print("[准备] 删除现有数据库...")
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                arcpy.Delete_management(gdb_path)
                time.sleep(0.5)
                if not arcpy.Exists(gdb_path):
                    return True
            except Exception as e:
                print("  警告: 删除尝试 {} 失败: {}".format(attempt + 1, str(e)[:50]))
                time.sleep(1)
        
        # Try shutil as fallback
        try:
            shutil.rmtree(gdb_path, ignore_errors=True)
            time.sleep(0.5)
            if not os.path.exists(gdb_path):
                return True
        except:
            pass
        
        return False
    
    def setup_workspace(self):
        """Create file geodatabase"""
        print("\n" + "=" * 60)
        print("Setting up workspace")
        print("=" * 60)
        
        # Delete existing if present
        self._safe_delete_gdb(self.gdb_path)
        
        # If still exists, use timestamped name
        if os.path.exists(self.gdb_path):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.gdb_name = 'benchmark_data_{}.gdb'.format(timestamp)
            self.gdb_path = os.path.join(self.data_dir, self.gdb_name)
            print("使用新数据库名: {}".format(self.gdb_name))
        
        # Create new geodatabase
        arcpy.CreateFileGDB_management(self.data_dir, self.gdb_name)
        arcpy.env.workspace = self.gdb_path
        arcpy.env.overwriteOutput = True
        
        print("Created: {}".format(self.gdb_path))
        return self.gdb_path
    
    def create_fishnet(self):
        """V1: Create fishnet polygon"""
        print("\n[1/7] Creating fishnet...")
        rows = self.vector_config['fishnet_rows']
        cols = self.vector_config['fishnet_cols']
        
        origin = "0 0"
        yaxis = "0 1"
        corner = "{} {}".format(cols * 10, rows * 10)
        cell = "10 10"
        
        arcpy.CreateFishnet_management(
            out_feature_class="fishnet",
            origin_coord=origin,
            y_axis_coord=yaxis,
            cell_width=10,
            cell_height=10,
            number_rows=rows,
            number_columns=cols,
            corner_coord=corner,
            labels="NO_LABELS",
            template="#",
            geometry_type="POLYGON"
        )
        arcpy.DefineProjection_management("fishnet", self.spatial_ref)
        
        count = int(arcpy.GetCount_management("fishnet")[0])
        print("  Created: {} polygons ({}x{})".format(count, rows, cols))
        return "fishnet"
    
    def create_random_points(self):
        """V2: Create random points"""
        print("\n[2/7] Creating random points...")
        num_points = self.vector_config['random_points']
        
        # Create extent feature
        arcpy.CreateFishnet_management(
            out_feature_class="extent",
            origin_coord="0 0",
            y_axis_coord="0 1",
            cell_width=0,
            cell_height=0,
            number_rows=1,
            number_columns=1,
            corner_coord="{} {}".format(
                self.vector_config['fishnet_cols'] * 10,
                self.vector_config['fishnet_rows'] * 10
            ),
            labels="NO_LABELS",
            geometry_type="POLYGON"
        )
        arcpy.DefineProjection_management("extent", self.spatial_ref)
        
        # Create random points
        arcpy.CreateRandomPoints_management(
            out_path=self.gdb_path,
            out_name="random_points",
            constraining_feature_class="extent",
            number_of_points_or_field=num_points
        )
        
        count = int(arcpy.GetCount_management("random_points")[0])
        print("  Created: {} points".format(count))
        
        # Clean up
        arcpy.Delete_management("extent")
        return "random_points"
    
    def create_buffer_data(self):
        """V3: Create data for buffer test"""
        print("\n[3/7] Creating buffer test data...")
        num_points = self.vector_config['buffer_points']
        
        # Create points along a line pattern
        points = []
        step = int((self.vector_config['fishnet_cols'] * 10) / (num_points ** 0.5))
        if step < 1:
            step = 1
        
        rows = int(num_points ** 0.5)
        for i in range(rows):
            for j in range(rows):
                x = i * step + 5
                y = j * step + 5
                points.append((x, y))
        
        # Create point feature class
        arcpy.CreateFeatureclass_management(
            self.gdb_path,
            "buffer_points",
            "POINT",
            spatial_reference=self.spatial_ref
        )
        
        with arcpy.da.InsertCursor("buffer_points", ["SHAPE@XY"]) as cursor:
            for x, y in points[:num_points]:
                cursor.insertRow([(x, y)])
        
        count = int(arcpy.GetCount_management("buffer_points")[0])
        print("  Created: {} points".format(count))
        return "buffer_points"
    
    def create_intersect_data(self):
        """V4: Create data for intersect test"""
        print("\n[4/7] Creating intersect test data...")
        num_a = self.vector_config['intersect_features_a']
        num_b = self.vector_config['intersect_features_b']
        
        # Create grid A
        arcpy.CreateFishnet_management(
            out_feature_class="test_polygons_a",
            origin_coord="0 0",
            y_axis_coord="0 1",
            cell_width=20,
            cell_height=20,
            number_rows=int(num_a ** 0.5),
            number_columns=int(num_a ** 0.5),
            corner_coord="{} {}".format(
                int(num_a ** 0.5) * 20,
                int(num_a ** 0.5) * 20
            ),
            labels="NO_LABELS",
            geometry_type="POLYGON"
        )
        arcpy.DefineProjection_management("test_polygons_a", self.spatial_ref)
        arcpy.AddField_management("test_polygons_a", "poly_id", "LONG")
        desc_a = arcpy.Describe("test_polygons_a")
        with arcpy.da.UpdateCursor("test_polygons_a", [desc_a.OIDFieldName, "poly_id"]) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        
        # Create offset grid B
        arcpy.CreateFishnet_management(
            out_feature_class="test_polygons_b",
            origin_coord="10 10",
            y_axis_coord="10 11",
            cell_width=20,
            cell_height=20,
            number_rows=int(num_b ** 0.5),
            number_columns=int(num_b ** 0.5),
            corner_coord="{} {}".format(
                int(num_b ** 0.5) * 20 + 10,
                int(num_b ** 0.5) * 20 + 10
            ),
            labels="NO_LABELS",
            geometry_type="POLYGON"
        )
        arcpy.DefineProjection_management("test_polygons_b", self.spatial_ref)
        
        count_a = int(arcpy.GetCount_management("test_polygons_a")[0])
        count_b = int(arcpy.GetCount_management("test_polygons_b")[0])
        print("  Created: A={} polygons, B={} polygons".format(count_a, count_b))
        return "test_polygons_a", "test_polygons_b"
    
    def create_spatial_join_data(self):
        """V5: Create data for spatial join"""
        print("\n[5/7] Creating spatial join test data...")
        num_points = self.vector_config['spatial_join_points']
        num_polys = self.vector_config['spatial_join_polygons']
        
        # Create random points
        extent_size = min(
            self.vector_config['fishnet_cols'] * 10,
            self.vector_config['fishnet_rows'] * 10
        )
        
        arcpy.CreateFeatureclass_management(
            self.gdb_path,
            "spatial_join_points",
            "POINT",
            spatial_reference=self.spatial_ref
        )
        
        import random
        random.seed(42)
        with arcpy.da.InsertCursor("spatial_join_points", ["SHAPE@XY"]) as cursor:
            for _ in range(num_points):
                x = random.uniform(0, extent_size)
                y = random.uniform(0, extent_size)
                cursor.insertRow([(x, y)])
        
        # Create grid polygons
        grid_size = int(num_polys ** 0.5)
        cell_size = extent_size / grid_size
        arcpy.CreateFishnet_management(
            out_feature_class="spatial_join_polygons",
            origin_coord="0 0",
            y_axis_coord="0 1",
            cell_width=cell_size,
            cell_height=cell_size,
            number_rows=grid_size,
            number_columns=grid_size,
            corner_coord="{} {}".format(extent_size, extent_size),
            labels="NO_LABELS",
            geometry_type="POLYGON"
        )
        arcpy.DefineProjection_management("spatial_join_polygons", self.spatial_ref)
        
        # Add attribute field
        arcpy.AddField_management("spatial_join_polygons", "poly_id", "LONG")
        # Get OID field name (may vary between ArcGIS versions)
        desc = arcpy.Describe("spatial_join_polygons")
        oid_field = desc.OIDFieldName
        with arcpy.da.UpdateCursor("spatial_join_polygons", [oid_field, "poly_id"]) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        
        count_p = int(arcpy.GetCount_management("spatial_join_points")[0])
        count_poly = int(arcpy.GetCount_management("spatial_join_polygons")[0])
        print("  Created: {} points, {} polygons".format(count_p, count_poly))
        return "sj_points", "sj_polygons"
    
    def create_calculate_field_data(self):
        """V6: Create data for calculate field test"""
        print("\n[6/7] Creating calculate field test data...")
        num_records = self.vector_config['calculate_field_records']
        
        # Create feature class for calculate field test (benchmark needs polygon feature class with poly_id)
        arcpy.CreateFeatureclass_management(
            self.gdb_path,
            "calculate_field_fc",
            "POLYGON",
            spatial_reference=self.spatial_ref
        )
        # Add required fields
        arcpy.AddField_management("calculate_field_fc", "poly_id", "LONG")
        arcpy.AddField_management("calculate_field_fc", "calc_field", "DOUBLE")
        
        # Create simple polygons
        grid_size = int(num_records ** 0.5)
        cell_size = 10
        with arcpy.da.InsertCursor("calculate_field_fc", ["SHAPE@", "poly_id", "calc_field"]) as cursor:
            poly_id = 1
            for i in range(grid_size):
                for j in range(grid_size):
                    if poly_id > num_records:
                        break
                    # Create a simple square polygon
                    array = arcpy.Array([
                        arcpy.Point(i * cell_size, j * cell_size),
                        arcpy.Point((i + 1) * cell_size, j * cell_size),
                        arcpy.Point((i + 1) * cell_size, (j + 1) * cell_size),
                        arcpy.Point(i * cell_size, (j + 1) * cell_size),
                        arcpy.Point(i * cell_size, j * cell_size)
                    ])
                    polygon = arcpy.Polygon(array)
                    cursor.insertRow([polygon, poly_id, 0])
                    poly_id += 1
                if poly_id > num_records:
                    break
        
        count = int(arcpy.GetCount_management("calculate_field_fc")[0])
        print("  Created: {} records".format(count))
        return "calc_table"
    
    def create_raster_data(self):
        """Create raster test data"""
        print("\n[7/7] Creating raster data...")
        size = self.raster_config['constant_raster_size']
        
        # Try multiple methods for creating constant raster
        raster_path = os.path.join(self.gdb_path, "constant_raster")
        
        # Method 1: arcpy.sa (ArcGIS Pro)
        try:
            import arcpy.sa
            extent = "0 0 {} {}".format(size, size)
            cell_size = 1
            out_raster = arcpy.sa.CreateConstantRaster(1, "INTEGER", cell_size, extent)
            out_raster.save(raster_path)
            print("  Created: {}x{} raster (using arcpy.sa)".format(size, size))
            return "constant_raster"
        except:
            pass
        
        # Method 2: NumPy to Raster
        try:
            import numpy as np
            arr = np.ones((size, size), dtype=np.int32)
            raster = arcpy.NumPyArrayToRaster(arr, arcpy.Point(0, 0), 1, 1)
            raster.save(raster_path)
            print("  Created: {}x{} raster (using NumPy)".format(size, size))
            return "constant_raster"
        except Exception as e:
            print("  Error creating raster: {}".format(str(e)[:50]))
            return None
    
    def generate_all(self):
        """Generate all test data"""
        print("\n" + "=" * 60)
        print("Generating Test Data")
        print("Scale: {}".format(settings.DATA_SCALE.upper()))
        print("=" * 60)
        
        try:
            # Setup
            self.setup_workspace()
            
            # Generate vector data
            self.create_fishnet()
            self.create_random_points()
            self.create_buffer_data()
            self.create_intersect_data()
            self.create_spatial_join_data()
            self.create_calculate_field_data()
            
            # Generate raster data
            self.create_raster_data()
            
            print("\n" + "=" * 60)
            print("Test data generation complete!")
            print("Location: {}".format(self.gdb_path))
            print("=" * 60)
            return True
            
        except Exception as e:
            print("\n[ERROR] Failed to generate test data:")
            print("  {}".format(str(e)))
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    generator = TestDataGenerator()
    success = generator.generate_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
