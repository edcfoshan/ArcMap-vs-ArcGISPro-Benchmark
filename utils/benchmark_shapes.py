# -*- coding: utf-8 -*-
"""
Helpers for deterministic synthetic benchmark shapes and expected counts.
Compatible with Python 2.7 and 3.x.
"""
from __future__ import print_function, division, absolute_import

import math

try:
    import numpy as np
except ImportError:
    np = None


def factor_grid_dimensions(total_count):
    """Return exact integer grid dimensions whose product equals total_count.

    The returned pair is chosen to be as square as possible while still
    multiplying to the requested count. If no better factor exists, it falls
    back to ``1 x total_count``.
    """
    total_count = int(total_count or 0)
    if total_count <= 0:
        raise ValueError("total_count must be positive")

    root = int(math.sqrt(total_count))
    for rows in range(root, 0, -1):
        if total_count % rows == 0:
            cols = total_count // rows
            return rows, cols

    return 1, total_count


def expected_offset_grid_intersections(rows_a, cols_a, rows_b, cols_b):
    """Return expected intersect output count for two half-cell offset grids."""
    rows_a = int(rows_a or 0)
    cols_a = int(cols_a or 0)
    rows_b = int(rows_b or 0)
    cols_b = int(cols_b or 0)

    if rows_a <= 0 or cols_a <= 0 or rows_b <= 0 or cols_b <= 0:
        return 0

    return (rows_a + rows_b - 1) * (cols_a + cols_b - 1)


def derive_group_count(total_count, divisor=2500, min_groups=4, max_groups=64):
    """Return a deterministic grouping count for large synthetic datasets.

    The helper keeps the number of groups stable across ArcPy and open-source
    benchmark paths while ensuring that larger datasets get more aggregation
    work than smaller ones.
    """
    total_count = int(total_count or 0)
    if total_count <= 0:
        raise ValueError("total_count must be positive")

    divisor = max(1, int(divisor))
    min_groups = max(1, int(min_groups))
    max_groups = max(min_groups, int(max_groups))

    group_count = total_count // divisor
    if group_count < min_groups:
        group_count = min_groups
    if group_count > max_groups:
        group_count = max_groups
    if group_count > total_count:
        group_count = total_count

    return max(1, group_count)


def derive_block_size(total_size, target_blocks_per_side=50, min_block_size=8):
    """Return a stable block size for patterned raster generation.

    The returned size is chosen so the raster contains roughly
    ``target_blocks_per_side`` blocks in each direction. This keeps the raster
    polygonization benchmarks realistic without exploding the polygon count.
    """
    total_size = int(total_size or 0)
    if total_size <= 0:
        raise ValueError("total_size must be positive")

    target_blocks_per_side = max(1, int(target_blocks_per_side))
    min_block_size = max(1, int(min_block_size))

    block_size = total_size // target_blocks_per_side
    if block_size < min_block_size:
        block_size = min_block_size
    if block_size > total_size:
        block_size = total_size

    return max(1, block_size)


def expected_block_pattern_region_count(total_size, block_size):
    """Return the expected number of contiguous regions in a block raster."""
    total_size = int(total_size or 0)
    block_size = int(block_size or 0)
    if total_size <= 0 or block_size <= 0:
        return 0

    blocks_per_side = int(math.ceil(float(total_size) / float(block_size)))
    return blocks_per_side * blocks_per_side


def build_block_pattern_array(height, width=None, block_size=8, levels=6):
    """Return a deterministic integer raster with repeating block regions."""
    if np is None:
        raise RuntimeError("NumPy is required to build patterned benchmark rasters")

    height = int(height or 0)
    width = int(width if width is not None else height)
    block_size = max(1, int(block_size or 1))
    levels = max(2, int(levels or 2))

    if height <= 0 or width <= 0:
        raise ValueError("height and width must be positive")

    array = np.zeros((height, width), dtype=np.int16)
    for row_start in range(0, height, block_size):
        row_block = row_start // block_size
        row_end = min(height, row_start + block_size)
        for col_start in range(0, width, block_size):
            col_block = col_start // block_size
            col_end = min(width, col_start + block_size)
            value = 1 + ((row_block * 3 + col_block * 5) % levels)
            array[row_start:row_end, col_start:col_end] = value

    return array
