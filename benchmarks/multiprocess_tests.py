# -*- coding: utf-8 -*-
"""
Multiprocess benchmark tests - Simplified and Robust Version
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import tempfile
import shutil
import time

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
from utils.timer import ProgressHeartbeat
from utils.raster_utils import create_constant_raster


class MultiprocessBenchmark(BaseBenchmark):
    """Base class for multiprocess benchmarks"""
    
    def __init__(self, name, category="general"):
        super(MultiprocessBenchmark, self).__init__(name, category)
        self.num_workers = settings.get_multiprocess_workers() if hasattr(settings, 'get_multiprocess_workers') else 4
    
    def run(self, num_runs=None, warmup_runs=None, use_multiprocess=False):
        """Run benchmark with optional multiprocessing"""
        if num_runs is None:
            num_runs = settings.TEST_RUNS
        if warmup_runs is None:
            warmup_runs = settings.WARMUP_RUNS
        
        py_version = "Py%d.%d" % (sys.version_info[0], sys.version_info[1])
        
        if use_multiprocess:
            print("\n  [%s] [多进程 %d进程] 初始化测试: %s" % (py_version, self.num_workers, self.name))
        else:
            print("\n  [%s] 初始化测试: %s" % (py_version, self.name))
        
        print("  类别: %s" % self.category)
        
        # Setup
        print("  执行 setup()...")
        with ProgressHeartbeat("{} setup()".format(self.name)):
            self.setup()
        print("  [OK] setup() 完成")
        
        try:
            # Warmup runs
            if warmup_runs > 0:
                print("  预热运行 (%d 次)..." % warmup_runs)
                for i in range(warmup_runs):
                    result = self._run_single_iteration(
                        use_multiprocess=False,
                        progress_label="预热 %d/%d" % (i + 1, warmup_runs)
                    )
                    self.warmup_results.append(result)
            
            # Actual benchmark runs
            print("  正式测试运行 (%d 次)..." % num_runs)
            for i in range(num_runs):
                print("    运行 %d/%d..." % (i + 1, num_runs))
                mode_label = "多进程" if use_multiprocess else "单进程"
                result = self._run_single_iteration(
                    use_multiprocess=use_multiprocess,
                    progress_label="正式 %d/%d (%s)" % (i + 1, num_runs, mode_label)
                )
                self.results.append(result)
                
                if result.get('success'):
                    elapsed = result.get('elapsed_seconds', 0)
                    mode = result.get('mode', 'single')
                    print("      [OK] 耗时: %.4f秒 [%s]" % (elapsed, mode))
                else:
                    print("      [FAILED] %s" % result.get('error', 'Unknown error'))
        
        finally:
            # Teardown
            print("  执行 teardown()...")
            with ProgressHeartbeat("{} teardown()".format(self.name)):
                self.teardown()
            print("  [OK] teardown() 完成")
        
        return self.get_statistics()
    
    def _run_single_iteration(self, use_multiprocess=False, progress_label=None):
        """Run a single iteration"""
        from utils.timer import BenchmarkTimer

        heartbeat_label = self.name
        if progress_label:
            heartbeat_label = "%s - %s" % (self.name, progress_label)

        with BenchmarkTimer(name=self.name, monitor_memory=settings.ENABLE_MEMORY_MONITORING) as bt:
            with ProgressHeartbeat(heartbeat_label):
                try:
                    if use_multiprocess:
                        result = self.run_multiprocess(self.num_workers)
                    else:
                        result = self.run_single()
                    result['success'] = True
                except Exception as e:
                    import traceback
                    result = {
                        'success': False,
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    }
        
        timing_results = bt.get_results()
        result.update(timing_results)
        return result
    
    def run_single(self):
        raise NotImplementedError("Subclasses must implement run_single()")
    
    def run_multiprocess(self, num_workers):
        raise NotImplementedError("Subclasses must implement run_multiprocess()")


class MP_V1_CreateFishnet(MultiprocessBenchmark):
    """Multiprocess benchmark: Create Fishnet"""
    
    def __init__(self):
        super(MP_V1_CreateFishnet, self).__init__("MP_V1_CreateFishnet", "vector_multiprocess")
        self.rows = settings.VECTOR_CONFIG['fishnet_rows']
        self.cols = settings.VECTOR_CONFIG['fishnet_cols']
        self.output_fc = None
        self.temp_dir = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        self.output_fc = os.path.join(settings.DATA_DIR, "MP_V1_fishnet_output.shp")
        self.temp_dir = tempfile.mkdtemp(prefix="mp_fishnet_")
    
    def teardown(self):
        """Clean up all temporary files and directories"""
        # Clean up output feature class
        if self.output_fc and arcpy.Exists(self.output_fc):
            try:
                arcpy.Delete_management(self.output_fc)
            except Exception:
                pass
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Also clean up any orphaned temp directories from previous runs
        try:
            import tempfile
            temp_root = tempfile.gettempdir()
            for item in os.listdir(temp_root):
                if item.startswith('mp_fishnet_'):
                    try:
                        item_path = os.path.join(temp_root, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except:
                        pass
        except:
            pass
    
    def __del__(self):
        """Ensure cleanup even if test crashes"""
        try:
            self.teardown()
        except:
            pass
    
    def run_single(self):
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
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
        
        sr = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
        arcpy.DefineProjection_management(self.output_fc, sr)
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count, 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # Sequential execution for stability
        rows_per_worker = self.rows // num_workers
        remainder = self.rows % num_workers
        
        partition_outputs = []
        row_start = 0
        
        for worker_id in range(num_workers):
            extra = 1 if worker_id < remainder else 0
            row_count = rows_per_worker + extra
            row_end = row_start + row_count
            
            output_path = os.path.join(self.temp_dir, "fishnet_w%d.shp" % worker_id)
            
            try:
                self._create_partition(row_start, row_end, output_path)
                partition_outputs.append(output_path)
            except Exception as e:
                print("    Worker %d failed: %s" % (worker_id, str(e)[:50]))
            
            row_start = row_end
        
        if not partition_outputs:
            raise RuntimeError("All partitions failed")
        
        # Merge
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        arcpy.Merge_management(partition_outputs, self.output_fc)
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {
            'features_created': count,
            'mode': 'multiprocess',
            'workers': num_workers,
            'partitions': len(partition_outputs)
        }
    
    def _create_partition(self, row_start, row_end, output_path):
        """Create a single partition"""
        total_width = 360.0
        total_height = 180.0
        cell_width = total_width / self.cols
        cell_height = total_height / self.rows
        
        origin_y = 90 - (row_start * cell_height)
        corner_y = 90 - (row_end * cell_height)
        num_rows = row_end - row_start
        
        arcpy.CreateFishnet_management(
            out_feature_class=output_path,
            origin_coord="-180 %f" % origin_y,
            y_axis_coord="-180 %f" % (origin_y + 10),
            cell_width=cell_width,
            cell_height=cell_height,
            number_rows=num_rows,
            number_columns=self.cols,
            corner_coord="180 %f" % corner_y,
            labels="NO_LABELS",
            template="",
            geometry_type="POLYGON"
        )
        
        sr = arcpy.SpatialReference(settings.SPATIAL_REFERENCE)
        arcpy.DefineProjection_management(output_path, sr)


def get_oid_field(fc):
    """Get the OID field name for a feature class (OID@ or OBJECTID)"""
    try:
        # Try to get from describe
        desc = arcpy.Describe(fc)
        if hasattr(desc, 'OIDFieldName'):
            return desc.OIDFieldName
    except:
        pass
    
    # Default fallback - check if OBJECTID exists
    try:
        fields = [f.name.upper() for f in arcpy.ListFields(fc)]
        if 'OBJECTID' in fields:
            return 'OBJECTID'
    except:
        pass
    
    # Final fallback
    return 'FID'


class MP_V2_CreateRandomPoints(MultiprocessBenchmark):
    """Multiprocess benchmark: Create Random Points"""
    
    def __init__(self):
        super(MP_V2_CreateRandomPoints, self).__init__("MP_V2_CreateRandomPoints", "vector_multiprocess")
        self.num_points = settings.VECTOR_CONFIG['random_points']
        self.output_fc = None
        self.temp_dir = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        self.output_fc = os.path.join(settings.DATA_DIR, "MP_V2_random_points.shp")
        self.temp_dir = tempfile.mkdtemp(prefix="mp_randpts_")
    
    def teardown(self):
        """Clean up all temporary files and directories"""
        if self.output_fc and arcpy.Exists(self.output_fc):
            try:
                arcpy.Delete_management(self.output_fc)
            except Exception:
                pass
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Clean up orphaned temp directories
        try:
            import tempfile
            temp_root = tempfile.gettempdir()
            for item in os.listdir(temp_root):
                if item.startswith('mp_randpts_'):
                    try:
                        item_path = os.path.join(temp_root, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except:
                        pass
        except:
            pass
    
    def __del__(self):
        """Ensure cleanup even if test crashes"""
        try:
            self.teardown()
        except:
            pass
    
    def run_single(self):
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        arcpy.CreateRandomPoints_management(
            out_path=settings.DATA_DIR,
            out_name="MP_V2_random_points",
            constraining_extent="-180 -90 180 90",
            number_of_points_or_field=self.num_points,
            minimum_allowed_distance="0 DecimalDegrees"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count, 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # Divide points among workers
        points_per_worker = self.num_points // num_workers
        remainder = self.num_points % num_workers
        
        partition_outputs = []
        
        for worker_id in range(num_workers):
            extra = 1 if worker_id < remainder else 0
            num_pts = points_per_worker + extra
            
            # Divide by longitude
            lon_start = -180 + (360.0 / num_workers) * worker_id
            lon_end = -180 + (360.0 / num_workers) * (worker_id + 1)
            extent = "%f -90 %f 90" % (lon_start, lon_end)
            
            output_path = os.path.join(self.temp_dir, "randpts_w%d.shp" % worker_id)
            
            try:
                arcpy.CreateRandomPoints_management(
                    out_path=self.temp_dir,
                    out_name="randpts_w%d" % worker_id,
                    constraining_extent=extent,
                    number_of_points_or_field=num_pts,
                    minimum_allowed_distance="0 DecimalDegrees"
                )
                partition_outputs.append(output_path)
            except Exception as e:
                print("    Worker %d failed: %s" % (worker_id, str(e)[:50]))
        
        if not partition_outputs:
            raise RuntimeError("All partitions failed")
        
        # Merge
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        arcpy.Merge_management(partition_outputs, self.output_fc)
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {
            'features_created': count,
            'mode': 'multiprocess',
            'workers': num_workers
        }


class MP_V3_Buffer(MultiprocessBenchmark):
    """Multiprocess benchmark: Buffer Analysis"""
    
    def __init__(self):
        super(MP_V3_Buffer, self).__init__("MP_V3_Buffer", "vector_multiprocess")
        self.input_fc = None
        self.output_fc = None
        self.temp_dir = None
        self.buffer_distance = "1 Kilometer"
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_fc = os.path.join(gdb_path, "buffer_points")
        self.output_fc = os.path.join(settings.DATA_DIR, "MP_V3_buffer_output.shp")
        self.temp_dir = tempfile.mkdtemp(prefix="mp_buffer_")
    
    def teardown(self):
        """Clean up all temporary files and directories"""
        if self.output_fc and arcpy.Exists(self.output_fc):
            try:
                arcpy.Delete_management(self.output_fc)
            except Exception:
                pass
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Clean up orphaned temp directories
        try:
            import tempfile
            temp_root = tempfile.gettempdir()
            for item in os.listdir(temp_root):
                if item.startswith('mp_buffer_'):
                    try:
                        item_path = os.path.join(temp_root, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except:
                        pass
        except:
            pass
    
    def __del__(self):
        """Ensure cleanup even if test crashes"""
        try:
            self.teardown()
        except:
            pass
    
    def run_single(self):
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        arcpy.Buffer_analysis(
            in_features=self.input_fc,
            out_feature_class=self.output_fc,
            buffer_distance_or_field=self.buffer_distance,
            line_side="FULL",
            line_end_type="ROUND",
            dissolve_option="NONE"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count, 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # Get count and divide
        total_count = int(arcpy.GetCount_management(self.input_fc)[0])
        count_per_worker = total_count // num_workers
        remainder = total_count % num_workers
        
        partition_outputs = []
        oid_start = 1
        oid_field = get_oid_field(self.input_fc)
        
        for worker_id in range(num_workers):
            extra = 1 if worker_id < remainder else 0
            oid_count = count_per_worker + extra
            oid_end = oid_start + oid_count - 1
            
            output_path = os.path.join(self.temp_dir, "buffer_w%d.shp" % worker_id)
            
            try:
                # Select by OID using correct field name
                where_clause = "%s >= %d AND %s <= %d" % (oid_field, oid_start, oid_field, oid_end)
                temp_layer = "buf_lyr_%d" % worker_id
                arcpy.MakeFeatureLayer_management(self.input_fc, temp_layer, where_clause)
                
                arcpy.Buffer_analysis(
                    in_features=temp_layer,
                    out_feature_class=output_path,
                    buffer_distance_or_field=self.buffer_distance,
                    line_side="FULL",
                    line_end_type="ROUND",
                    dissolve_option="NONE"
                )
                
                arcpy.Delete_management(temp_layer)
                partition_outputs.append(output_path)
            except Exception as e:
                print("    Worker %d failed: %s" % (worker_id, str(e)[:50]))
            
            oid_start = oid_end + 1
        
        if not partition_outputs:
            raise RuntimeError("All partitions failed")
        
        # Merge
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        arcpy.Merge_management(partition_outputs, self.output_fc)
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {
            'features_created': count,
            'mode': 'multiprocess',
            'workers': num_workers
        }


class MP_V4_Intersect(MultiprocessBenchmark):
    """Multiprocess benchmark: Intersect Analysis"""
    
    def __init__(self):
        super(MP_V4_Intersect, self).__init__("MP_V4_Intersect", "vector_multiprocess")
        self.input_a = None
        self.input_b = None
        self.output_fc = None
        self.temp_dir = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        gdb_path = os.path.join(settings.DATA_DIR, settings.DEFAULT_GDB_NAME)
        self.input_a = os.path.join(gdb_path, "test_polygons_a")
        self.input_b = os.path.join(gdb_path, "test_polygons_b")
        self.output_fc = os.path.join(settings.DATA_DIR, "MP_V4_intersect_output.shp")
        self.temp_dir = tempfile.mkdtemp(prefix="mp_intersect_")
    
    def teardown(self):
        """Clean up all temporary files and directories"""
        if self.output_fc and arcpy.Exists(self.output_fc):
            try:
                arcpy.Delete_management(self.output_fc)
            except Exception:
                pass
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Clean up orphaned temp directories
        try:
            import tempfile
            temp_root = tempfile.gettempdir()
            for item in os.listdir(temp_root):
                if item.startswith('mp_intersect_'):
                    try:
                        item_path = os.path.join(temp_root, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except:
                        pass
        except:
            pass
    
    def __del__(self):
        """Ensure cleanup even if test crashes"""
        try:
            self.teardown()
        except:
            pass
    
    def run_single(self):
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        arcpy.Intersect_analysis(
            in_features=[self.input_a, self.input_b],
            out_feature_class=self.output_fc,
            join_attributes="ALL",
            output_type="INPUT"
        )
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {'features_created': count, 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # For intersect, we divide input A by OID and intersect each part with B
        total_count = int(arcpy.GetCount_management(self.input_a)[0])
        count_per_worker = total_count // num_workers
        remainder = total_count % num_workers
        
        partition_outputs = []
        oid_start = 1
        oid_field = get_oid_field(self.input_a)
        
        for worker_id in range(num_workers):
            extra = 1 if worker_id < remainder else 0
            oid_count = count_per_worker + extra
            oid_end = oid_start + oid_count - 1
            
            output_path = os.path.join(self.temp_dir, "intersect_w%d.shp" % worker_id)
            
            try:
                # Select subset of A using correct OID field
                where_clause = "%s >= %d AND %s <= %d" % (oid_field, oid_start, oid_field, oid_end)
                temp_a = os.path.join(self.temp_dir, "temp_a_%d.shp" % worker_id)
                
                arcpy.Select_analysis(self.input_a, temp_a, where_clause)
                
                arcpy.Intersect_analysis(
                    in_features=[temp_a, self.input_b],
                    out_feature_class=output_path,
                    join_attributes="ALL",
                    output_type="INPUT"
                )
                
                arcpy.Delete_management(temp_a)
                partition_outputs.append(output_path)
            except Exception as e:
                print("    Worker %d failed: %s" % (worker_id, str(e)[:50]))
            
            oid_start = oid_end + 1
        
        if not partition_outputs:
            raise RuntimeError("All partitions failed")
        
        # Merge
        if arcpy.Exists(self.output_fc):
            arcpy.Delete_management(self.output_fc)
        
        arcpy.Merge_management(partition_outputs, self.output_fc)
        
        count = int(arcpy.GetCount_management(self.output_fc)[0])
        return {
            'features_created': count,
            'mode': 'multiprocess',
            'workers': num_workers
        }


class MP_R1_CreateConstantRaster(MultiprocessBenchmark):
    """Multiprocess benchmark: Create Constant Raster"""
    
    def __init__(self):
        super(MP_R1_CreateConstantRaster, self).__init__("MP_R1_CreateConstantRaster", "raster_multiprocess")
        self.size = settings.RASTER_CONFIG['constant_raster_size']
        self.output_raster = None
        self.temp_dir = None
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
        self.output_raster = os.path.join(settings.DATA_DIR, "MP_R1_constant_raster.tif")
        self.temp_dir = tempfile.mkdtemp(prefix="mp_raster_")
    
    def teardown(self):
        """Clean up all temporary files and directories"""
        if self.output_raster and arcpy.Exists(self.output_raster):
            try:
                arcpy.Delete_management(self.output_raster)
            except Exception:
                pass
        
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Clean up orphaned temp directories
        try:
            import tempfile
            temp_root = tempfile.gettempdir()
            for item in os.listdir(temp_root):
                if item.startswith('mp_raster_'):
                    try:
                        item_path = os.path.join(temp_root, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                    except:
                        pass
        except:
            pass
    
    def __del__(self):
        """Ensure cleanup even if test crashes"""
        try:
            self.teardown()
        except:
            pass
    
    def run_single(self):
        if arcpy.Exists(self.output_raster):
            arcpy.Delete_management(self.output_raster)
        
        cell_size = 360.0 / self.size
        extent = "-180 -90 180 90"
        create_constant_raster(self.output_raster, cell_size, extent, value=1, use_spatial_analyst=False)
        
        return {'raster_created': self.output_raster, 'mode': 'single'}
    
    def run_multiprocess(self, num_workers):
        # Divide by rows
        rows_per_worker = self.size // num_workers
        remainder = self.size % num_workers
        cell_size = 360.0 / self.size
        
        partition_rasters = []
        row_start = 0
        
        for worker_id in range(num_workers):
            extra = 1 if worker_id < remainder else 0
            row_count = rows_per_worker + extra
            row_end = row_start + row_count
            
            # Calculate extent
            y_start = 90 - (row_start * cell_size)
            y_end = 90 - (row_end * cell_size)
            extent = "-180 %f 180 %f" % (y_end, y_start)
            
            output_path = os.path.join(self.temp_dir, "raster_w%d.tif" % worker_id)
            
            try:
                create_constant_raster(output_path, cell_size, extent, value=1, use_spatial_analyst=False)
                partition_rasters.append(output_path)
            except Exception as e:
                print("    Worker %d failed: %s" % (worker_id, str(e)[:50]))
            
            row_start = row_end
        
        if not partition_rasters:
            raise RuntimeError("All partitions failed")
        
        # Mosaic
        if arcpy.Exists(self.output_raster):
            arcpy.Delete_management(self.output_raster)
        
        arcpy.MosaicToNewRaster_management(
            input_rasters=";".join(partition_rasters),
            output_location=os.path.dirname(self.output_raster),
            raster_dataset_name_with_extension=os.path.basename(self.output_raster),
            pixel_type="8_BIT_UNSIGNED",
            cellsize=cell_size,
            number_of_bands=1
        )
        
        return {
            'raster_created': self.output_raster,
            'mode': 'multiprocess',
            'workers': num_workers
        }


def get_multiprocess_benchmarks():
    """Get all multiprocess benchmark instances"""
    if not HAS_ARCPY:
        return []
    return [
        MP_V1_CreateFishnet(),
        MP_V2_CreateRandomPoints(),
        MP_V3_Buffer(),
        MP_V4_Intersect(),
        MP_R1_CreateConstantRaster(),
    ]


if __name__ == '__main__':
    print("Multiprocess benchmarks loaded")
