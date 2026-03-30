#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick test for multiprocess benchmarks"""
from __future__ import print_function
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set tiny scale
import config.settings as settings
settings.DATA_SCALE = 'tiny'
settings.VECTOR_CONFIG = settings.VECTOR_CONFIG_TINY
settings.RASTER_CONFIG = settings.RASTER_CONFIG_TINY

from benchmarks.multiprocess_tests import get_multiprocess_benchmarks

print("=" * 60)
print("Testing Multiprocess Benchmarks (Tiny Scale)")
print("=" * 60)

benchmarks = get_multiprocess_benchmarks()
print("\nFound %d multiprocess benchmarks:" % len(benchmarks))
for b in benchmarks:
    print("  - %s" % b.name)

print("\n" + "=" * 60)
print("Testing MP_V1_CreateFishnet...")
print("=" * 60)

# Test single process
print("\n[1/2] Single Process:")
bench = benchmarks[0]
bench.setup()
try:
    result = bench.run_single()
    print("  Success: %s" % result)
except Exception as e:
    print("  Error: %s" % e)
bench.teardown()

# Test multiprocess
print("\n[2/2] Multiprocess (4 workers):")
bench.setup()
try:
    result = bench.run_multiprocess(4)
    print("  Success: %s" % result)
except Exception as e:
    print("  Error: %s" % e)
    import traceback
    traceback.print_exc()
bench.teardown()

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
