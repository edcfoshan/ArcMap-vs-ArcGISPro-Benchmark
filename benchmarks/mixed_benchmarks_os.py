# -*- coding: utf-8 -*-
"""
Mixed (vector-raster) benchmarks using open-source libraries
Compatible with Python 3.x only
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import open-source libraries
try:
    import geopandas as gpd
    import rasterio
    from rasterio import features
    from rasterio.transform import from_bounds
    import shapely
    import pyogrio
    HAS_OS_LIBS = True
except ImportError:
    HAS_OS_LIBS = False

from config import settings
from benchmarks.base_benchmark import BaseBenchmark
from utils.benchmark_inputs import (
    get_analysis_boundary_extent,
    get_analysis_crs,
    get_analysis_raster_path,
    get_benchmark_gdb_path,
)


def _analysis_extent(default_size):
    """Return a square projected extent for raster fallback generation."""
    extent = get_analysis_boundary_extent(settings.DATA_DIR)
    if extent:
        return extent
    half = float(default_size) / 2.0
    return (-half, -half, half, half)


def _create_analysis_raster_fallback(output_path, raster_size):
    """Create a patterned raster when the generated analysis raster is missing."""
    extent = _analysis_extent(raster_size)
    width = int(raster_size)
    height = int(raster_size)
    transform = from_bounds(extent[0], extent[1], extent[2], extent[3], width, height)
    rows = np.arange(height, dtype=np.int32).reshape(-1, 1)
    cols = np.arange(width, dtype=np.int32).reshape(1, -1)
    data = ((rows // max(1, height // 8)) + (cols // max(1, width // 8))) % 8 + 1
    profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': 1,
        'dtype': data.dtype,
        'crs': 'EPSG:{}'.format(get_analysis_crs(settings.DATA_DIR)),
        'transform': transform,
        'compress': 'lzw'
    }
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data, 1)
    return output_path


class MixedBenchmarksOS(object):
    """Collection of mixed vector-raster benchmarks using open-source libraries"""

    @staticmethod
    def get_all_benchmarks():
        """Get all open-source mixed benchmark instances"""
        if not HAS_OS_LIBS:
            return []
        return [
            M1_PolygonToRaster_OS(),
            M2_RasterToPoint_OS(),
        ]


class M1_PolygonToRaster_OS(BaseBenchmark):
    """Benchmark: Polygon to Raster Conversion using Rasterio"""

    def __init__(self):
        super(M1_PolygonToRaster_OS, self).__init__("M1_PolygonToRaster_OS", "mixed_os")
        self.gdb_path = None
        self.input_layer = None
        self.output_path = None
        self.cell_size = None

    def setup(self):
        self.gdb_path = get_benchmark_gdb_path(settings.DATA_DIR)
        self.input_layer = "test_polygons_a"
        self.output_path = os.path.join(settings.DATA_DIR, "M1_poly_to_ras_os.tif")

        cfg = settings.get_raster_config_for_test('M1')
        raster_size = cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size'))
        extent = get_analysis_boundary_extent(settings.DATA_DIR)
        if extent:
            self.cell_size = max(1.0, float(extent[2] - extent[0]) / float(raster_size))
        else:
            self.cell_size = 1.0

    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass

    def run_single(self):
        # Read polygons (using layer parameter)
        gdf = gpd.read_file(self.gdb_path, layer=self.input_layer)

        # Rasterize
        cfg = settings.get_raster_config_for_test('M1')
        raster_size = cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size'))
        bounds = gdf.total_bounds
        width = float(bounds[2] - bounds[0])
        height = float(bounds[3] - bounds[1])
        scale = max(width, height) / float(raster_size)
        expected_width = int(round(width / scale))
        expected_height = int(round(height / scale))
        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], expected_width, expected_height)

        # Create shapes for rasterization (geometry, value pairs)
        shapes = ((geom, value) for geom, value in zip(gdf.geometry, gdf['poly_id']))

        # Rasterize
        result = features.rasterize(
            shapes=shapes,
            out_shape=(expected_height, expected_width),
            transform=transform,
            fill=0,
            dtype=np.int32
        )

        # Write to GeoTIFF
        profile = {
            'driver': 'GTiff',
            'height': expected_height,
            'width': expected_width,
            'count': 1,
            'dtype': result.dtype,
            'crs': 'EPSG:{}'.format(get_analysis_crs(settings.DATA_DIR)),
            'transform': transform,
            'compress': 'lzw'
        }

        with rasterio.open(self.output_path, 'w', **profile) as dst:
            dst.write(result, 1)

        filled_cells = int(np.count_nonzero(result))
        if filled_cells <= 0:
            raise RuntimeError("M1_PolygonToRaster_OS 校验失败: 输出栅格没有有效像元")

        return {
            'output_width': expected_width,
            'output_height': expected_height,
            'validation_metric': 'polygon_to_raster_dimensions',
            'validation_expected': "{}x{}; nonzero>0".format(expected_width, expected_height),
            'validation_observed': "{}x{}; nonzero={}".format(expected_width, expected_height, filled_cells),
            'validation_passed': True,
        }


class M2_RasterToPoint_OS(BaseBenchmark):
    """Benchmark: Raster to Points using Rasterio and GeoPandas"""

    def __init__(self):
        super(M2_RasterToPoint_OS, self).__init__("M2_RasterToPoint_OS", "mixed_os")
        self.input_path = None
        self.output_path = None

    def setup(self):
        self.input_path = get_analysis_raster_path(settings.DATA_DIR)
        self.output_path = os.path.join(settings.DATA_DIR, "M2_raster_to_point_os.gpkg")

        cfg = settings.get_raster_config_for_test('M2')
        expected_size = int(cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size')))
        needs_regen = True
        if os.path.exists(self.input_path):
            try:
                with rasterio.open(self.input_path) as src:
                    if int(src.width) == expected_size and int(src.height) == expected_size:
                        needs_regen = False
            except Exception:
                needs_regen = True

        if needs_regen and os.path.exists(self.input_path):
            try:
                os.remove(self.input_path)
            except Exception:
                pass

        if needs_regen:
            _create_analysis_raster_fallback(self.input_path, expected_size)

    def teardown(self):
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except:
                pass

    def run_single(self):
        # Delete previous output if present
        if self.output_path and os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except Exception:
                pass

        layer_name = "m2_raster_to_point"
        block_rows = 64  # keep chunk size bounded for large rasters

        total_written = 0
        expected_features = None

        with rasterio.open(self.input_path) as src:
            source_width = int(src.width)
            source_height = int(src.height)

            cfg = settings.get_raster_config_for_test('M2')
            expected_size = int(cfg.get('analysis_raster_size', settings.RASTER_CONFIG.get('analysis_raster_size')))
            if source_width != expected_size or source_height != expected_size:
                raise RuntimeError(
                    "M2_RasterToPoint_OS 输入栅格尺寸不符合当前规模: 实际 {}x{}, 期望 {}x{}".format(
                        source_width, source_height, expected_size, expected_size
                    )
                )

            transform = src.transform
            nodata = src.nodata
            crs = src.crs or "EPSG:{}".format(get_analysis_crs(settings.DATA_DIR))

            # RasterToPoint creates a point for every cell with a value (NoData is skipped).
            expected_features = int(source_width) * int(source_height) if nodata is None else None

            # Precompute column center offsets once per raster
            col_centers = (np.arange(source_width, dtype=np.float64) + 0.5)

            first_write = True
            for row_off in range(0, source_height, block_rows):
                rows_in_block = min(block_rows, source_height - row_off)
                window = rasterio.windows.Window(0, row_off, source_width, rows_in_block)
                data = src.read(1, window=window)

                if nodata is None:
                    values = data.reshape(-1)

                    row_centers = (row_off + np.arange(rows_in_block, dtype=np.float64) + 0.5)

                    # Fast path for north-up transforms (no rotation/shear)
                    if abs(float(transform.b)) < 1e-12 and abs(float(transform.d)) < 1e-12:
                        x_coords = float(transform.c) + col_centers * float(transform.a)
                        y_coords = float(transform.f) + row_centers * float(transform.e)
                        xs = np.tile(x_coords, rows_in_block)
                        ys = np.repeat(y_coords, source_width)
                    else:
                        cols_grid, rows_grid = np.meshgrid(col_centers, row_centers)
                        xs = (float(transform.c) + cols_grid * float(transform.a) + rows_grid * float(transform.b)).reshape(-1)
                        ys = (float(transform.f) + cols_grid * float(transform.d) + rows_grid * float(transform.e)).reshape(-1)

                    geoms = shapely.points(xs, ys)
                    chunk_gdf = gpd.GeoDataFrame({'value': values}, geometry=geoms, crs=crs)
                    pyogrio.write_dataframe(
                        chunk_gdf,
                        self.output_path,
                        layer=layer_name,
                        driver="GPKG",
                        append=(not first_write),
                    )
                    total_written += int(len(chunk_gdf))
                    first_write = False
                else:
                    valid_mask = (data != nodata)
                    if not np.any(valid_mask):
                        continue

                    valid_rows, valid_cols = np.nonzero(valid_mask)
                    values = data[valid_rows, valid_cols].reshape(-1)

                    rows_global = (row_off + valid_rows).astype(np.float64) + 0.5
                    cols_global = valid_cols.astype(np.float64) + 0.5

                    if abs(float(transform.b)) < 1e-12 and abs(float(transform.d)) < 1e-12:
                        xs = float(transform.c) + cols_global * float(transform.a)
                        ys = float(transform.f) + rows_global * float(transform.e)
                    else:
                        xs = float(transform.c) + cols_global * float(transform.a) + rows_global * float(transform.b)
                        ys = float(transform.f) + cols_global * float(transform.d) + rows_global * float(transform.e)

                    geoms = shapely.points(xs, ys)
                    chunk_gdf = gpd.GeoDataFrame({'value': values}, geometry=geoms, crs=crs)
                    pyogrio.write_dataframe(
                        chunk_gdf,
                        self.output_path,
                        layer=layer_name,
                        driver="GPKG",
                        append=(not first_write),
                    )
                    total_written += int(len(chunk_gdf))
                    first_write = False

        if expected_features is not None and total_written != expected_features:
            raise RuntimeError(
                "M2_RasterToPoint_OS 输出数量校验失败: 输入 {}x{} 期望 {} 个点, 实际 {} 个点".format(
                    source_width,
                    source_height,
                    expected_features,
                    total_written
                )
            )

        return {
            'features_created': total_written,
            'expected_features': expected_features if expected_features is not None else total_written,
            'input_width': source_width,
            'input_height': source_height,
            'validation_metric': 'raster_to_point_feature_count',
            'validation_expected': expected_features if expected_features is not None else total_written,
            'validation_observed': total_written,
            'validation_passed': True,
        }


if __name__ == '__main__':
    if not HAS_OS_LIBS:
        print("Open-source libraries not available. Please install:")
        print("  pip install geopandas rasterio shapely")
        sys.exit(1)

    print("Testing open-source mixed benchmarks...")
    benchmarks = MixedBenchmarksOS.get_all_benchmarks()
    for bm in benchmarks:
        print("\nTest: {}".format(bm.name))
        try:
            stats = bm.run(num_runs=1, warmup_runs=0)
            print("  Success: {}".format(stats.get('success')))
            print("  Mean time: {:.4f}s".format(stats.get('mean_time', 0)))
        except Exception as e:
            print("  Error: {}".format(str(e)))
