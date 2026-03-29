# ArcGIS Python 2.7 vs Python 3.x Performance Comparison

*Generated on 2026-03-29 19:37:13*

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 12 |
| Python 3.x Faster | 4 (33.3%) |
| Python 2.7 Faster | 7 (58.3%) |
| Equal Performance | 1 (8.3%) |
| Average Speedup | 0.88x |
| Median Speedup | 0.87x |
| Max Speedup | 1.46x |
| Min Speedup | 0.12x |

## Detailed Results

| Test | Category | Python 2.7 (s) | Python 3.x (s) | Speedup | Faster |
|------|----------|----------------|----------------|---------|--------|
| M1_PolygonToRaster | mixed | 0.8910 ± 0.0000 | 0.6943 ± 0.0000 | 1.28x | Python 3.x |
| M2_RasterToPoint | mixed | 13.8439 ± 0.0000 | 9.4918 ± 0.0000 | 1.46x | Python 3.x |
| R1_CreateConstantRaster | raster | 0.1390 ± 0.0000 | 1.1947 ± 0.0000 | 0.12x | Python 2.7 |
| R2_Resample | raster | 0.2250 ± 0.0000 | 0.4096 ± 0.0000 | 0.55x | Python 2.7 |
| R3_Clip | raster | 0.2876 ± 0.0000 | 0.2878 ± 0.0000 | 1.00x | Equal |
| R4_RasterCalculator | raster | 0.4235 ± 0.0000 | 0.4864 ± 0.0000 | 0.87x | Python 2.7 |
| V1_CreateFishnet | vector | 0.5695 ± 0.0000 | 0.7305 ± 0.0000 | 0.78x | Python 2.7 |
| V2_CreateRandomPoints | vector | 0.0830 ± 0.0000 | 0.1300 ± 0.0000 | 0.64x | Python 2.7 |
| V3_Buffer | vector | 0.1687 ± 0.0000 | 0.2562 ± 0.0000 | 0.66x | Python 2.7 |
| V4_Intersect | vector | 0.3546 ± 0.0000 | 0.2827 ± 0.0000 | 1.25x | Python 3.x |
| V5_SpatialJoin | vector | 1.2703 ± 0.0000 | 1.4754 ± 0.0000 | 0.86x | Python 2.7 |
| V6_CalculateField | vector | 1.1532 ± 0.0000 | 1.0487 ± 0.0000 | 1.10x | Python 3.x |

## Notes

- **Times**: Mean ± Standard Deviation (in seconds)
- **Speedup**: Ratio of Python 2.7 time to Python 3.x time
  - Speedup > 1: Python 3.x is faster
  - Speedup < 1: Python 2.7 is faster
  - Speedup = 1: Equal performance
- **Faster**: Which Python version performed better

## Interpretation

Based on the benchmark results:
- On average, **Python 2.7 is 1.14x faster** than Python 3.x
- Python 3.x was faster in 4 out of 12 tests (33.3%)