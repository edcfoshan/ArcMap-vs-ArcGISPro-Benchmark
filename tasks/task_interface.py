# -*- coding: utf-8 -*-
"""
Task adapter factory for the 6-core benchmark matrix.
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks.task_specs import CORE_TASK_IDS, LEGACY_BENCHMARK_NAMES, LEGACY_BENCHMARK_NAMES_OS


def _import_arcpy_benchmarks():
    """Import ArcGIS-based benchmark classes."""
    try:
        from benchmarks.vector_benchmarks import VectorBenchmarks
        from benchmarks.raster_benchmarks import RasterBenchmarks
        from benchmarks.mixed_benchmarks import MixedBenchmarks
        return True
    except ImportError:
        return False


def _import_os_benchmarks():
    """Import open-source benchmark classes."""
    try:
        from benchmarks.vector_benchmarks_os import VectorBenchmarksOS
        from benchmarks.raster_benchmarks_os import RasterBenchmarksOS
        from benchmarks.mixed_benchmarks_os import MixedBenchmarksOS
        return True
    except Exception:
        return False


def _find_benchmark_class(name, is_os=False):
    """Find a benchmark class by its legacy name."""
    if is_os:
        try:
            from benchmarks.vector_benchmarks_os import VectorBenchmarksOS
            from benchmarks.raster_benchmarks_os import RasterBenchmarksOS
            from benchmarks.mixed_benchmarks_os import MixedBenchmarksOS
            factories = [VectorBenchmarksOS, RasterBenchmarksOS, MixedBenchmarksOS]
            for factory in factories:
                for bm in factory.get_all_benchmarks():
                    if bm.__class__.__name__ == name:
                        return bm.__class__
        except Exception:
            pass
    else:
        try:
            from benchmarks.vector_benchmarks import VectorBenchmarks
            from benchmarks.raster_benchmarks import RasterBenchmarks
            from benchmarks.mixed_benchmarks import MixedBenchmarks
            factories = [VectorBenchmarks, RasterBenchmarks, MixedBenchmarks]
            for factory in factories:
                for bm in factory.get_all_benchmarks():
                    if bm.__class__.__name__ == name:
                        return bm.__class__
        except Exception:
            pass
    return None


_BENCHMARK_REGISTRY = {}

def _build_registry():
    """Build the registry mapping (task_id, stack) -> benchmark class."""
    global _BENCHMARK_REGISTRY
    if _BENCHMARK_REGISTRY:
        return

    has_arcpy = _import_arcpy_benchmarks()
    has_os = _import_os_benchmarks()

    for task_id in CORE_TASK_IDS:
        if has_arcpy:
            legacy_name = LEGACY_BENCHMARK_NAMES.get(task_id)
            cls = _find_benchmark_class(legacy_name, is_os=False)
            if cls:
                _BENCHMARK_REGISTRY[(task_id, "arcpy_desktop")] = cls
                _BENCHMARK_REGISTRY[(task_id, "arcpy_pro")] = cls
        if has_os:
            legacy_name_os = LEGACY_BENCHMARK_NAMES_OS.get(task_id)
            cls_os = _find_benchmark_class(legacy_name_os, is_os=True)
            if cls_os:
                _BENCHMARK_REGISTRY[(task_id, "oss")] = cls_os


def get_benchmark_class(task_id, stack):
    """
    Return the benchmark class for a given task and stack.

    Args:
        task_id: str, one of CORE_TASK_IDS
        stack: str, one of 'arcpy_desktop', 'arcpy_pro', 'oss'

    Returns:
        benchmark class or None
    """
    _build_registry()
    return _BENCHMARK_REGISTRY.get((task_id, stack))


def get_all_benchmarks_for_stack(stack, output_format="SHP"):
    """
    Return a list of instantiated benchmarks for a given stack.

    Args:
        stack: str, one of 'arcpy_desktop', 'arcpy_pro', 'oss'
        output_format: str, one of 'SHP', 'GPKG', 'GDB'

    Returns:
        list of benchmark instances
    """
    _build_registry()
    benchmarks = []
    for task_id in CORE_TASK_IDS:
        cls = _BENCHMARK_REGISTRY.get((task_id, stack))
        if cls:
            try:
                instance = cls(output_format=output_format)
            except TypeError:
                # Fallback for legacy classes that don't accept output_format yet
                instance = cls()
            benchmarks.append(instance)
    return benchmarks


def list_available_stacks():
    """Return available stacks based on importable modules."""
    stacks = []
    if _import_arcpy_benchmarks():
        stacks.extend(["arcpy_desktop", "arcpy_pro"])
    if _import_os_benchmarks():
        stacks.append("oss")
    return stacks
