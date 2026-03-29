# -*- coding: utf-8 -*-
"""
ArcMap Python 窗口测试脚本
在 ArcMap 的 Python 窗口中执行此脚本
"""
import arcpy
import time
import json
import sys
import os

# 添加项目路径（根据实际情况修改）
project_path = r"D:\测试arcmap与gispro的运行速度\arcgis_performance_benchmark"
sys.path.insert(0, project_path)

from benchmarks.vector_benchmarks import VectorBenchmarks
from benchmarks.raster_benchmarks import RasterBenchmarks
from benchmarks.mixed_benchmarks import MixedBenchmarks
from config import settings

# 输出文件路径
output_file = os.path.join(project_path, "results", "raw", "benchmark_results_arcmap.json")

# 确保输出目录存在
output_dir = os.path.dirname(output_file)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 测试结果列表
results = []

print("=" * 60)
print("ArcMap Python 窗口性能测试")
print("=" * 60)
print("ArcGIS Version: {}".format(arcpy.GetInstallInfo()['Version']))
print("Python Version: {}.{}.{}".format(
    sys.version_info[0],
    sys.version_info[1],
    sys.version_info[2]
))
print("=" * 60)

# 获取所有测试
all_benchmarks = []
all_benchmarks.extend(VectorBenchmarks.get_all_benchmarks())
all_benchmarks.extend(RasterBenchmarks.get_all_benchmarks())
all_benchmarks.extend(MixedBenchmarks.get_all_benchmarks())

total = len(all_benchmarks)

print("\n总共 {} 项测试\n".format(total))

# 运行每个测试
for i, bm in enumerate(all_benchmarks, 1):
    print("[{}/{}] {}".format(i, total, bm.name))
    
    try:
        # 预热（可选）
        if settings.WARMUP_RUNS > 0:
            print("  Warmup...")
            bm.setup()
            bm.run_single()
            bm.teardown()
        
        # 正式测试
        times = []
        for run in range(settings.TEST_RUNS):
            bm.setup()
            start = time.time()
            bm.run_single()
            elapsed = time.time() - start
            bm.teardown()
            times.append(elapsed)
        
        # 计算统计
        mean_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        if len(times) > 1:
            variance = sum((t - mean_time) ** 2 for t in times) / (len(times) - 1)
            std_time = variance ** 0.5
        else:
            std_time = 0
        
        results.append({
            'test_name': bm.name,
            'category': bm.category,
            'success': True,
            'mean_time': mean_time,
            'std_time': std_time,
            'min_time': min_time,
            'max_time': max_time,
            'python_version': '{}.{}.{}'.format(
                sys.version_info[0],
                sys.version_info[1],
                sys.version_info[2]
            )
        })
        
        print("  完成: {:.4f}s (±{:.4f}s)".format(mean_time, std_time))
        
    except Exception as e:
        results.append({
            'test_name': bm.name,
            'category': bm.category,
            'success': False,
            'error': str(e)
        })
        print("  失败: {}".format(e))

# 保存结果
with open(output_file, 'w') as f:
    json.dump({
        'test_type': 'ArcMap_Python_Window',
        'arcgis_version': arcpy.GetInstallInfo()['Version'],
        'python_version': '{}.{}.{}'.format(
            sys.version_info[0],
            sys.version_info[1],
            sys.version_info[2]
        ),
        'results': results
    }, f, indent=2)

print("\n" + "=" * 60)
print("测试完成！")
print("结果已保存到: {}".format(output_file))
print("=" * 60)
print("\n成功: {} | 失败: {}".format(
    len([r for r in results if r.get('success')]),
    len([r for r in results if not r.get('success')])
))
