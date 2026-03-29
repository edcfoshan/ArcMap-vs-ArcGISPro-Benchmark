# Benchmark Results (py2)

*Generated on 2026-03-29 18:55:00*

## Summary

| Test Name | Mean Time | Std Time | Min Time | Max Time |
|---|---|---|---|---|
| V1_CreateFishnet | 0.6561 | 0 | 0.6561 | 0.6561 |
| V2_CreateRandomPoints | 0.1006 | 0 | 0.1006 | 0.1006 |
| V3_Buffer | 0.1964 | 0 | 0.1964 | 0.1964 |
| V4_Intersect | 0.6725 | 0 | 0.6725 | 0.6725 |
| V5_SpatialJoin |  |  |  |  |
| V6_CalculateField | 1.7982 | 0 | 1.7982 | 1.7982 |
| R1_CreateConstantRaster | 0.1830 | 0 | 0.1830 | 0.1830 |
| R2_Resample | 0.2555 | 0 | 0.2555 | 0.2555 |
| R3_Clip | 0.3032 | 0 | 0.3032 | 0.3032 |
| R4_RasterCalculator | 0.4127 | 0 | 0.4127 | 0.4127 |
| M1_PolygonToRaster | 1.0429 | 0 | 1.0429 | 1.0429 |
| M2_RasterToPoint | 16.0478 | 0 | 16.0478 | 16.0478 |

## Detailed Results

### V1_CreateFishnet

- **all_times**: [0.6560745]
- **avg_memory_mb**: 196.0859375
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.6560745
- **mean_time**: 0.6560745
- **min_time**: 0.6560745
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V1_CreateFishnet
- **total_runs**: 1

### V2_CreateRandomPoints

- **all_times**: [0.10061000000000009]
- **avg_memory_mb**: 198.4296875
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.10061
- **mean_time**: 0.10061
- **min_time**: 0.10061
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V2_CreateRandomPoints
- **total_runs**: 1

### V3_Buffer

- **all_times**: [0.19641409999999992]
- **avg_memory_mb**: 199.0390625
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.1964141
- **mean_time**: 0.1964141
- **min_time**: 0.1964141
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V3_Buffer
- **total_runs**: 1

### V4_Intersect

- **all_times**: [0.6724549999999998]
- **avg_memory_mb**: 205.26953125
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.672455
- **mean_time**: 0.672455
- **min_time**: 0.672455
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V4_Intersect
- **total_runs**: 1

### V5_SpatialJoin

- **category**: vector
- **error**: All runs failed
- **success**: False
- **successful_runs**: 0
- **test_name**: V5_SpatialJoin
- **total_runs**: 1

### V6_CalculateField

- **all_times**: [1.7982023000000007]
- **avg_memory_mb**: 237.07421875
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 1.7982023
- **mean_time**: 1.7982023
- **min_time**: 1.7982023
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V6_CalculateField
- **total_runs**: 1

### R1_CreateConstantRaster

- **all_times**: [0.18297729999999923]
- **avg_memory_mb**: 237.35546875
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.1829773
- **mean_time**: 0.1829773
- **min_time**: 0.1829773
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R1_CreateConstantRaster
- **total_runs**: 1

### R2_Resample

- **all_times**: [0.2555100000000001]
- **avg_memory_mb**: 243.08203125
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.25551
- **mean_time**: 0.25551
- **min_time**: 0.25551
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R2_Resample
- **total_runs**: 1

### R3_Clip

- **all_times**: [0.30321320000000007]
- **avg_memory_mb**: 243.99609375
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.3032132
- **mean_time**: 0.3032132
- **min_time**: 0.3032132
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R3_Clip
- **total_runs**: 1

### R4_RasterCalculator

- **all_times**: [0.41265710000000055]
- **avg_memory_mb**: 244.0234375
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.4126571
- **mean_time**: 0.4126571
- **min_time**: 0.4126571
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R4_RasterCalculator
- **total_runs**: 1

### M1_PolygonToRaster

- **all_times**: [1.0428588999999988]
- **avg_memory_mb**: 245.12109375
- **category**: mixed
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 1.0428589
- **mean_time**: 1.0428589
- **min_time**: 1.0428589
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: M1_PolygonToRaster
- **total_runs**: 1

### M2_RasterToPoint

- **all_times**: [16.0478199]
- **avg_memory_mb**: 246.484375
- **category**: mixed
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 16.0478199
- **mean_time**: 16.0478199
- **min_time**: 16.0478199
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: M2_RasterToPoint
- **total_runs**: 1
