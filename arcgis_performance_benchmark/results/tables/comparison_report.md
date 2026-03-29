# ArcGIS Python 2.7 vs Python 3.x Performance Comparison

*Generated on 2026-03-29 17:04:37*

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 6 |
| Python 3.x Faster | 3 (50.0%) |
| Python 2.7 Faster | 2 (33.3%) |
| Equal Performance | 1 (16.7%) |
| Average Speedup | 1.12x |
| Median Speedup | 1.10x |
| Max Speedup | 1.60x |
| Min Speedup | 0.85x |

## Detailed Results

| Test | Category | Python 2.7 (s) | Python 3.x (s) | Speedup | Faster |
|------|----------|----------------|----------------|---------|--------|
| V1_CreateFishnet | vector | 0.9981 ± 0.0000 | 1.0403 ± 0.0000 | 0.96x | Equal |
| V2_CreateRandomPoints | vector | 0.3714 ± 0.0000 | 0.4366 ± 0.0000 | 0.85x | Python 2.7 |
| V3_Buffer | vector | 1.1932 ± 0.0000 | 1.0882 ± 0.0000 | 1.10x | Python 3.x |
| V4_Intersect | vector | 11.9735 ± 0.0000 | 7.4626 ± 0.0000 | 1.60x | Python 3.x |
| V5_SpatialJoin | vector | 5.1295 ± 0.0000 | 6.0290 ± 0.0000 | 0.85x | Python 2.7 |
| V6_CalculateField | vector | 9.1009 ± 0.0000 | 6.7455 ± 0.0000 | 1.35x | Python 3.x |

## Notes

- **Times**: Mean ± Standard Deviation (in seconds)
- **Speedup**: Ratio of Python 2.7 time to Python 3.x time
  - Speedup > 1: Python 3.x is faster
  - Speedup < 1: Python 2.7 is faster
  - Speedup = 1: Equal performance
- **Faster**: Which Python version performed better

## Interpretation

Based on the benchmark results:
- On average, **Python 3.x is 1.12x faster** than Python 2.7
- Python 3.x was faster in 3 out of 6 tests (50.0%)