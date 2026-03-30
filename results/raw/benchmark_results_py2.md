# Benchmark Results (py2)

*Generated on 2026-03-30 08:31:58*

## Summary

| Test Name | Mean Time | Std Time | Min Time | Max Time |
|---|---|---|---|---|
| V1_CreateFishnet | 0.6754 | 0 | 0.6754 | 0.6754 |
| V2_CreateRandomPoints | 0.0851 | 0 | 0.0851 | 0.0851 |
| V3_Buffer | 0.1787 | 0 | 0.1787 | 0.1787 |
| V4_Intersect | 0.3539 | 0 | 0.3539 | 0.3539 |
| V5_SpatialJoin | 1.0737 | 0 | 1.0737 | 1.0737 |
| V6_CalculateField | 1.1907 | 0 | 1.1907 | 1.1907 |
| R1_CreateConstantRaster | 0.1539 | 0 | 0.1539 | 0.1539 |
| R2_Resample | 0.2564 | 0 | 0.2564 | 0.2564 |
| R3_Clip | 0.3174 | 0 | 0.3174 | 0.3174 |
| R4_RasterCalculator | 0.4539 | 0 | 0.4539 | 0.4539 |
| M1_PolygonToRaster | 1.0905 | 0 | 1.0905 | 1.0905 |
| M2_RasterToPoint | 13.3960 | 0 | 13.3960 | 13.3960 |
| Py2_MP_V1_CreateFishnet_single | 0.2007 | 0 | 0.2007 | 0.2007 |
| Py2_MP_V1_CreateFishnet_multiprocess | 0.4761 | 0.3894 | 0.2007 | 0.7514 |
| Py2_MP_V2_CreateRandomPoints_single | 0.0807 | 0 | 0.0807 | 0.0807 |
| Py2_MP_V2_CreateRandomPoints_multiprocess | 0.2510 | 0.2409 | 0.0807 | 0.4213 |
| Py2_MP_V3_Buffer_single | 3.6863 | 0 | 3.6863 | 3.6863 |
| Py2_MP_V3_Buffer_multiprocess | 3.6863 | 0 | 3.6863 | 3.6863 |
| Py2_MP_V4_Intersect_single | 0.3399 | 0 | 0.3399 | 0.3399 |
| Py2_MP_V4_Intersect_multiprocess | 0.3399 | 0 | 0.3399 | 0.3399 |
| Py2_MP_R1_CreateConstantRaster_single | 0.0741 | 0 | 0.0741 | 0.0741 |
| Py2_MP_R1_CreateConstantRaster_multiprocess | 0.0741 | 0 | 0.0741 | 0.0741 |

## Detailed Results

### V1_CreateFishnet

- **all_times**: [0.6753775]
- **avg_memory_mb**: 193.8984375
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.6753775
- **mean_time**: 0.6753775
- **min_time**: 0.6753775
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V1_CreateFishnet
- **total_runs**: 1

### V2_CreateRandomPoints

- **all_times**: [0.08511650000000004]
- **avg_memory_mb**: 196.234375
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.0851165
- **mean_time**: 0.0851165
- **min_time**: 0.0851165
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V2_CreateRandomPoints
- **total_runs**: 1

### V3_Buffer

- **all_times**: [0.17873910000000004]
- **avg_memory_mb**: 196.74609375
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.1787391
- **mean_time**: 0.1787391
- **min_time**: 0.1787391
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V3_Buffer
- **total_runs**: 1

### V4_Intersect

- **all_times**: [0.3538709999999998]
- **avg_memory_mb**: 200.37890625
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.353871
- **mean_time**: 0.353871
- **min_time**: 0.353871
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V4_Intersect
- **total_runs**: 1

### V5_SpatialJoin

- **all_times**: [1.0736854999999998]
- **avg_memory_mb**: 233.49609375
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 1.0736855
- **mean_time**: 1.0736855
- **min_time**: 1.0736855
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V5_SpatialJoin
- **total_runs**: 1

### V6_CalculateField

- **all_times**: [1.1907050999999997]
- **avg_memory_mb**: 233.87890625
- **category**: vector
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 1.1907051
- **mean_time**: 1.1907051
- **min_time**: 1.1907051
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: V6_CalculateField
- **total_runs**: 1

### R1_CreateConstantRaster

- **all_times**: [0.15386070000000007]
- **avg_memory_mb**: 233.99609375
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.1538607
- **mean_time**: 0.1538607
- **min_time**: 0.1538607
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R1_CreateConstantRaster
- **total_runs**: 1

### R2_Resample

- **all_times**: [0.2564013000000003]
- **avg_memory_mb**: 240.37890625
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.2564013
- **mean_time**: 0.2564013
- **min_time**: 0.2564013
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R2_Resample
- **total_runs**: 1

### R3_Clip

- **all_times**: [0.31737140000000075]
- **avg_memory_mb**: 240.87109375
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.3173714
- **mean_time**: 0.3173714
- **min_time**: 0.3173714
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R3_Clip
- **total_runs**: 1

### R4_RasterCalculator

- **all_times**: [0.45389130000000044]
- **avg_memory_mb**: 240.89453125
- **category**: raster
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.4538913
- **mean_time**: 0.4538913
- **min_time**: 0.4538913
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: R4_RasterCalculator
- **total_runs**: 1

### M1_PolygonToRaster

- **all_times**: [1.0905257000000006]
- **avg_memory_mb**: 242.87109375
- **category**: mixed
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 1.0905257
- **mean_time**: 1.0905257
- **min_time**: 1.0905257
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: M1_PolygonToRaster
- **total_runs**: 1

### M2_RasterToPoint

- **all_times**: [13.395961900000001]
- **avg_memory_mb**: 244.84375
- **category**: mixed
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 13.3959619
- **mean_time**: 13.3959619
- **min_time**: 13.3959619
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: M2_RasterToPoint
- **total_runs**: 1

### Py2_MP_V1_CreateFishnet_single

- **all_times**: [0.20073400000000063]
- **avg_memory_mb**: 245.0234375
- **category**: vector_multiprocess
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.200734
- **mean_time**: 0.200734
- **min_time**: 0.200734
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_V1_CreateFishnet_single
- **total_runs**: 1

### Py2_MP_V1_CreateFishnet_multiprocess

- **all_times**: [0.20073400000000063, 0.7514424999999996]
- **avg_memory_mb**: 245.5234375
- **category**: vector_multiprocess
- **cv_percent**: 81.7935991504
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 0.7514425
- **mean_time**: 0.47608825
- **min_time**: 0.200734
- **num_workers**: 4
- **parallel_efficiency**: 10.5407978458
- **python_version**: 2.7.16
- **speedup_vs_single**: 0.421631913831
- **std_time**: 0.389409714807
- **success**: True
- **successful_runs**: 2
- **test_name**: Py2_MP_V1_CreateFishnet_multiprocess
- **total_runs**: 2

### Py2_MP_V2_CreateRandomPoints_single

- **all_times**: [0.08068859999999844]
- **avg_memory_mb**: 246.0234375
- **category**: vector_multiprocess
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.0806886
- **mean_time**: 0.0806886
- **min_time**: 0.0806886
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_V2_CreateRandomPoints_single
- **total_runs**: 1

### Py2_MP_V2_CreateRandomPoints_multiprocess

- **all_times**: [0.08068859999999844, 0.42132900000000006]
- **avg_memory_mb**: 246.0234375
- **category**: vector_multiprocess
- **cv_percent**: 95.9604351665
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 0.421329
- **mean_time**: 0.2510088
- **min_time**: 0.0806886
- **num_workers**: 4
- **parallel_efficiency**: 8.03643139205
- **python_version**: 2.7.16
- **speedup_vs_single**: 0.321457255682
- **std_time**: 0.240869136786
- **success**: True
- **successful_runs**: 2
- **test_name**: Py2_MP_V2_CreateRandomPoints_multiprocess
- **total_runs**: 2

### Py2_MP_V3_Buffer_single

- **all_times**: [3.6862604999999995]
- **avg_memory_mb**: 247.52734375
- **category**: vector_multiprocess
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 3.6862605
- **mean_time**: 3.6862605
- **min_time**: 3.6862605
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_V3_Buffer_single
- **total_runs**: 1

### Py2_MP_V3_Buffer_multiprocess

- **all_times**: [3.6862604999999995]
- **avg_memory_mb**: 247.52734375
- **category**: vector_multiprocess
- **cv_percent**: 0.0
- **execution_mode**: multiprocess
- **failed_runs**: 1
- **max_time**: 3.6862605
- **mean_time**: 3.6862605
- **min_time**: 3.6862605
- **num_workers**: 4
- **parallel_efficiency**: 25.0
- **python_version**: 2.7.16
- **speedup_vs_single**: 1.0
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_V3_Buffer_multiprocess
- **total_runs**: 2

### Py2_MP_V4_Intersect_single

- **all_times**: [0.33987319999999954]
- **avg_memory_mb**: 247.5625
- **category**: vector_multiprocess
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.3398732
- **mean_time**: 0.3398732
- **min_time**: 0.3398732
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_V4_Intersect_single
- **total_runs**: 1

### Py2_MP_V4_Intersect_multiprocess

- **all_times**: [0.33987319999999954]
- **avg_memory_mb**: 247.5625
- **category**: vector_multiprocess
- **cv_percent**: 0.0
- **execution_mode**: multiprocess
- **failed_runs**: 1
- **max_time**: 0.3398732
- **mean_time**: 0.3398732
- **min_time**: 0.3398732
- **num_workers**: 4
- **parallel_efficiency**: 25.0
- **python_version**: 2.7.16
- **speedup_vs_single**: 1.0
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_V4_Intersect_multiprocess
- **total_runs**: 2

### Py2_MP_R1_CreateConstantRaster_single

- **all_times**: [0.07408990000000415]
- **avg_memory_mb**: 245.36328125
- **category**: raster_multiprocess
- **cv_percent**: 0.0
- **failed_runs**: 0
- **max_time**: 0.0740899
- **mean_time**: 0.0740899
- **min_time**: 0.0740899
- **python_version**: 2.7.16
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_R1_CreateConstantRaster_single
- **total_runs**: 1

### Py2_MP_R1_CreateConstantRaster_multiprocess

- **all_times**: [0.07408990000000415]
- **avg_memory_mb**: 245.36328125
- **category**: raster_multiprocess
- **cv_percent**: 0.0
- **execution_mode**: multiprocess
- **failed_runs**: 1
- **max_time**: 0.0740899
- **mean_time**: 0.0740899
- **min_time**: 0.0740899
- **num_workers**: 4
- **parallel_efficiency**: 25.0
- **python_version**: 2.7.16
- **speedup_vs_single**: 1.0
- **std_time**: 0
- **success**: True
- **successful_runs**: 1
- **test_name**: Py2_MP_R1_CreateConstantRaster_multiprocess
- **total_runs**: 2
