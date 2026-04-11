# -*- coding: utf-8 -*-
"""
Raster helper utilities for ArcPy benchmarks.
Compatible with Python 2.7 and 3.x.
"""
from __future__ import print_function, division, absolute_import
import os

try:
    import numpy as np
except ImportError:
    np = None

try:
    import arcpy
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False
    arcpy = None

from utils.gis_cleanup import remove_dataset_artifacts
from utils.benchmark_shapes import build_block_pattern_array


def _parse_extent(extent):
    """Parse an extent value into four floats."""
    if extent is None:
        return -180.0, -90.0, 180.0, 90.0

    if isinstance(extent, (tuple, list)) and len(extent) >= 4:
        return float(extent[0]), float(extent[1]), float(extent[2]), float(extent[3])

    text = str(extent).replace(',', ' ')
    parts = [part for part in text.split() if part]
    if len(parts) < 4:
        raise ValueError("Invalid extent: {}".format(extent))
    return float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])


def _ensure_parent_dir(path):
    """Create parent directory when needed."""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)


def spatial_analyst_available():
    """Return True when the Spatial Analyst extension is available."""
    if not HAS_ARCPY:
        return False

    try:
        return arcpy.CheckExtension("Spatial") == "Available"
    except Exception:
        return False


def create_constant_raster(output_path, cell_size, extent, value=1, spatial_reference=None,
                           use_spatial_analyst=False):
    """Create a constant raster.

    The benchmark defaults to the NumPy implementation so it works even when the
    Spatial Analyst extension is unavailable. Set ``use_spatial_analyst=True`` to
    opt into the native ArcPy path when the license is present.
    """
    if not HAS_ARCPY:
        raise RuntimeError("ArcPy is required to create benchmark rasters")

    _ensure_parent_dir(output_path)
    remove_dataset_artifacts(output_path)

    x_min, y_min, x_max, y_max = _parse_extent(extent)
    extent_text = "{} {} {} {}".format(x_min, y_min, x_max, y_max)

    if use_spatial_analyst and spatial_analyst_available():
        try:
            try:
                arcpy.CheckOutExtension("Spatial")
            except Exception:
                pass

            from arcpy.sa import CreateConstantRaster
            out_raster = CreateConstantRaster(value, "INTEGER", cell_size, extent_text)
            out_raster.save(output_path)
            if spatial_reference is not None:
                arcpy.DefineProjection_management(output_path, spatial_reference)
            return output_path
        except Exception:
            pass
        finally:
            try:
                arcpy.CheckInExtension("Spatial")
            except Exception:
                pass

    if np is None:
        raise RuntimeError("NumPy is required for the raster fallback")

    width = max(1, int(round((x_max - x_min) / float(cell_size))))
    height = max(1, int(round((y_max - y_min) / float(cell_size))))
    array = np.ones((height, width), dtype=np.int16) * int(value)
    lower_left = arcpy.Point(x_min, y_min)
    raster = arcpy.NumPyArrayToRaster(
        array,
        lower_left,
        float(cell_size),
        float(cell_size)
    )
    raster.save(output_path)
    if spatial_reference is not None:
        arcpy.DefineProjection_management(output_path, spatial_reference)
    return output_path


def double_raster(input_raster, output_raster, use_spatial_analyst=False):
    """Multiply raster values by two.

    The benchmark defaults to the NumPy implementation so it does not depend on
    Spatial Analyst licensing. Set ``use_spatial_analyst=True`` to opt into the
    native ArcPy path when the license is present.
    """
    if not HAS_ARCPY:
        raise RuntimeError("ArcPy is required to process benchmark rasters")

    _ensure_parent_dir(output_raster)
    remove_dataset_artifacts(output_raster)

    if use_spatial_analyst and spatial_analyst_available():
        try:
            try:
                arcpy.CheckOutExtension("Spatial")
            except Exception:
                pass

            from arcpy.sa import Raster, Int, Times
            out_raster = Int(Times(Raster(input_raster), 2))
            out_raster.save(output_raster)
            return output_raster
        except Exception:
            pass
        finally:
            try:
                arcpy.CheckInExtension("Spatial")
            except Exception:
                pass

    if np is None:
        raise RuntimeError("NumPy is required for the raster fallback")

    desc = arcpy.Describe(input_raster)
    array = arcpy.RasterToNumPyArray(input_raster)
    array = array * 2
    lower_left = arcpy.Point(desc.extent.XMin, desc.extent.YMin)
    raster = arcpy.NumPyArrayToRaster(
        array,
        lower_left,
        desc.meanCellWidth,
        desc.meanCellHeight
    )
    raster.save(output_raster)
    if hasattr(desc, 'spatialReference') and desc.spatialReference:
        arcpy.DefineProjection_management(output_raster, desc.spatialReference)
    return output_raster


def create_block_pattern_raster(output_path, cell_size, extent, block_size, levels=6, spatial_reference=None):
    """Create a deterministic integer raster with repeating block regions."""
    if not HAS_ARCPY:
        raise RuntimeError("ArcPy is required to create benchmark rasters")

    _ensure_parent_dir(output_path)
    remove_dataset_artifacts(output_path)

    x_min, y_min, x_max, y_max = _parse_extent(extent)
    width = max(1, int(round((x_max - x_min) / float(cell_size))))
    height = max(1, int(round((y_max - y_min) / float(cell_size))))
    if width != height:
        raise RuntimeError("Patterned benchmark rasters must be square: {}x{}".format(height, width))

    array = build_block_pattern_array(height, width, block_size=block_size, levels=levels)
    lower_left = arcpy.Point(x_min, y_min)
    raster = arcpy.NumPyArrayToRaster(
        array,
        lower_left,
        float(cell_size),
        float(cell_size)
    )
    raster.save(output_path)
    if spatial_reference is not None:
        arcpy.DefineProjection_management(output_path, spatial_reference)
    return output_path


def expected_clip_dimension(input_size, clip_ratio):
    """Return the expected raster dimension after centered clipping.

    The benchmark clip geometry is centered on raster bounds, and ArcGIS /
    Rasterio can both return one extra cell when the clipped span lands on a
    half-cell boundary. We normalize that behavior here so both benchmark
    stacks validate against the same rule.
    """
    expected_size = int(round(float(input_size) * float(clip_ratio)))
    if expected_size % 2 == 1:
        expected_size += 1
    return expected_size
