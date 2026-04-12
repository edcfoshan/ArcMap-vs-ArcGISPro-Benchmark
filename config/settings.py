# -*- coding: utf-8 -*-
"""
Configuration settings for ArcGIS Performance Benchmark
Compatible with both Python 2.7 and Python 3.x
"""
from __future__ import print_function, division, absolute_import
import os
import sys
import copy

# ============================================================================
# Test Configuration
# ============================================================================

# Number of runs for each test (excluding warmup)
TEST_RUNS = 3

# Warmup runs (not counted in results)
WARMUP_RUNS = 1

# ============================================================================
# Data Scale Configuration
# ============================================================================

# Tiny Scale (super lightweight, for quick verification)
VECTOR_CONFIG_TINY = {
    'fishnet_rows': 50,
    'fishnet_cols': 50,
    'random_points': 5000,
    'buffer_points': 5000,
    'intersect_features_a': 20000,
    'intersect_features_b': 20000,
    'spatial_join_points': 10000,
    'spatial_join_polygons': 1000,
    'calculate_field_records': 20000,
}

RASTER_CONFIG_TINY = {
    'constant_raster_size': 500,  # pixels (square)
    'resample_source_size': 500,
    'resample_target_size': 250,
    'clip_ratio': 0.5,
    'analysis_raster_size': 600,
    'analysis_raster_target_size': 300,
    'analysis_raster_clip_ratio': 0.5,
}

# Small Scale (quick test for debugging)
VECTOR_CONFIG_SMALL = {
    'fishnet_rows': 100,
    'fishnet_cols': 100,
    'random_points': 10000,
    'buffer_points': 10000,
    'intersect_features_a': 40000,
    'intersect_features_b': 40000,
    'spatial_join_points': 20000,
    'spatial_join_polygons': 2000,
    'calculate_field_records': 40000,
}

RASTER_CONFIG_SMALL = {
    'constant_raster_size': 1000,  # pixels (square)
    'resample_source_size': 1000,
    'resample_target_size': 500,
    'clip_ratio': 0.5,
    'analysis_raster_size': 1200,
    'analysis_raster_target_size': 600,
    'analysis_raster_clip_ratio': 0.5,
}

# Standard Scale (balanced, for regular benchmark runs)
VECTOR_CONFIG_STANDARD = {
    'fishnet_rows': 250,
    'fishnet_cols': 250,  # 250×250=62,500 polygons
    'random_points': 25000,
    'buffer_points': 25000,
    'intersect_features_a': 250000,
    'intersect_features_b': 250000,
    'spatial_join_points': 125000,
    'spatial_join_polygons': 2500,
    'calculate_field_records': 250000,
}

RASTER_CONFIG_STANDARD = {
    'constant_raster_size': 2500,  # pixels (square)
    'resample_source_size': 2500,
    'resample_target_size': 1250,
    'clip_ratio': 0.5,
    'analysis_raster_size': 2500,
    'analysis_raster_target_size': 1250,
    'analysis_raster_clip_ratio': 0.5,
}

# ============================================================================
# Standard Scale Per-Test Overrides
# ============================================================================
#
# standard 作为论文主尺度，允许每个测试项使用独立的输入规模参数，
# 以便把 12 项尽量拉到 30-90s 的可比较区间。tiny/small 仍保持统一倍数尺度，
# 用于快速验证链路是否正常。
#
# 说明：
# - 这里的覆盖是“按测试项覆盖配置字段”，最终输入仍在同一个 gdb 中生成；
#   各测试项主要使用不同的输入图层，因此覆盖字段基本互不冲突。
# - 若某项仍明显偏短，优先只调整对应测试项的覆盖参数，而不是叠加多步骤流程。
#
STANDARD_VECTOR_CONFIG_BY_TEST = {
    # 控制组：尽量保持偏轻
    'V1': {
        'fishnet_rows': 1500,
        'fishnet_cols': 1500,
    },
    'V2': {
        'random_points': 1000000,
    },
    # 重点提压项（第二轮迭代，基于实测 2026-04-12 tiny/standard 数据调参）
    'V3': {
        'buffer_points': 200000,
    },
    'V4': {
        'intersect_features_a': 200000,
        'intersect_features_b': 200000,
    },
    'V5': {
        'spatial_join_points': 85000,
        'spatial_join_polygons': 1700,
    },
    'V6': {
        'calculate_field_records': 750000,
    },
    # 混合项默认复用矢量/栅格输入规模
    'M1': {},
    'M2': {},
}

STANDARD_RASTER_CONFIG_BY_TEST = {
    # 控制组：偏轻
    'R1': {
        'constant_raster_size': 32700,
    },
    # 重点提压项：优先通过像元规模与重采样比提时
    'R2': {
        'resample_source_size': 30000,
        'resample_target_size': 28000,
    },
    'R3': {
        'analysis_raster_size': 32000,
        'analysis_raster_clip_ratio': 0.98,
    },
    'R4': {
        'analysis_raster_size': 32600,
        'analysis_raster_target_size': 15000,
        'analysis_raster_clip_ratio': 0.95,
    },
    'M1': {
        'analysis_raster_size': 18000,
    },
    'M2': {
        'analysis_raster_size': 1500,
    },
}

# Medium Scale (heavier than standard but still intended to be runnable)
VECTOR_CONFIG_MEDIUM = {
    'fishnet_rows': 375,
    'fishnet_cols': 375,  # 375×375=140,625 polygons
    'random_points': 37500,
    'buffer_points': 37500,
    'intersect_features_a': 375000,
    'intersect_features_b': 375000,
    'spatial_join_points': 187500,
    'spatial_join_polygons': 3750,
    'calculate_field_records': 375000,
}

RASTER_CONFIG_MEDIUM = {
    'constant_raster_size': 3750,  # pixels (square)
    'resample_source_size': 3750,
    'resample_target_size': 1875,
    'clip_ratio': 0.5,
    'analysis_raster_size': 3750,
    'analysis_raster_target_size': 1875,
    'analysis_raster_clip_ratio': 0.5,
}

# Large Scale (capped at half of the legacy medium profile)
VECTOR_CONFIG_LARGE = {
    'fishnet_rows': 500,
    'fishnet_cols': 500,  # 500×500=250,000 polygons
    'random_points': 50000,
    'buffer_points': 50000,
    'intersect_features_a': 500000,
    'intersect_features_b': 500000,
    'spatial_join_points': 250000,
    'spatial_join_polygons': 5000,
    'calculate_field_records': 500000,
}

RASTER_CONFIG_LARGE = {
    'constant_raster_size': 5000,  # pixels (square)
    'resample_source_size': 5000,
    'resample_target_size': 2500,
    'clip_ratio': 0.5,
    'analysis_raster_size': 5000,
    'analysis_raster_target_size': 2500,
    'analysis_raster_clip_ratio': 0.5,
}

# Active format and complexity for multi-matrix runs
ACTIVE_OUTPUT_FORMAT = 'GDB'
ACTIVE_COMPLEXITY = 'simple'

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
DATA_ROOT_DIR = r'C:\temp\arcgis_benchmark_data'
DATA_DIR = DATA_ROOT_DIR
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Shared cache / metadata paths
OSM_CACHE_DIR = os.path.join(DATA_ROOT_DIR, '_osm_cache')
BENCHMARK_MANIFEST_NAME = 'benchmark_manifest.json'
BENCHMARK_RUN_LOG_NAME = 'benchmark_run.log'
if not os.path.exists(OSM_CACHE_DIR):
    os.makedirs(OSM_CACHE_DIR)

# Results directory - stored in project folder (small files)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
RAW_RESULTS_DIR = os.path.join(RESULTS_DIR, 'raw')
TABLES_DIR = os.path.join(RESULTS_DIR, 'tables')
FIGURES_DIR = os.path.join(RESULTS_DIR, 'figures')

# Timestamped results directory (set dynamically at runtime)
TIMESTAMPED_RESULTS_DIR = None
CURRENT_TIMESTAMP = None

def set_timestamped_dirs(timestamp=None, base_data_dir=None):
    """Set timestamped directories for temp folder organization

    Args:
        timestamp: Timestamp string (YYYYMMDD_HHMMSS). If None, generates current time.
        base_data_dir: Base data directory. If None, uses default temp path.
    """
    global TIMESTAMPED_RESULTS_DIR, RAW_RESULTS_DIR, TABLES_DIR, FIGURES_DIR, RESULTS_DIR
    global DATA_DIR, DEFAULT_GDB_NAME, SCRATCH_WORKSPACE

    if timestamp is None:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if base_data_dir is None:
        base_data_dir = r'C:\temp\arcgis_benchmark_data'

    # Store the timestamp for later use
    global CURRENT_TIMESTAMP
    CURRENT_TIMESTAMP = timestamp

    # Set data directory to timestamped folder
    DATA_DIR = os.path.join(base_data_dir, timestamp)

    # Keep reports at the timestamp root and raw artifacts under a dedicated
    # data folder so the top-level directory stays tidy.
    TIMESTAMPED_RESULTS_DIR = DATA_DIR
    RESULTS_DIR = DATA_DIR
    RAW_RESULTS_DIR = os.path.join(DATA_DIR, 'data')
    TABLES_DIR = DATA_DIR
    FIGURES_DIR = DATA_DIR

    # Scratch work stays flat; runtime code can narrow this further if needed.
    SCRATCH_WORKSPACE = DATA_DIR

    # 保持为文件名，避免 ArcPy 在 CreateFileGDB 时把完整路径当作名称
    DEFAULT_GDB_NAME = 'benchmark_data_{}.gdb'.format(DATA_SCALE)

    # Create the root folder and the raw-data base folder.
    for dir_path in [DATA_DIR, RAW_RESULTS_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    return TIMESTAMPED_RESULTS_DIR


def set_output_root(output_root):
    """Set the benchmark output root to an exact directory."""
    global TIMESTAMPED_RESULTS_DIR, RAW_RESULTS_DIR, TABLES_DIR, FIGURES_DIR, RESULTS_DIR
    global DATA_DIR, DEFAULT_GDB_NAME, SCRATCH_WORKSPACE, CURRENT_TIMESTAMP

    output_root = os.path.abspath(output_root)
    RESULTS_DIR = output_root
    TIMESTAMPED_RESULTS_DIR = output_root
    RAW_RESULTS_DIR = os.path.join(output_root, 'data')
    TABLES_DIR = output_root
    FIGURES_DIR = output_root
    DATA_DIR = output_root
    CURRENT_TIMESTAMP = os.path.basename(output_root)
    DEFAULT_GDB_NAME = 'benchmark_data_{}.gdb'.format(DATA_SCALE)
    SCRATCH_WORKSPACE = os.path.join(output_root, 'scratch')

    for dir_path in [RESULTS_DIR, RAW_RESULTS_DIR, TABLES_DIR, FIGURES_DIR, DATA_DIR, SCRATCH_WORKSPACE]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    return RESULTS_DIR

def reset_to_default_dirs():
    """Reset to default project-based results directories"""
    global TIMESTAMPED_RESULTS_DIR, RAW_RESULTS_DIR, TABLES_DIR, FIGURES_DIR, RESULTS_DIR
    global DATA_DIR, DEFAULT_GDB_NAME, SCRATCH_WORKSPACE, CURRENT_TIMESTAMP

    RESULTS_DIR = os.path.join(BASE_DIR, 'results')
    RAW_RESULTS_DIR = os.path.join(RESULTS_DIR, 'raw')
    TABLES_DIR = os.path.join(RESULTS_DIR, 'tables')
    FIGURES_DIR = os.path.join(RESULTS_DIR, 'figures')
    TIMESTAMPED_RESULTS_DIR = None
    CURRENT_TIMESTAMP = None

    # Reset data directory
    DATA_DIR = r'C:\temp\arcgis_benchmark_data'
    SCRATCH_WORKSPACE = os.path.join(DATA_DIR, 'scratch')
    DEFAULT_GDB_NAME = 'benchmark_data_{}.gdb'.format(DATA_SCALE)

    # Create directories if they don't exist
    for dir_path in [RESULTS_DIR, RAW_RESULTS_DIR, TABLES_DIR, FIGURES_DIR, DATA_DIR, SCRATCH_WORKSPACE]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


def get_default_gdb_name():
    """获取默认地理数据库名称（不含目录）"""
    return os.path.basename(DEFAULT_GDB_NAME)


def get_default_gdb_path():
    """获取默认地理数据库完整路径"""
    if os.path.isabs(DEFAULT_GDB_NAME):
        return DEFAULT_GDB_NAME
    return os.path.join(DATA_DIR, DEFAULT_GDB_NAME)

# Create default directories if they don't exist
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
MEMORY_SAMPLE_INTERVAL = 0.1  # seconds, fine-grained enough for short GIS tasks

# Progress heartbeat interval for long-running tasks.
# Set to 0 or a negative value to disable heartbeat logs.
PROGRESS_HEARTBEAT_INTERVAL = 2

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

def set_scale(scale, scale_overrides=None):
    """Set data scale dynamically"""
    global DATA_SCALE, VECTOR_CONFIG, RASTER_CONFIG, DEFAULT_GDB_NAME
    
    if scale not in ALL_SCALES:
        raise ValueError("Invalid scale: {}. Must be one of: {}".format(scale, ALL_SCALES))
    
    DATA_SCALE = scale

    # Update VECTOR_CONFIG
    if scale == 'tiny':
        VECTOR_CONFIG = copy.deepcopy(VECTOR_CONFIG_TINY)
        RASTER_CONFIG = copy.deepcopy(RASTER_CONFIG_TINY)
    elif scale == 'small':
        VECTOR_CONFIG = copy.deepcopy(VECTOR_CONFIG_SMALL)
        RASTER_CONFIG = copy.deepcopy(RASTER_CONFIG_SMALL)
    elif scale == 'standard':
        VECTOR_CONFIG = copy.deepcopy(VECTOR_CONFIG_STANDARD)
        RASTER_CONFIG = copy.deepcopy(RASTER_CONFIG_STANDARD)
    elif scale == 'medium':
        VECTOR_CONFIG = copy.deepcopy(VECTOR_CONFIG_MEDIUM)
        RASTER_CONFIG = copy.deepcopy(RASTER_CONFIG_MEDIUM)
    elif scale == 'large':
        VECTOR_CONFIG = copy.deepcopy(VECTOR_CONFIG_LARGE)
        RASTER_CONFIG = copy.deepcopy(RASTER_CONFIG_LARGE)

    if isinstance(scale_overrides, dict) and scale_overrides:
        if 'vector' in scale_overrides or 'raster' in scale_overrides:
            vector_overrides = scale_overrides.get('vector', {}) or {}
            raster_overrides = scale_overrides.get('raster', {}) or {}
            if isinstance(vector_overrides, dict) and 'intersect_features' in vector_overrides:
                legacy_value = vector_overrides.pop('intersect_features')
                vector_overrides.setdefault('intersect_features_a', legacy_value)
                vector_overrides.setdefault('intersect_features_b', legacy_value)
        else:
            vector_overrides = {}
            raster_overrides = {}
            for key, value in scale_overrides.items():
                if key == 'intersect_features':
                    vector_overrides['intersect_features_a'] = value
                    vector_overrides['intersect_features_b'] = value
                elif key in VECTOR_CONFIG:
                    vector_overrides[key] = value
                elif key in RASTER_CONFIG:
                    raster_overrides[key] = value
        if isinstance(vector_overrides, dict):
            VECTOR_CONFIG.update(vector_overrides)
        if isinstance(raster_overrides, dict):
            RASTER_CONFIG.update(raster_overrides)
    
    # Update DEFAULT_GDB_NAME
    DEFAULT_GDB_NAME = 'benchmark_data_{}.gdb'.format(DATA_SCALE)


def _merge_config(base_config, override):
    merged = copy.deepcopy(base_config or {})
    if isinstance(override, dict) and override:
        merged.update(override)
    return merged


def get_vector_config_for_test(test_id):
    """Return the active vector config, optionally overridden per test in standard scale."""
    base = VECTOR_CONFIG
    if DATA_SCALE != 'standard':
        return base
    key = str(test_id or '').upper()
    overrides = STANDARD_VECTOR_CONFIG_BY_TEST.get(key) or {}
    return _merge_config(base, overrides)


def get_raster_config_for_test(test_id):
    """Return the active raster config, optionally overridden per test in standard scale."""
    base = RASTER_CONFIG
    if DATA_SCALE != 'standard':
        return base
    key = str(test_id or '').upper()
    overrides = STANDARD_RASTER_CONFIG_BY_TEST.get(key) or {}
    return _merge_config(base, overrides)


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
    print("Vector Config: {}".format(VECTOR_CONFIG))
    print("Raster Config: {}".format(RASTER_CONFIG))
    print("=" * 60)

if __name__ == '__main__':
    print_config()
