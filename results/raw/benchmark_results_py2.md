# Benchmark Results (py2)

*Generated on 2026-03-31 08:21:54*

## Summary

| Test Name | Mean Time | Std Time | Min Time | Max Time |
|---|---|---|---|---|
| V1_CreateFishnet | 0.6263 | 0.0299 | 0.5930 | 0.6509 |
| V2_CreateRandomPoints | 0.2580 | 0.0085 | 0.2512 | 0.2675 |
| V3_Buffer | 0.5125 | 0.0069 | 0.5056 | 0.5194 |
| V4_Intersect | 0.8775 | 0.0788 | 0.8110 | 0.9645 |
| V5_SpatialJoin | 2.2257 | 0.0232 | 2.2068 | 2.2516 |
| V6_CalculateField | 3.1588 | 0.0306 | 3.1306 | 3.1914 |
| R1_CreateConstantRaster | 0.2732 | 0.0356 | 0.2472 | 0.3137 |
| R2_Resample | 0.6217 | 0.0517 | 0.5631 | 0.6611 |
| R3_Clip | 0.6948 | 0.0423 | 0.6687 | 0.7437 |
| R4_RasterCalculator | 0.8076 | 0.0176 | 0.7957 | 0.8279 |
| M1_PolygonToRaster | 2.5503 | 0.0266 | 2.5206 | 2.5720 |
| M2_RasterToPoint | 32.8054 | 0.1157 | 32.6973 | 32.9275 |
| Py2_MP_V1_CreateFishnet_single | 0.6243 | 0.0498 | 0.5760 | 0.6755 |
| Py2_MP_V1_CreateFishnet_multiprocess | 2.2641 | 0.0707 | 2.2194 | 2.3455 |
| Py2_MP_V2_CreateRandomPoints_single | 0.2574 | 0.0141 | 0.2460 | 0.2732 |
| Py2_MP_V2_CreateRandomPoints_multiprocess | 1.0582 | 0.0604 | 0.9997 | 1.1203 |
| Py2_MP_V3_Buffer_single | 8.3303 | 0.0512 | 8.2754 | 8.3766 |
| Py2_MP_V3_Buffer_multiprocess | 11.5362 | 0.3821 | 11.1215 | 11.8738 |
| Py2_MP_V4_Intersect_single | 0.8924 | 0.0528 | 0.8319 | 0.9287 |
| Py2_MP_V4_Intersect_multiprocess | 9.2045 | 0.2357 | 8.9500 | 9.4153 |
| Py2_MP_R1_CreateConstantRaster_single | 0.2869 | 0.0098 | 0.2781 | 0.2975 |
| Py2_MP_R1_CreateConstantRaster_multiprocess | 1.8841 | 0.2077 | 1.6472 | 2.0355 |

## Detailed Results

### V1_CreateFishnet

- **all_times**: [0.6508782000000002, 0.6349217, 0.5929535000000001]
- **avg_memory_mb**: 195.381510417
- **category**: vector
- **cv_percent**: 4.77762368882
- **failed_runs**: 0
- **max_time**: 0.6508782
- **mean_time**: 0.626251133333
- **min_time**: 0.5929535
- **python_version**: 2.7.16
- **std_time**: 0.0299199224976
- **success**: True
- **successful_runs**: 3
- **test_name**: V1_CreateFishnet
- **total_runs**: 3

### V2_CreateRandomPoints

- **all_times**: [0.25115029999999994, 0.26750589999999974, 0.2552820999999996]
- **avg_memory_mb**: 196.029947917
- **category**: vector
- **cv_percent**: 3.2967309793
- **failed_runs**: 0
- **max_time**: 0.2675059
- **mean_time**: 0.257979433333
- **min_time**: 0.2511503
- **python_version**: 2.7.16
- **std_time**: 0.00850488789893
- **success**: True
- **successful_runs**: 3
- **test_name**: V2_CreateRandomPoints
- **total_runs**: 3

### V3_Buffer

- **all_times**: [0.5194393999999996, 0.5124663999999992, 0.505614099999999]
- **avg_memory_mb**: 199.58984375
- **category**: vector
- **cv_percent**: 1.34880943247
- **failed_runs**: 0
- **max_time**: 0.5194394
- **mean_time**: 0.512506633333
- **min_time**: 0.5056141
- **python_version**: 2.7.16
- **std_time**: 0.00691273781243
- **success**: True
- **successful_runs**: 3
- **test_name**: V3_Buffer
- **total_runs**: 3

### V4_Intersect

- **all_times**: [0.8568543999999996, 0.8110403999999996, 0.9645291]
- **avg_memory_mb**: 202.559895833
- **category**: vector
- **cv_percent**: 8.9797024703
- **failed_runs**: 0
- **max_time**: 0.9645291
- **mean_time**: 0.877474633333
- **min_time**: 0.8110404
- **python_version**: 2.7.16
- **std_time**: 0.0787946113257
- **success**: True
- **successful_runs**: 3
- **test_name**: V4_Intersect
- **total_runs**: 3

### V5_SpatialJoin

- **all_times**: [2.2186968999999976, 2.2068233, 2.2515576999999993]
- **avg_memory_mb**: 237.111979167
- **category**: vector
- **cv_percent**: 1.04116768543
- **failed_runs**: 0
- **max_time**: 2.2515577
- **mean_time**: 2.22569263333
- **min_time**: 2.2068233
- **python_version**: 2.7.16
- **std_time**: 0.0231731924752
- **success**: True
- **successful_runs**: 3
- **test_name**: V5_SpatialJoin
- **total_runs**: 3

### V6_CalculateField

- **all_times**: [3.1545396999999937, 3.1305798000000067, 3.1914108]
- **avg_memory_mb**: 233.627604167
- **category**: vector
- **cv_percent**: 0.970070641414
- **failed_runs**: 0
- **max_time**: 3.1914108
- **mean_time**: 3.15884343333
- **min_time**: 3.1305798
- **python_version**: 2.7.16
- **std_time**: 0.030643012755
- **success**: True
- **successful_runs**: 3
- **test_name**: V6_CalculateField
- **total_runs**: 3

### R1_CreateConstantRaster

- **all_times**: [0.24719060000000326, 0.2585955999999996, 0.31372220000000084]
- **avg_memory_mb**: 239.70703125
- **category**: raster
- **cv_percent**: 13.0247543806
- **failed_runs**: 0
- **max_time**: 0.3137222
- **mean_time**: 0.273169466667
- **min_time**: 0.2471906
- **python_version**: 2.7.16
- **std_time**: 0.0355796520761
- **success**: True
- **successful_runs**: 3
- **test_name**: R1_CreateConstantRaster
- **total_runs**: 3

### R2_Resample

- **all_times**: [0.6408352999999991, 0.6610939999999985, 0.563138600000002]
- **avg_memory_mb**: 241.065104167
- **category**: raster
- **cv_percent**: 8.31737654224
- **failed_runs**: 0
- **max_time**: 0.661094
- **mean_time**: 0.6216893
- **min_time**: 0.5631386
- **python_version**: 2.7.16
- **std_time**: 0.0517082400038
- **success**: True
- **successful_runs**: 3
- **test_name**: R2_Resample
- **total_runs**: 3

### R3_Clip

- **all_times**: [0.743658400000001, 0.6721126999999996, 0.6687377999999953]
- **avg_memory_mb**: 241.125
- **category**: raster
- **cv_percent**: 6.08990041184
- **failed_runs**: 0
- **max_time**: 0.7436584
- **mean_time**: 0.6948363
- **min_time**: 0.6687378
- **python_version**: 2.7.16
- **std_time**: 0.0423148386953
- **success**: True
- **successful_runs**: 3
- **test_name**: R3_Clip
- **total_runs**: 3

### R4_RasterCalculator

- **all_times**: [0.7956635000000034, 0.827883700000001, 0.7992893000000052]
- **avg_memory_mb**: 242.82421875
- **category**: raster
- **cv_percent**: 2.18533358578
- **failed_runs**: 0
- **max_time**: 0.8278837
- **mean_time**: 0.807612166667
- **min_time**: 0.7956635
- **python_version**: 2.7.16
- **std_time**: 0.017649019921
- **success**: True
- **successful_runs**: 3
- **test_name**: R4_RasterCalculator
- **total_runs**: 3

### M1_PolygonToRaster

- **all_times**: [2.5584161999999964, 2.5720090000000084, 2.520616199999992]
- **avg_memory_mb**: 241.830729167
- **category**: mixed
- **cv_percent**: 1.04415718918
- **failed_runs**: 0
- **max_time**: 2.572009
- **mean_time**: 2.55034713333
- **min_time**: 2.5206162
- **python_version**: 2.7.16
- **std_time**: 0.0266296329418
- **success**: True
- **successful_runs**: 3
- **test_name**: M1_PolygonToRaster
- **total_runs**: 3

### M2_RasterToPoint

- **all_times**: [32.927510699999985, 32.79146369999998, 32.69732959999999]
- **avg_memory_mb**: 245.125
- **category**: mixed
- **cv_percent**: 0.352761014065
- **failed_runs**: 0
- **max_time**: 32.9275107
- **mean_time**: 32.8054346667
- **min_time**: 32.6973296
- **python_version**: 2.7.16
- **std_time**: 0.115724783999
- **success**: True
- **successful_runs**: 3
- **test_name**: M2_RasterToPoint
- **total_runs**: 3

### Py2_MP_V1_CreateFishnet_single

- **all_times**: [0.6215004000000022, 0.5759544999999946, 0.6754795000000229]
- **avg_memory_mb**: 245.47265625
- **category**: vector_multiprocess
- **cv_percent**: 7.98031361706
- **failed_runs**: 0
- **max_time**: 0.6754795
- **mean_time**: 0.624311466667
- **min_time**: 0.5759545
- **python_version**: 2.7.16
- **std_time**: 0.0498220129873
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V1_CreateFishnet_single
- **total_runs**: 3

### Py2_MP_V1_CreateFishnet_multiprocess

- **all_times**: [2.345545699999974, 2.2272873000000004, 2.2194359000000077]
- **avg_memory_mb**: 246.6953125
- **category**: vector_multiprocess
- **cv_percent**: 3.12055537085
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 2.3455457
- **mean_time**: 2.26408963333
- **min_time**: 2.2194359
- **num_workers**: 4
- **parallel_efficiency**: 6.89362578092
- **python_version**: 2.7.16
- **speedup_vs_single**: 0.275745031237
- **std_time**: 0.0706521706538
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V1_CreateFishnet_multiprocess
- **total_runs**: 3

### Py2_MP_V2_CreateRandomPoints_single

- **all_times**: [0.2731632999999931, 0.2531689000000199, 0.24599030000001676]
- **avg_memory_mb**: 247.858072917
- **category**: vector_multiprocess
- **cv_percent**: 5.46968189843
- **failed_runs**: 0
- **max_time**: 0.2731633
- **mean_time**: 0.257440833333
- **min_time**: 0.2459903
- **python_version**: 2.7.16
- **std_time**: 0.01408119466
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V2_CreateRandomPoints_single
- **total_runs**: 3

### Py2_MP_V2_CreateRandomPoints_multiprocess

- **all_times**: [1.1203496999999913, 1.0543998999999928, 0.9997206999999833]
- **avg_memory_mb**: 247.869791667
- **category**: vector_multiprocess
- **cv_percent**: 5.70824578951
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 1.1203497
- **mean_time**: 1.05815676667
- **min_time**: 0.9997207
- **num_workers**: 4
- **parallel_efficiency**: 6.08229426497
- **python_version**: 2.7.16
- **speedup_vs_single**: 0.243291770599
- **std_time**: 0.0604021890797
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V2_CreateRandomPoints_multiprocess
- **total_runs**: 3

### Py2_MP_V3_Buffer_single

- **all_times**: [8.33902599999999, 8.376615600000036, 8.275364299999978]
- **avg_memory_mb**: 250.799479167
- **category**: vector_multiprocess
- **cv_percent**: 0.614405687422
- **failed_runs**: 0
- **max_time**: 8.3766156
- **mean_time**: 8.3303353
- **min_time**: 8.2753643
- **python_version**: 2.7.16
- **std_time**: 0.0511820538645
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V3_Buffer_single
- **total_runs**: 3

### Py2_MP_V3_Buffer_multiprocess

- **all_times**: [11.121459700000003, 11.6134548, 11.873804099999973]
- **avg_memory_mb**: 257.97265625
- **category**: vector_multiprocess
- **cv_percent**: 3.31190757228
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 11.8738041
- **mean_time**: 11.5362395333
- **min_time**: 11.1214597
- **num_workers**: 4
- **parallel_efficiency**: 18.0525362618
- **python_version**: 2.7.16
- **speedup_vs_single**: 0.722101450471
- **std_time**: 0.382069590661
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V3_Buffer_multiprocess
- **total_runs**: 3

### Py2_MP_V4_Intersect_single

- **all_times**: [0.9165957999999819, 0.8319010999999819, 0.9287327999999775]
- **avg_memory_mb**: 263.764322917
- **category**: vector_multiprocess
- **cv_percent**: 5.91122677321
- **failed_runs**: 0
- **max_time**: 0.9287328
- **mean_time**: 0.8924099
- **min_time**: 0.8319011
- **python_version**: 2.7.16
- **std_time**: 0.0527523729355
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V4_Intersect_single
- **total_runs**: 3

### Py2_MP_V4_Intersect_multiprocess

- **all_times**: [8.950025899999957, 9.415303999999992, 9.248282000000017]
- **avg_memory_mb**: 265.881510417
- **category**: vector_multiprocess
- **cv_percent**: 2.56073134611
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 9.415304
- **mean_time**: 9.2045373
- **min_time**: 8.9500259
- **num_workers**: 4
- **parallel_efficiency**: 2.42383150536
- **python_version**: 2.7.16
- **speedup_vs_single**: 0.0969532602144
- **std_time**: 0.235703471906
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_V4_Intersect_multiprocess
- **total_runs**: 3

### Py2_MP_R1_CreateConstantRaster_single

- **all_times**: [0.27806609999998955, 0.28527810000002773, 0.29746350000004895]
- **avg_memory_mb**: 267.420572917
- **category**: raster_multiprocess
- **cv_percent**: 3.41692592199
- **failed_runs**: 0
- **max_time**: 0.2974635
- **mean_time**: 0.2869359
- **min_time**: 0.2780661
- **python_version**: 2.7.16
- **std_time**: 0.00980438714661
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_R1_CreateConstantRaster_single
- **total_runs**: 3

### Py2_MP_R1_CreateConstantRaster_multiprocess

- **all_times**: [1.9695742999999766, 2.0354756000000407, 1.6472475999999574]
- **avg_memory_mb**: 267.83984375
- **category**: raster_multiprocess
- **cv_percent**: 11.0264489614
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 2.0354756
- **mean_time**: 1.88409916667
- **min_time**: 1.6472476
- **num_workers**: 4
- **parallel_efficiency**: 3.80733542422
- **python_version**: 2.7.16
- **speedup_vs_single**: 0.152293416969
- **std_time**: 0.207749232994
- **success**: True
- **successful_runs**: 3
- **test_name**: Py2_MP_R1_CreateConstantRaster_multiprocess
- **total_runs**: 3
