# Benchmark Results (py3)

*Generated on 2026-03-31 08:26:56*

## Summary

| Test Name | Mean Time | Std Time | Min Time | Max Time |
|---|---|---|---|---|
| V1_CreateFishnet | 0.8713 | 0.0538 | 0.8397 | 0.9334 |
| V2_CreateRandomPoints | 0.5502 | 0.0212 | 0.5370 | 0.5747 |
| V3_Buffer | 0.7716 | 0.0384 | 0.7382 | 0.8136 |
| V4_Intersect | 0.8081 | 0.0594 | 0.7612 | 0.8750 |
| V5_SpatialJoin | 4.8600 | 0.3285 | 4.6103 | 5.2321 |
| V6_CalculateField | 3.1498 | 0.1426 | 3.0160 | 3.2998 |
| R1_CreateConstantRaster | 0.6437 | 0.0310 | 0.6085 | 0.6664 |
| R2_Resample | 1.4080 | 0.0250 | 1.3863 | 1.4354 |
| R3_Clip | 0.9198 | 0.0822 | 0.8638 | 1.0142 |
| R4_RasterCalculator | 0.6660 | 0.0138 | 0.6532 | 0.6806 |
| M1_PolygonToRaster | 2.0902 | 0.1100 | 1.9958 | 2.2111 |
| M2_RasterToPoint | 26.0003 | 0.1116 | 25.8801 | 26.1006 |
| Py3_MP_V1_CreateFishnet_single | 0.8655 | 0.0224 | 0.8405 | 0.8836 |
| Py3_MP_V1_CreateFishnet_multiprocess | 2.8973 | 0.0651 | 2.8260 | 2.9536 |
| Py3_MP_V2_CreateRandomPoints_single | 0.5263 | 0.0358 | 0.4857 | 0.5534 |
| Py3_MP_V2_CreateRandomPoints_multiprocess | 1.9793 | 0.0464 | 1.9458 | 2.0323 |
| Py3_MP_V3_Buffer_single | 1.9286 | 0.0937 | 1.8721 | 2.0367 |
| Py3_MP_V3_Buffer_multiprocess | 5.4928 | 0.1479 | 5.3277 | 5.6134 |
| Py3_MP_V4_Intersect_single | 0.9380 | 0.0379 | 0.8964 | 0.9707 |
| Py3_MP_V4_Intersect_multiprocess | 7.5330 | 0.2517 | 7.2524 | 7.7389 |
| Py3_MP_R1_CreateConstantRaster_single | 0.6066 | 0.0033 | 0.6033 | 0.6098 |
| Py3_MP_R1_CreateConstantRaster_multiprocess | 2.8935 | 0.1161 | 2.7799 | 3.0120 |

## Detailed Results

### V1_CreateFishnet

- **all_times**: [0.9334294000000227, 0.8397399999957997, 0.8408282000164036]
- **avg_memory_mb**: 0.0
- **category**: vector
- **cv_percent**: 6.172180470263324
- **failed_runs**: 0
- **max_time**: 0.9334294000000227
- **mean_time**: 0.8713325333374087
- **min_time**: 0.8397399999957997
- **python_version**: 3.13.7
- **std_time**: 0.053780216453702206
- **success**: True
- **successful_runs**: 3
- **test_name**: V1_CreateFishnet
- **total_runs**: 3

### V2_CreateRandomPoints

- **all_times**: [0.5388787999982014, 0.5746653999958653, 0.5370058999978937]
- **avg_memory_mb**: 0.0
- **category**: vector
- **cv_percent**: 3.8573927373142194
- **failed_runs**: 0
- **max_time**: 0.5746653999958653
- **mean_time**: 0.5501833666639868
- **min_time**: 0.5370058999978937
- **python_version**: 3.13.7
- **std_time**: 0.02122273322760749
- **success**: True
- **successful_runs**: 3
- **test_name**: V2_CreateRandomPoints
- **total_runs**: 3

### V3_Buffer

- **all_times**: [0.8135736999975052, 0.7381515000015497, 0.763013999996474]
- **avg_memory_mb**: 0.0
- **category**: vector
- **cv_percent**: 4.98118137457707
- **failed_runs**: 0
- **max_time**: 0.8135736999975052
- **mean_time**: 0.7715797333318429
- **min_time**: 0.7381515000015497
- **python_version**: 3.13.7
- **std_time**: 0.03843378596673718
- **success**: True
- **successful_runs**: 3
- **test_name**: V3_Buffer
- **total_runs**: 3

### V4_Intersect

- **all_times**: [0.8749631000100635, 0.7881206999882124, 0.7612275000137743]
- **avg_memory_mb**: 0.0
- **category**: vector
- **cv_percent**: 7.355829621825655
- **failed_runs**: 0
- **max_time**: 0.8749631000100635
- **mean_time**: 0.8081037666706834
- **min_time**: 0.7612275000137743
- **python_version**: 3.13.7
- **std_time**: 0.059442736243851005
- **success**: True
- **successful_runs**: 3
- **test_name**: V4_Intersect
- **total_runs**: 3

### V5_SpatialJoin

- **all_times**: [5.232091999991098, 4.737769700004719, 4.610251500009326]
- **avg_memory_mb**: 0.0
- **category**: vector
- **cv_percent**: 6.758306508651561
- **failed_runs**: 0
- **max_time**: 5.232091999991098
- **mean_time**: 4.860037733335048
- **min_time**: 4.610251500009326
- **python_version**: 3.13.7
- **std_time**: 0.32845624645490434
- **success**: True
- **successful_runs**: 3
- **test_name**: V5_SpatialJoin
- **total_runs**: 3

### V6_CalculateField

- **all_times**: [3.299846800015075, 3.133572800026741, 3.0159633999865036]
- **avg_memory_mb**: 0.0
- **category**: vector
- **cv_percent**: 4.528397198728863
- **failed_runs**: 0
- **max_time**: 3.299846800015075
- **mean_time**: 3.1497943333427734
- **min_time**: 3.0159633999865036
- **python_version**: 3.13.7
- **std_time**: 0.1426351983568146
- **success**: True
- **successful_runs**: 3
- **test_name**: V6_CalculateField
- **total_runs**: 3

### R1_CreateConstantRaster

- **all_times**: [0.6084643000212964, 0.6664311999920756, 0.6563509999832604]
- **avg_memory_mb**: 0.0
- **category**: raster
- **cv_percent**: 4.810908653295342
- **failed_runs**: 0
- **max_time**: 0.6664311999920756
- **mean_time**: 0.6437488333322108
- **min_time**: 0.6084643000212964
- **python_version**: 3.13.7
- **std_time**: 0.030970168328267135
- **success**: True
- **successful_runs**: 3
- **test_name**: R1_CreateConstantRaster
- **total_runs**: 3

### R2_Resample

- **all_times**: [1.3863307999854442, 1.4354414000117686, 1.4023511999985203]
- **avg_memory_mb**: 0.0
- **category**: raster
- **cv_percent**: 1.7787012382179483
- **failed_runs**: 0
- **max_time**: 1.4354414000117686
- **mean_time**: 1.408041133331911
- **min_time**: 1.3863307999854442
- **python_version**: 3.13.7
- **std_time**: 0.025044845073192733
- **success**: True
- **successful_runs**: 3
- **test_name**: R2_Resample
- **total_runs**: 3

### R3_Clip

- **all_times**: [1.0141503999766428, 0.8638029999856371, 0.8813185000035446]
- **avg_memory_mb**: 0.0
- **category**: raster
- **cv_percent**: 8.938728120639455
- **failed_runs**: 0
- **max_time**: 1.0141503999766428
- **mean_time**: 0.9197572999886082
- **min_time**: 0.8638029999856371
- **python_version**: 3.13.7
- **std_time**: 0.08221460441571592
- **success**: True
- **successful_runs**: 3
- **test_name**: R3_Clip
- **total_runs**: 3

### R4_RasterCalculator

- **all_times**: [0.6532133000146132, 0.6806107000156771, 0.6641006999998353]
- **avg_memory_mb**: 0.0
- **category**: raster
- **cv_percent**: 2.0713276879281257
- **failed_runs**: 0
- **max_time**: 0.6806107000156771
- **mean_time**: 0.6659749000100419
- **min_time**: 0.6532133000146132
- **python_version**: 3.13.7
- **std_time**: 0.013794522498559648
- **success**: True
- **successful_runs**: 3
- **test_name**: R4_RasterCalculator
- **total_runs**: 3

### M1_PolygonToRaster

- **all_times**: [2.063664399989648, 2.2110594999976456, 1.9958496000035666]
- **avg_memory_mb**: 0.0
- **category**: mixed
- **cv_percent**: 5.264106671414941
- **failed_runs**: 0
- **max_time**: 2.2110594999976456
- **mean_time**: 2.09019116666362
- **min_time**: 1.9958496000035666
- **python_version**: 3.13.7
- **std_time**: 0.11002989264966542
- **success**: True
- **successful_runs**: 3
- **test_name**: M1_PolygonToRaster
- **total_runs**: 3

### M2_RasterToPoint

- **all_times**: [26.100558099977206, 26.020121799985645, 25.880111700011184]
- **avg_memory_mb**: 0.0
- **category**: mixed
- **cv_percent**: 0.4290600424817611
- **failed_runs**: 0
- **max_time**: 26.100558099977206
- **mean_time**: 26.000263866658013
- **min_time**: 25.880111700011184
- **python_version**: 3.13.7
- **std_time**: 0.11155674319165285
- **success**: True
- **successful_runs**: 3
- **test_name**: M2_RasterToPoint
- **total_runs**: 3

### Py3_MP_V1_CreateFishnet_single

- **all_times**: [0.8404994999873452, 0.8835547000053339, 0.872579399991082]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 2.5848556747441758
- **failed_runs**: 0
- **max_time**: 0.8835547000053339
- **mean_time**: 0.8655445333279204
- **min_time**: 0.8404994999873452
- **python_version**: 3.13.7
- **std_time**: 0.022373076987164744
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V1_CreateFishnet_single
- **total_runs**: 3

### Py3_MP_V1_CreateFishnet_multiprocess

- **all_times**: [2.9121747000026517, 2.8260295999934897, 2.953573699982371]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 2.2458149925420825
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 2.953573699982371
- **mean_time**: 2.8972593333261707
- **min_time**: 2.8260295999934897
- **num_workers**: 4
- **parallel_efficiency**: 7.468649107208504
- **python_version**: 3.13.7
- **speedup_vs_single**: 0.29874596428834016
- **std_time**: 0.06506708448066392
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V1_CreateFishnet_multiprocess
- **total_runs**: 3

### Py3_MP_V2_CreateRandomPoints_single

- **all_times**: [0.4857377999869641, 0.5533624999807216, 0.5396771999949124]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 6.793882527903178
- **failed_runs**: 0
- **max_time**: 0.5533624999807216
- **mean_time**: 0.5262591666541994
- **min_time**: 0.4857377999869641
- **python_version**: 3.13.7
- **std_time**: 0.035753429574808517
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V2_CreateRandomPoints_single
- **total_runs**: 3

### Py3_MP_V2_CreateRandomPoints_multiprocess

- **all_times**: [1.9596788999915589, 2.0322600999788847, 1.9458262999833096]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 2.3454926256785082
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 2.0322600999788847
- **mean_time**: 1.9792550999845844
- **min_time**: 1.9458262999833096
- **num_workers**: 4
- **parallel_efficiency**: 6.6471872001024295
- **python_version**: 3.13.7
- **speedup_vs_single**: 0.26588748800409717
- **std_time**: 0.046423282413504206
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V2_CreateRandomPoints_multiprocess
- **total_runs**: 3

### Py3_MP_V3_Buffer_single

- **all_times**: [1.8768225999956485, 2.0367497999977786, 1.8721367999969516]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 4.859351214130996
- **failed_runs**: 0
- **max_time**: 2.0367497999977786
- **mean_time**: 1.9285697333301262
- **min_time**: 1.8721367999969516
- **python_version**: 3.13.7
- **std_time**: 0.09371597675194039
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V3_Buffer_single
- **total_runs**: 3

### Py3_MP_V3_Buffer_multiprocess

- **all_times**: [5.327728700009175, 5.613437099993462, 5.537150300020585]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 2.6932440017391603
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 5.613437099993462
- **mean_time**: 5.4927720333410734
- **min_time**: 5.327728700009175
- **num_workers**: 4
- **parallel_efficiency**: 8.777761582056048
- **python_version**: 3.13.7
- **speedup_vs_single**: 0.3511104632822419
- **std_time**: 0.14793375331716457
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V3_Buffer_multiprocess
- **total_runs**: 3

### Py3_MP_V4_Intersect_single

- **all_times**: [0.9706702999828849, 0.8964396999799646, 0.9469287999963854]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 4.041517745494345
- **failed_runs**: 0
- **max_time**: 0.9706702999828849
- **mean_time**: 0.938012933319745
- **min_time**: 0.8964396999799646
- **python_version**: 3.13.7
- **std_time**: 0.03790995915514953
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V4_Intersect_single
- **total_runs**: 3

### Py3_MP_V4_Intersect_multiprocess

- **all_times**: [7.252362999977777, 7.607645799987949, 7.738941599993268]
- **avg_memory_mb**: 0.0
- **category**: vector_multiprocess
- **cv_percent**: 3.341770805630853
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 7.738941599993268
- **mean_time**: 7.532983466652998
- **min_time**: 7.252362999977777
- **num_workers**: 4
- **parallel_efficiency**: 3.1130193550541416
- **python_version**: 3.13.7
- **speedup_vs_single**: 0.12452077420216566
- **std_time**: 0.25173504228160887
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_V4_Intersect_multiprocess
- **total_runs**: 3

### Py3_MP_R1_CreateConstantRaster_single

- **all_times**: [0.603259600000456, 0.6098432999860961, 0.6066619999764953]
- **avg_memory_mb**: 0.0
- **category**: raster_multiprocess
- **cv_percent**: 0.5427847355810678
- **failed_runs**: 0
- **max_time**: 0.6098432999860961
- **mean_time**: 0.6065882999876825
- **min_time**: 0.603259600000456
- **python_version**: 3.13.7
- **std_time**: 0.003292468700153837
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_R1_CreateConstantRaster_single
- **total_runs**: 3

### Py3_MP_R1_CreateConstantRaster_multiprocess

- **all_times**: [2.888580400001956, 3.012024899973767, 2.779896899999585]
- **avg_memory_mb**: 0.0
- **category**: raster_multiprocess
- **cv_percent**: 4.01389891505045
- **execution_mode**: multiprocess
- **failed_runs**: 0
- **max_time**: 3.012024899973767
- **mean_time**: 2.893500733325103
- **min_time**: 2.779896899999585
- **num_workers**: 4
- **parallel_efficiency**: 5.240955125753622
- **python_version**: 3.13.7
- **speedup_vs_single**: 0.20963820503014488
- **std_time**: 0.11614219454191312
- **success**: True
- **successful_runs**: 3
- **test_name**: Py3_MP_R1_CreateConstantRaster_multiprocess
- **total_runs**: 3
