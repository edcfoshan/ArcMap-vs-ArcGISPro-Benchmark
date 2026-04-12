# -*- coding: utf-8 -*-
"""
Helpers for reading benchmark input paths and manifest metadata.
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import

import os

from config import settings
from utils.benchmark_manifest import load_manifest


def get_benchmark_root(root_dir=None):
    """Return the active benchmark data root directory."""
    return os.path.abspath(root_dir or getattr(settings, 'DATA_DIR', r'C:\temp\arcgis_benchmark_data'))


def get_manifest(root_dir=None, default=None):
    """Load the benchmark manifest for a given data root."""
    return load_manifest(get_benchmark_root(root_dir), default=default)


def get_active_format(root_dir=None):
    """Return the active input format from manifest or settings."""
    manifest = get_manifest(root_dir, default={})
    fmt = manifest.get('output_format')
    if fmt:
        return str(fmt).upper()
    return getattr(settings, 'ACTIVE_OUTPUT_FORMAT', 'GDB')


def get_active_complexity(root_dir=None):
    """Return the active complexity tier from manifest or settings."""
    manifest = get_manifest(root_dir, default={})
    complexity = manifest.get('complexity')
    if complexity:
        return str(complexity).lower()
    return getattr(settings, 'ACTIVE_COMPLEXITY', 'simple')


def get_benchmark_gdb_path(root_dir=None):
    """Return the benchmark file geodatabase path for the active root."""
    root_dir = get_benchmark_root(root_dir)
    return os.path.join(root_dir, getattr(settings, 'DEFAULT_GDB_NAME', 'benchmark_data.gdb'))


def get_benchmark_gpkg_path(root_dir=None):
    """Return the benchmark GeoPackage path for the active root."""
    root_dir = get_benchmark_root(root_dir)
    return os.path.join(root_dir, 'benchmark_data.gpkg')


def get_input_feature_path(dataset_name, root_dir=None):
    """Return the ArcPy-compatible path to an input feature class for the active format."""
    root_dir = get_benchmark_root(root_dir)
    fmt = get_active_format(root_dir)
    if fmt == 'SHP':
        return os.path.join(root_dir, '{}.shp'.format(dataset_name))
    if fmt == 'GPKG':
        return os.path.join(get_benchmark_gpkg_path(root_dir), dataset_name)
    return os.path.join(get_benchmark_gdb_path(root_dir), dataset_name)


def get_input_feature_path_os(dataset_name, root_dir=None):
    """Return the (path, layer) tuple for GeoPandas for the active format."""
    root_dir = get_benchmark_root(root_dir)
    fmt = get_active_format(root_dir)
    if fmt == 'SHP':
        return os.path.join(root_dir, '{}.shp'.format(dataset_name)), None
    if fmt == 'GPKG':
        return get_benchmark_gpkg_path(root_dir), dataset_name
    return get_benchmark_gdb_path(root_dir), dataset_name


def get_analysis_boundary_path(root_dir=None):
    """Return the boundary feature class path used by the benchmarks."""
    root_dir = get_benchmark_root(root_dir)
    manifest = get_manifest(root_dir, default={})
    path = manifest.get('analysis_boundary_path')
    if path:
        return path
    return os.path.join(get_benchmark_gdb_path(root_dir), 'analysis_boundary')


def get_analysis_boundary_extent(root_dir=None):
    """Return the boundary extent as a 4-tuple when available."""
    manifest = get_manifest(root_dir, default={})
    extent = manifest.get('analysis_boundary_extent') or {}
    if isinstance(extent, dict):
        try:
            return (
                float(extent.get('xmin')),
                float(extent.get('ymin')),
                float(extent.get('xmax')),
                float(extent.get('ymax')),
            )
        except Exception:
            return None

    if isinstance(extent, (list, tuple)) and len(extent) >= 4:
        try:
            return float(extent[0]), float(extent[1]), float(extent[2]), float(extent[3])
        except Exception:
            return None

    return None


def get_analysis_crs(root_dir=None):
    """Return the projected analysis CRS code used by benchmark inputs."""
    manifest = get_manifest(root_dir, default={})
    try:
        return int(manifest.get('analysis_crs', 3857))
    except Exception:
        return 3857


def get_analysis_raster_path(root_dir=None):
    """Return the analysis raster path used by the benchmarks."""
    root_dir = get_benchmark_root(root_dir)
    manifest = get_manifest(root_dir, default={})
    path = manifest.get('analysis_raster_path')
    if path:
        return path
    return os.path.join(root_dir, 'analysis_raster.tif')


def get_constant_raster_path(root_dir=None):
    """Return the baseline constant raster path used by the benchmarks."""
    root_dir = get_benchmark_root(root_dir)
    manifest = get_manifest(root_dir, default={})
    path = manifest.get('constant_raster_path')
    if path:
        return path
    return os.path.join(root_dir, 'constant_raster.tif')


def get_source_mode(root_dir=None):
    """Return the active input source mode ('osm' or 'synthetic')."""
    manifest = get_manifest(root_dir, default={})
    return manifest.get('source_mode', 'synthetic')


def get_osm_source_summary(root_dir=None):
    """Return a compact dict describing the current OSM cache/source."""
    manifest = get_manifest(root_dir, default={})
    return manifest.get('osm_source') or {}
