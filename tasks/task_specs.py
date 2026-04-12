# -*- coding: utf-8 -*-
"""
Task specification constants for the 6-core benchmark matrix.
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import

CORE_TASK_IDS = [
    "Buffer",
    "Intersect",
    "SpatialJoin",
    "Resample",
    "Clip",
    "PolygonToRaster",
]

CORE_TASK_CATEGORIES = {
    "Buffer": "vector",
    "Intersect": "vector",
    "SpatialJoin": "vector",
    "Resample": "raster",
    "Clip": "raster",
    "PolygonToRaster": "mixed",
}

CORE_TASK_NAMES = {
    "Buffer": "Vector Buffer",
    "Intersect": "Overlay Intersect",
    "SpatialJoin": "Spatial Join",
    "Resample": "Raster Resample",
    "Clip": "Raster Clip/Mask",
    "PolygonToRaster": "Polygon to Raster",
}

# Mapping from core task id to legacy benchmark name used in the original suite.
# This allows the runner to instantiate the correct legacy benchmark class.
LEGACY_BENCHMARK_NAMES = {
    "Buffer": "V3_Buffer",
    "Intersect": "V4_Intersect",
    "SpatialJoin": "V5_SpatialJoin",
    "Resample": "R2_Resample",
    "Clip": "R3_Clip",
    "PolygonToRaster": "M1_PolygonToRaster",
}

# Legacy open-source suffix
LEGACY_BENCHMARK_NAMES_OS = {
    "Buffer": "V3_Buffer_OS",
    "Intersect": "V4_Intersect_OS",
    "SpatialJoin": "V5_SpatialJoin_OS",
    "Resample": "R2_Resample_OS",
    "Clip": "R3_Clip_OS",
    "PolygonToRaster": "M1_PolygonToRaster_OS",
}

FORMAT_EXTENSIONS = {
    "SHP": ".shp",
    "GPKG": ".gpkg",
    "GDB": "",  # feature class inside geodatabase
}

FORMAT_DRIVERS_OS = {
    "SHP": "ESRI Shapefile",
    "GPKG": "GPKG",
    "GDB": "OpenFileGDB",
}

ALL_SCALES = ["tiny", "small", "standard", "medium", "large"]
ALL_FORMATS = ["SHP", "GPKG", "GDB"]
ALL_COMPLEXITIES = ["simple", "medium", "complex"]
