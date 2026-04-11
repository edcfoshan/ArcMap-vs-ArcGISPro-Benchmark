# 交接说明（当前进度）

本文用于把当前改动与未完成事项整理成“可直接接手”的状态，方便后续换 agent 继续调参和跑数。

## 当前结论（收敛版重设计已落地的部分）

### 1) `standard` 改为“按测试项单独调参”

- 配置入口在 `config/settings.py`：
  - `STANDARD_VECTOR_CONFIG_BY_TEST`
  - `STANDARD_RASTER_CONFIG_BY_TEST`
  - 读取接口：`get_vector_config_for_test(test_id)` / `get_raster_config_for_test(test_id)`
- `tiny / small` 仍保持统一倍数口径用于快速验证链路。

实现细节：
- 矢量类（V1-V4）以及开源库对应项、以及多进程 V1/V2 现在会在构造时读取 `get_vector_config_for_test('Vx')`。
- 栅格类（R1-R4）以及开源库对应项、以及多进程 R1 现在会读取 `get_raster_config_for_test('Rx')`。

### 2) 栅格项（R2/R3/R4）改为独立输入栅格，避免互相牵连

为了让 `standard` 可以只调某一项的 raster 参数而不影响其它项，R2/R3/R4 现在不再共享 `analysis_raster.tif`：

- `R2` 输入：`analysis_raster_R2.tif`
- `R3` 输入：`analysis_raster_R3.tif`
- `R4` 输入：`analysis_raster_R4.tif`

这些栅格会在各自 benchmark 的 `setup()` 中“按当前配置尺寸”自动生成（不计时），计时阶段只跑单一主操作。

### 3) OSM 输入链路：下载 shp，但正式生成前会导入/投影到 gdb

- OSM 缓存下载在 `utils/osm_samples.py`（默认香港，失败回退 Berlin）。
- `data/generate_test_data.py` 在 OSM 模式下会把 shp 通过 `arcpy.Project_management` 投影导入到基准 gdb（`osm_roads/osm_buildings/...`），并基于这些图层派生出基准用的 `buffer_points/spatial_join_*/calculate_field_fc/test_polygons_*`。
- 若 OSM 准备失败，会自动降级到“可复现的合成数据”模式，并在 manifest 中标记。

### 4) 日志产物：每次运行目录都会生成 `benchmark_run.log`

- `run_benchmarks.py` 会把 stdout/stderr 镜像到 `benchmark_run.log`。
- `analyze_results.py`、`verification_console/scheduler.py` 都会把 `benchmark_run.log` 当成正式产物引用/检查。

### 5) 中文验证页（独立，不动桌面 GUI）

- 目录：`verification_console/static/`
- 默认勾选：`tiny + small`（并且预设按钮也是两档）
- 全中文、字号与间距偏松，不走模板引擎，纯静态页 + 后端调度器。

## 仍需完成的工作（下一位 agent 直接做）

### A) `standard` 的 30-90s 目标调参

现在的 `STANDARD_*_CONFIG_BY_TEST` 只是“保守起步值”。需要在真实 ArcGIS 环境下跑 `standard`，并逐项把 Py2/Py3 尽量推入 30-90s 区间：

1. 先跑一轮 `standard`：`runs=1`、`warmup=0`、开启 `--opensource` 与 `--multiprocess`
2. 读取 `comparison_data.json`（或报告）查看每项耗时
3. 不达标就只调该项：
   - V3/V4/V5/V6 主要调 `STANDARD_VECTOR_CONFIG_BY_TEST`
   - R2/R3/R4 主要调 `STANDARD_RASTER_CONFIG_BY_TEST`
   - M1/M2 若偏短，再考虑把 `STANDARD_RASTER_CONFIG_BY_TEST['M2']['analysis_raster_size']` 拉高

### B) 在 ArcGIS 机器上验证 tiny/small 回归

本次改动涉及输入生成与配置读取，建议先在 ArcGIS Pro 的 Python 环境里跑 tiny/small 确认 12 项都能通过：

- 数据生成（Py3）：
  - `"<ArcGISProPython>" data\\generate_test_data.py`
- Py2：
  - `<ArcMapPython> run_benchmarks.py --scale tiny --opensource --multiprocess`
  - `<ArcMapPython> run_benchmarks.py --scale small --opensource --multiprocess`
- Py3：
  - `"<ArcGISProPython>" run_benchmarks.py --scale tiny --opensource --multiprocess`
  - `"<ArcGISProPython>" run_benchmarks.py --scale small --opensource --multiprocess`
- 分析：
  - `python analyze_results.py`

（路径以 `README.md/QUICKSTART.md` 为准。）

### C) 目录中的临时/调试文件清理

当前工作区仍有一些新增文件与研究笔记（例如 `.agents/research/...`），是否纳入正式交付需要你确认。

## 关键文件索引

- `config/settings.py`
- `data/generate_test_data.py`
- `run_benchmarks.py`
- `analyze_results.py`
- `benchmarks/vector_benchmarks*.py`
- `benchmarks/raster_benchmarks*.py`
- `benchmarks/mixed_benchmarks*.py`
- `verification_console/server.py`
- `verification_console/scheduler.py`
- `verification_console/static/index.html`
