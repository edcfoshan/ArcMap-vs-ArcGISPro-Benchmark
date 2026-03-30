# -*- coding: utf-8 -*-
"""
Configuration settings for ArcGIS Performance Benchmark
Compatible with both Python 2.7 and Python 3.x
"""
from __future__ import print_function, division, absolute_import
import os
import sys

# ============================================================================
# Test Configuration
# ============================================================================

# Number of runs for each test (excluding warmup)
TEST_RUNS = 1

# Warmup runs (not counted in results)
WARMUP_RUNS = 0

# ============================================================================
# Data Scale Configuration
# ============================================================================

# Tiny Scale (super lightweight, for quick verification)
VECTOR_CONFIG_TINY = {
    'fishnet_rows': 50,
    'fishnet_cols': 50,
    'random_points': 1000,
    'buffer_points': 1000,
    'intersect_features_a': 10000,
    'intersect_features_b': 10000,
    'spatial_join_points': 5000,
    'spatial_join_polygons': 500,
    'calculate_field_records': 10000,
}

RASTER_CONFIG_TINY = {
    'constant_raster_size': 500,  # pixels (square)
    'resample_source_size': 500,
    'resample_target_size': 250,
    'clip_ratio': 0.5,
}

# Small Scale (quick test for debugging)
VECTOR_CONFIG_SMALL = {
    'fishnet_rows': 100,
    'fishnet_cols': 100,
    'random_points': 10000,
    'buffer_points': 10000,
    'intersect_features_a': 100000,
    'intersect_features_b': 100000,
    'spatial_join_points': 50000,
    'spatial_join_polygons': 1000,
    'calculate_field_records': 100000,
}

RASTER_CONFIG_SMALL = {
    'constant_raster_size': 1000,  # pixels (square)
    'resample_source_size': 1000,
    'resample_target_size': 500,
    'clip_ratio': 0.5,
}

# Standard Scale (between small and medium, for moderate testing)
VECTOR_CONFIG_STANDARD = {
    'fishnet_rows': 500,
    'fishnet_cols': 500,  # 500×500=250,000 polygons
    'random_points': 50000,
    'buffer_points': 50000,
    'intersect_features_a': 300000,
    'intersect_features_b': 300000,
    'spatial_join_points': 200000,
    'spatial_join_polygons': 5000,
    'calculate_field_records': 300000,
}

RASTER_CONFIG_STANDARD = {
    'constant_raster_size': 5000,  # pixels (square)
    'resample_source_size': 5000,
    'resample_target_size': 2500,
    'clip_ratio': 0.5,
}

# Medium Scale (original - 1M records for intensive testing)
VECTOR_CONFIG_MEDIUM = {
    'fishnet_rows': 1000,
    'fishnet_cols': 1000,  # 1000×1000=1,000,000 polygons
    'random_points': 100000,
    'buffer_points': 100000,
    'intersect_features_a': 1000000,
    'intersect_features_b': 1000000,
    'spatial_join_points': 500000,
    'spatial_join_polygons': 10000,  # Use independent grid, not full fishnet
    'calculate_field_records': 1000000,
}

RASTER_CONFIG_MEDIUM = {
    'constant_raster_size': 10000,  # pixels (square)
    'resample_source_size': 10000,
    'resample_target_size': 5000,
    'clip_ratio': 0.5,
}

# Large Scale (for academic paper)
VECTOR_CONFIG_LARGE = {
    'fishnet_rows': 5000,
    'fishnet_cols': 5000,
    'random_points': 500000,
    'buffer_points': 500000,
    'intersect_features_a': 5000000,
    'intersect_features_b': 5000000,
    'spatial_join_points': 2000000,
    'spatial_join_polygons': 50000,
    'calculate_field_records': 5000000,
}

RASTER_CONFIG_LARGE = {
    'constant_raster_size': 30000,  # pixels (square)
    'resample_source_size': 30000,
    'resample_target_size': 15000,
    'clip_ratio': 0.5,
}

# Select configuration to use
# Options: 'tiny', 'small', 'standard', 'medium', 'large'
DATA_SCALE = 'tiny'

# All available scales
ALL_SCALES = ['tiny', 'small', 'standard', 'medium', 'large']

if DATA_SCALE == 'tiny':
    VECTOR_CONFIG = VECTOR_CONFIG_TINY
    RASTER_CONFIG = RASTER_CONFIG_TINY
elif DATA_SCALE == 'small':
    VECTOR_CONFIG = VECTOR_CONFIG_SMALL
    RASTER_CONFIG = RASTER_CONFIG_SMALL
elif DATA_SCALE == 'standard':
    VECTOR_CONFIG = VECTOR_CONFIG_STANDARD
    RASTER_CONFIG = RASTER_CONFIG_STANDARD
elif DATA_SCALE == 'large':
    VECTOR_CONFIG = VECTOR_CONFIG_LARGE
    RASTER_CONFIG = RASTER_CONFIG_LARGE
else:  # medium (default)
    VECTOR_CONFIG = VECTOR_CONFIG_MEDIUM
    RASTER_CONFIG = RASTER_CONFIG_MEDIUM

# ============================================================================
# Multiprocess Configuration
# ============================================================================

# Multiprocess benchmark settings
MULTIPROCESS_CONFIG = {
    'enabled': False,  # Enable multiprocess benchmarks
    'num_workers': 4,  # Number of worker processes
    'scales': ['tiny', 'small', 'standard', 'medium', 'large'],  # Scales to run multiprocess tests (all supported)
}

# Get multiprocess settings with defaults
def get_multiprocess_workers():
    return MULTIPROCESS_CONFIG.get('num_workers', 4)

def is_multiprocess_enabled(scale=None):
    if not MULTIPROCESS_CONFIG.get('enabled', False):
        return False
    if scale is None:
        scale = DATA_SCALE
    return scale in MULTIPROCESS_CONFIG.get('scales', [])

# ============================================================================
# Path Configuration
# ============================================================================

# Data directory - stored in C:\temp for easy cleanup
DATA_DIR = r'C:\temp\arcgis_benchmark_data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Results directory - stored in project folder (small files)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
RAW_RESULTS_DIR = os.path.join(RESULTS_DIR, 'raw')
TABLES_DIR = os.path.join(RESULTS_DIR, 'tables')
FIGURES_DIR = os.path.join(RESULTS_DIR, 'figures')

# Create directories if they don't exist
for dir_path in [RESULTS_DIR, RAW_RESULTS_DIR, TABLES_DIR, FIGURES_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# ============================================================================
# ArcGIS Configuration
# ============================================================================

# Spatial reference (WGS 84)
SPATIAL_REFERENCE = 4326

# Default geodatabase name - includes scale to avoid regeneration
# Format: benchmark_data_{scale}.gdb (e.g., benchmark_data_tiny.gdb)
# This allows reusing test data across runs if scale matches
DEFAULT_GDB_NAME = 'benchmark_data_{}.gdb'.format(DATA_SCALE)

# Scratch workspace
SCRATCH_WORKSPACE = os.path.join(DATA_DIR, 'scratch')
if not os.path.exists(SCRATCH_WORKSPACE):
    os.makedirs(SCRATCH_WORKSPACE)

# ============================================================================
# Output Configuration
# ============================================================================

# Output formats
OUTPUT_FORMATS = ['json', 'csv', 'markdown', 'latex']

# Default output format
DEFAULT_OUTPUT_FORMAT = 'markdown'

# Precision for timing results (decimal places)
TIMING_PRECISION = 4

# ============================================================================
# Test Categories
# ============================================================================

TEST_CATEGORIES = {
    'vector': [
        'V1_CreateFishnet',
        'V2_CreateRandomPoints',
        'V3_Buffer',
        'V4_Intersect',
        'V5_SpatialJoin',
        'V6_CalculateField',
    ],
    'raster': [
        'R1_CreateConstantRaster',
        'R2_Resample',
        'R3_Clip',
        'R4_RasterCalculator',
    ],
    'mixed': [
        'M1_PolygonToRaster',
        'M2_RasterToPoint',
    ],
}

# All tests
ALL_TESTS = []
for category in TEST_CATEGORIES.values():
    ALL_TESTS.extend(category)

# ============================================================================
# Memory Monitoring (Windows only)
# ============================================================================

ENABLE_MEMORY_MONITORING = True
MEMORY_SAMPLE_INTERVAL = 0.5  # seconds

# ============================================================================
# Helper Functions
# ============================================================================

def get_test_data_path(filename):
    """Get full path for test data file"""
    return os.path.join(DATA_DIR, filename)

def get_result_path(filename, subdir='raw'):
    """Get full path for result file"""
    if subdir == 'raw':
        return os.path.join(RAW_RESULTS_DIR, filename)
    elif subdir == 'tables':
        return os.path.join(TABLES_DIR, filename)
    elif subdir == 'figures':
        return os.path.join(FIGURES_DIR, filename)
    else:
        return os.path.join(RESULTS_DIR, filename)

def cleanup_data():
    """Clean up all test data from C:\temp"""
    import shutil
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
        print("Cleaned up: {}".format(DATA_DIR))

def print_config():
    """Print current configuration"""
    print("=" * 60)
    print("ArcGIS Performance Benchmark Configuration")
    print("=" * 60)
    print("Python Version: {}.{}.{}".format(
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro
    ))
    print("Data Scale: {}".format(DATA_SCALE.upper()))
    print("Test Runs: {} (plus {} warmup)".format(TEST_RUNS, WARMUP_RUNS))
    print("Memory Monitoring: {}".format("Enabled" if ENABLE_MEMORY_MONITORING else "Disabled"))
    print("Data Directory: {}".format(DATA_DIR))
    print("Results Directory: {}".format(RESULTS_DIR))
    print("=" * 60)

if __name__ == '__main__':
    print_config()
