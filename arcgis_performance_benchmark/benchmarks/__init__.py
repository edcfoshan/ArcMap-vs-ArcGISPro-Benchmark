# -*- coding: utf-8 -*-
"""
ArcGIS Performance Benchmark - Benchmarks Module
"""
from __future__ import absolute_import

# Import base class
from .base_benchmark import BaseBenchmark, BenchmarkSuite

# Import benchmark collections
try:
    from .vector_benchmarks import VectorBenchmarks
except ImportError:
    VectorBenchmarks = None

try:
    from .raster_benchmarks import RasterBenchmarks
except ImportError:
    RasterBenchmarks = None

try:
    from .mixed_benchmarks import MixedBenchmarks
except ImportError:
    MixedBenchmarks = None


def get_all_benchmarks():
    """Get all available benchmarks"""
    all_benchmarks = []
    
    if VectorBenchmarks:
        all_benchmarks.extend(VectorBenchmarks.get_all_benchmarks())
    
    if RasterBenchmarks:
        all_benchmarks.extend(RasterBenchmarks.get_all_benchmarks())
    
    if MixedBenchmarks:
        all_benchmarks.extend(MixedBenchmarks.get_all_benchmarks())
    
    return all_benchmarks


def get_benchmarks_by_category(category):
    """Get benchmarks by category"""
    if category == 'vector' and VectorBenchmarks:
        return VectorBenchmarks.get_all_benchmarks()
    elif category == 'raster' and RasterBenchmarks:
        return RasterBenchmarks.get_all_benchmarks()
    elif category == 'mixed' and MixedBenchmarks:
        return MixedBenchmarks.get_all_benchmarks()
    elif category == 'all':
        return get_all_benchmarks()
    else:
        return []
