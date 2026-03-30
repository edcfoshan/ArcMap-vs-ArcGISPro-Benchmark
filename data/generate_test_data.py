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
    
    def check_existing_data(self):
        """Check if existing data matches current scale requirements"""
        if not arcpy.Exists(self.gdb_path):
            print("  数据库不存在，需要生成")
            return False
        
        print("  发现现有数据库，检查数据完整性...")
        arcpy.env.workspace = self.gdb_path
        
        # Define expected datasets and their expected counts
        checks = [
            ("fishnet", "polygon", self.vector_config['fishnet_rows'] * self.vector_config['fishnet_cols']),
            ("random_points", "point", self.vector_config['random_points']),
            ("buffer_points", "point", int(self.vector_config['buffer_points'] ** 0.5) ** 2),  # Grid layout
            ("test_polygons_a", "polygon", int(self.vector_config['intersect_features_a'] ** 0.5) ** 2),
            ("test_polygons_b", "polygon", int(self.vector_config['intersect_features_b'] ** 0.5) ** 2),
            ("spatial_join_points", "point", self.vector_config['spatial_join_points']),
            ("spatial_join_polygons", "polygon", self.vector_config['fishnet_rows'] * self.vector_config['fishnet_cols']),
            ("calculate_field_fc", "polygon", self.vector_config['calculate_field_records']),
        ]
        
        all_valid = True
        for dataset_name, expected_type, expected_count in checks:
            try:
                if not arcpy.Exists(dataset_name):
                    print("    [缺失] {}".format(dataset_name))
                    all_valid = False
                    continue
                
                # Check feature count (with 10% tolerance)
                actual_count = int(arcpy.GetCount_management(dataset_name)[0])
                tolerance = max(1, expected_count * 0.1)
                
                if abs(actual_count - expected_count) <= tolerance:
                    print("    [OK] {}: {} {} (符合要求)".format(dataset_name, actual_count, expected_type))
                else:
                    print("    [不符] {}: {} vs 期望 {}".format(dataset_name, actual_count, expected_count))
                    all_valid = False
                    
            except Exception as e:
                print("    [错误] {}: {}".format(dataset_name, str(e)[:50]))
                all_valid = False
        
        # Check raster
        try:
            if arcpy.Exists("constant_raster"):
                desc = arcpy.Describe("constant_raster")
                expected_size = self.raster_config['constant_raster_size']
                if desc.width == expected_size and desc.height == expected_size:
                    print("    [OK] constant_raster: {}x{} (符合要求)".format(desc.width, desc.height))
                else:
                    print("    [不符] constant_raster: {}x{} vs 期望 {}x{}".format(
                        desc.width, desc.height, expected_size, expected_size))
                    all_valid = False
            else:
                print("    [缺失] constant_raster")
                all_valid = False
        except Exception as e:
            print("    [错误] constant_raster: {}".format(str(e)[:50]))
            all_valid = False
        
        if all_valid:
            print("  [OK] 现有数据完整，跳过生成步骤")
        else:
            print("  [需要] 数据不完整或规模不符，将重新生成")
        
        return all_valid
    
    def setup_workspace(self):
        """Create file geodatabase"""
        print("\n" + "=" * 60)
        print("[步骤 1/8] 准备工作空间")
        print("=" * 60)
        print("  数据目录: {}".format(self.data_dir))
        print("  数据库名: {}".format(self.gdb_name))
        print("  空间参考: WGS84 (EPSG:4326)")
        
        # Delete existing if present
        print("  检查并清理旧数据库...")
        self._safe_delete_gdb(self.gdb_path)
        
        # If still exists, use timestamped name
        if os.path.exists(self.gdb_path):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.gdb_name = 'benchmark_data_{}.gdb'.format(timestamp)
            self.gdb_path = os.path.join(self.data_dir, self.gdb_name)
            print("使用新数据库名: {}".format(self.gdb_name))
        
        # Create new geodatabase
        print("  创建文件地理数据库...")
        arcpy.CreateFileGDB_management(self.data_dir, self.gdb_name)
        arcpy.env.workspace = self.gdb_path
        arcpy.env.overwriteOutput = True
        
        print("  [OK] 数据库创建成功: {}".format(self.gdb_path))
        return self.gdb_path
    
    def create_fishnet(self):
        """V1: Create fishnet polygon"""
        print("\n[步骤 2/8] 创建渔网多边形 (V1)")
        print("-" * 60)
        rows = self.vector_config['fishnet_rows']
        cols = self.vector_config['fishnet_cols']
        print("  参数: {} 行 x {} 列".format(rows, cols))
        print("  预计生成: {} 个多边形".format(rows * cols))
        print("  正在执行 CreateFishnet_management...")
        
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
        print("  定义投影...")
        arcpy.DefineProjection_management("fishnet", self.spatial_ref)
        
        count = int(arcpy.GetCount_management("fishnet")[0])
        print("  [OK] 完成: {} 个多边形 ({}x{})".format(count, rows, cols))
        return "fishnet"
    
    def create_random_points(self):
        """V2: Create random points"""
        print("\n[步骤 3/8] 生成随机点 (V2)")
        print("-" * 60)
        num_points = self.vector_config['random_points']
        print("  参数: {} 个随机点".format(num_points))
        print("  正在创建范围要素类...")
        
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
        print("  正在生成随机点 (这可能需要一些时间)...")
        arcpy.CreateRandomPoints_management(
            out_path=self.gdb_path,
            out_name="random_points",
            constraining_feature_class="extent",
            number_of_points_or_field=num_points
        )
        
        count = int(arcpy.GetCount_management("random_points")[0])
        print("  [OK] 完成: {} 个点".format(count))
        
        # Clean up
        print("  清理临时数据...")
        arcpy.Delete_management("extent")
        print("  [OK] 临时数据已清理")
        return "random_points"
    
    def create_buffer_data(self):
        """V3: Create data for buffer test"""
        print("\n[步骤 4/8] 创建缓冲区测试数据 (V3)")
        print("-" * 60)
        num_points = self.vector_config['buffer_points']
        print("  参数: {} 个点要素".format(num_points))
        print("  计算网格布局...")
        
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
        print("  创建点要素类...")
        arcpy.CreateFeatureclass_management(
            self.gdb_path,
            "buffer_points",
            "POINT",
            spatial_reference=self.spatial_ref
        )
        
        print("  正在插入 {} 个点...".format(num_points))
        batch_size = max(1, num_points // 10)
        inserted = 0
        with arcpy.da.InsertCursor("buffer_points", ["SHAPE@XY"]) as cursor:
            for x, y in points[:num_points]:
                cursor.insertRow([(x, y)])
                inserted += 1
                if inserted % batch_size == 0:
                    progress = int(inserted * 100 / num_points)
                    print("    进度: {}/{} ({}%)".format(inserted, num_points, progress))
        
        count = int(arcpy.GetCount_management("buffer_points")[0])
        print("  [OK] 完成: {} 个点".format(count))
        return "buffer_points"
    
    def create_intersect_data(self):
        """V4: Create data for intersect test"""
        print("\n[步骤 5/8] 创建叠加分析测试数据 (V4)")
        print("-" * 60)
        num_a = self.vector_config['intersect_features_a']
        num_b = self.vector_config['intersect_features_b']
        print("  参数: 图层A={} 个多边形, 图层B={} 个多边形".format(num_a, num_b))
        
        # Create grid A
        rows_a = int(num_a ** 0.5)
        cols_a = int(num_a ** 0.5)
        print("  创建图层A (渔网 {}x{})...".format(rows_a, cols_a))
        arcpy.CreateFishnet_management(
            out_feature_class="test_polygons_a",
            origin_coord="0 0",
            y_axis_coord="0 1",
            cell_width=20,
            cell_height=20,
            number_rows=rows_a,
            number_columns=cols_a,
            corner_coord="{} {}".format(
                rows_a * 20,
                cols_a * 20
            ),
            labels="NO_LABELS",
            geometry_type="POLYGON"
        )
        print("  定义投影并添加字段...")
        arcpy.DefineProjection_management("test_polygons_a", self.spatial_ref)
        arcpy.AddField_management("test_polygons_a", "poly_id", "LONG")
        # Use CalculateField instead of cursor for better performance
        try:
            desc_a = arcpy.Describe("test_polygons_a")
            arcpy.CalculateField_management("test_polygons_a", "poly_id", "!{}!".format(desc_a.OIDFieldName), "PYTHON3")
            print("    poly_id 字段填充完成")
        except:
            # Fallback to cursor for compatibility
            desc_a = arcpy.Describe("test_polygons_a")
            with arcpy.da.UpdateCursor("test_polygons_a", [desc_a.OIDFieldName, "poly_id"]) as cursor:
                for row in cursor:
                    row[1] = row[0]
                    cursor.updateRow(row)
        
        # Create offset grid B
        rows_b = int(num_b ** 0.5)
        cols_b = int(num_b ** 0.5)
        print("  创建图层B (偏移渔网 {}x{})...".format(rows_b, cols_b))
        arcpy.CreateFishnet_management(
            out_feature_class="test_polygons_b",
            origin_coord="10 10",
            y_axis_coord="10 11",
            cell_width=20,
            cell_height=20,
            number_rows=rows_b,
            number_columns=cols_b,
            corner_coord="{} {}".format(
                rows_b * 20 + 10,
                cols_b * 20 + 10
            ),
            labels="NO_LABELS",
            geometry_type="POLYGON"
        )
        print("  定义投影...")
        arcpy.DefineProjection_management("test_polygons_b", self.spatial_ref)
        
        count_a = int(arcpy.GetCount_management("test_polygons_a")[0])
        count_b = int(arcpy.GetCount_management("test_polygons_b")[0])
        print("  [OK] 完成: A={} 个多边形, B={} 个多边形".format(count_a, count_b))
        return "test_polygons_a", "test_polygons_b"
    
    def create_spatial_join_data(self):
        """V5: Create data for spatial join"""
        print("\n[步骤 6/8] 创建空间连接测试数据 (V5)")
        print("-" * 60)
        num_points = self.vector_config['spatial_join_points']
        num_polygons = self.vector_config.get('spatial_join_polygons', 10000)
        print("  参数: {} 个点要素, {} 个多边形".format(num_points, num_polygons))
        
        # Create a smaller grid for spatial join instead of copying full fishnet
        # This avoids the slow update cursor on millions of records
        print("  创建独立的多边形网格 ({} 个)...".format(num_polygons))
        grid_rows = int(num_polygons ** 0.5)
        grid_cols = int(num_polygons ** 0.5)
        
        arcpy.CreateFishnet_management(
            out_feature_class="spatial_join_polygons",
            origin_coord="0 0",
            y_axis_coord="0 1",
            cell_width=10,
            cell_height=10,
            number_rows=grid_rows,
            number_columns=grid_cols,
            corner_coord="{} {}".format(grid_cols * 10, grid_rows * 10),
            labels="NO_LABELS",
            geometry_type="POLYGON"
        )
        arcpy.DefineProjection_management("spatial_join_polygons", self.spatial_ref)
        
        # Add poly_id field using CalculateField (much faster than cursor)
        print("  添加并填充 poly_id 字段...")
        arcpy.AddField_management("spatial_join_polygons", "poly_id", "LONG")
        # Use OID as poly_id - much faster than cursor update
        desc = arcpy.Describe("spatial_join_polygons")
        oid_field = desc.OIDFieldName
        try:
            # Try using CalculateField which is much faster
            arcpy.CalculateField_management("spatial_join_polygons", "poly_id", "!{}!".format(oid_field), "PYTHON3")
            print("    使用 CalculateField 快速填充完成")
        except:
            # Fallback: use cursor for small datasets only
            updated = 0
            batch_size = max(1, num_polygons // 10)
            with arcpy.da.UpdateCursor("spatial_join_polygons", [oid_field, "poly_id"]) as cursor:
                for row in cursor:
                    row[1] = row[0]
                    cursor.updateRow(row)
                    updated += 1
                    if updated % batch_size == 0:
                        print("    已更新 {} 条记录...".format(updated))
        
        # Create random points within the polygons extent (not fishnet extent)
        # Use the same extent as spatial_join_polygons for consistency
        print("  获取多边形范围...")
        desc = arcpy.Describe("spatial_join_polygons")
        extent = desc.extent
        x_min, y_min, x_max, y_max = extent.XMin, extent.YMin, extent.XMax, extent.YMax
        print("  范围: X={:.2f}~{:.2f}, Y={:.2f}~{:.2f}".format(x_min, x_max, y_min, y_max))
        
        print("  创建点要素类...")
        arcpy.CreateFeatureclass_management(
            self.gdb_path,
            "spatial_join_points",
            "POINT",
            spatial_reference=self.spatial_ref
        )
        
        print("  正在生成 {} 个随机点...".format(num_points))
        import random
        random.seed(42)
        batch_size = max(1, num_points // 10)
        inserted = 0
        with arcpy.da.InsertCursor("spatial_join_points", ["SHAPE@XY"]) as cursor:
            for _ in range(num_points):
                x = random.uniform(x_min, x_max)
                y = random.uniform(y_min, y_max)
                cursor.insertRow([(x, y)])
                inserted += 1
                if inserted % batch_size == 0:
                    progress = int(inserted * 100 / num_points)
                    print("    进度: {}/{} ({}%)".format(inserted, num_points, progress))
        
        count_p = int(arcpy.GetCount_management(os.path.join(self.gdb_path, "spatial_join_points"))[0])
        count_poly = int(arcpy.GetCount_management(os.path.join(self.gdb_path, "spatial_join_polygons"))[0])
        print("  [OK] 完成: {} 个点, {} 个多边形".format(count_p, count_poly))
        return "spatial_join_points", "spatial_join_polygons"
    
    def create_calculate_field_data(self):
        """V6: Create data for calculate field test"""
        print("\n[步骤 7/8] 创建字段计算测试数据 (V6)")
        print("-" * 60)
        num_records = self.vector_config['calculate_field_records']
        print("  参数: {} 条记录".format(num_records))
        
        # Create feature class for calculate field test (benchmark needs polygon feature class with poly_id)
        print("  创建多边形要素类...")
        arcpy.CreateFeatureclass_management(
            self.gdb_path,
            "calculate_field_fc",
            "POLYGON",
            spatial_reference=self.spatial_ref
        )
        # Add required fields
        print("  添加字段 (poly_id, calc_field)...")
        arcpy.AddField_management("calculate_field_fc", "poly_id", "LONG")
        arcpy.AddField_management("calculate_field_fc", "calc_field", "DOUBLE")
        
        # Create simple polygons
        print("  正在创建 {} 个多边形...".format(num_records))
        grid_size = int(num_records ** 0.5)
        cell_size = 10
        batch_size = max(1, num_records // 10)
        created = 0
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
                    created += 1
                    if created % batch_size == 0:
                        progress = int(created * 100 / num_records)
                        print("    进度: {}/{} ({}%)".format(created, num_records, progress))
                if poly_id > num_records:
                    break
        
        fc_path = os.path.join(self.gdb_path, "calculate_field_fc")
        count = int(arcpy.GetCount_management(fc_path)[0])
        print("  [OK] 完成: {} 条记录".format(count))
        return "calculate_field_fc"
    
    def create_raster_data(self):
        """Create raster test data using pure arcpy"""
        print("\n[步骤 8/8] 创建栅格测试数据 (R1)")
        print("-" * 60)
        size = self.raster_config['constant_raster_size']
        print("  参数: {}x{} 像素".format(size, size))
        print("  预计大小: ~{} MB".format(int(size * size * 4 / 1024 / 1024)))
        raster_path = os.path.join(self.gdb_path, "constant_raster")
        
        # Pure arcpy method: Use Raster Calculator to create a constant raster
        # Create a simple calculation that results in all 1's
        extent = "0 0 {} {}".format(size, size)
        cell_size = 1
        
        try:
            # Method 1: Try arcpy.sa.CreateConstantRaster (Pro style)
            print("  尝试使用 arcpy.sa.CreateConstantRaster 创建...")
            out_raster = arcpy.sa.CreateConstantRaster(1, "INTEGER", cell_size, extent)
            print("  正在保存栅格...")
            out_raster.save(raster_path)
            print("  [OK] 完成: {}x{} 栅格 (使用 arcpy.sa)".format(size, size))
            return "constant_raster"
        except Exception as e1:
            print("  方法1失败: {}".format(str(e1)[:50]))
            try:
                # Method 2: Try arcpy.CreateConstantRaster_sa (Desktop style)
                print("  尝试使用 CreateConstantRaster_sa 创建...")
                arcpy.CreateConstantRaster_sa(raster_path, 1, "INTEGER", cell_size, extent)
                print("  [OK] 完成: {}x{} 栅格 (使用 CreateConstantRaster_sa)".format(size, size))
                return "constant_raster"
            except Exception as e:
                print("  [ERROR] {}".format(str(e)[:100]))
                return None
    
    def generate_all(self, force=False):
        """Generate all test data if not exists or doesn't match scale"""
        print("\n" + "=" * 60)
        print("开始检查/生成 ArcGIS 性能测试数据")
        print("=" * 60)
        print("数据规模: {}".format(settings.DATA_SCALE.upper()))
        print("Python版本: {}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))
        print("数据库路径: {}".format(self.gdb_path))
        print("=" * 60)
        
        # Check if we can reuse existing data
        if not force:
            if self.check_existing_data():
                return True
        
        # Need to generate data
        print("\n开始生成数据...")
        
        try:
            # Setup (will delete existing if present)
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
            print("[OK] 测试数据生成成功！")
            print("=" * 60)
            print("数据库位置: {}".format(self.gdb_path))
            print("包含数据:")
            print("  - 渔网多边形 (fishnet)")
            print("  - 随机点 (random_points)")
            print("  - 缓冲区测试点 (buffer_points)")
            print("  - 叠加分析多边形A/B (test_polygons_a/b)")
            print("  - 空间连接数据 (spatial_join_points/polygons)")
            print("  - 字段计算数据 (calculate_field_fc)")
            print("  - 常量栅格 (constant_raster)")
            print("=" * 60)
            return True
            
        except Exception as e:
            print("\n" + "=" * 60)
            print("[ERROR] 测试数据生成失败！")
            print("=" * 60)
            print("错误信息: {}".format(str(e)))
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='Generate test data for ArcGIS benchmark')
    parser.add_argument('--force', action='store_true', 
                        help='Force regeneration even if valid data exists')
    args = parser.parse_args()
    
    generator = TestDataGenerator()
    success = generator.generate_all(force=args.force)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
