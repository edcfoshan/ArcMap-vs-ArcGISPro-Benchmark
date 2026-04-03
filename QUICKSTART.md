# 快速开始指南

> 面向 `v1.0.0`

## 最短路径

### 1. 启动 GUI

推荐直接双击：

```text
启动工具.vbs
```

也可以使用：

```bash
python launch_gui.py
```

### 2. 选择测试参数

- 先确认 Python 2.7 与 Python 3.x 路径可用。
- 勾选一个或多个数据规模：`tiny / small / standard / medium / large`。
- 按需启用“多进程”与“开源库”。

### 3. 开始测试

- 点击“开始测试”。
- 查看进度条、ETA 和日志输出。
- 测试完成后点击“打开生成结果文件夹”。

## 结果在哪里

默认输出路径：

```text
C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\
```

每个规模目录下都会生成：

- `comparison_report.md`
- `comparison_table.tex`
- `comparison_data.csv`
- `comparison_data.json`
- `data\py2`
- `data\py3`
- `data\os`

如果一次勾选多个规模，会在同一时间戳目录下并列生成多个规模文件夹。

## 命令行方式

### 环境验证

```bash
C:\Python27\ArcGIS10.8\python.exe test_setup.py
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_setup.py
```

### 手动跑双版本

```bash
C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py --scale medium
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale medium
python analyze_results.py --results-dir C:\temp\arcgis_benchmark_data\<时间戳>\<规模> --output-dir C:\temp\arcgis_benchmark_data\<时间戳>\<规模>
```

### 自动连续跑双版本

```bash
python scripts\run_both_versions.py
```

### 启用开源库对比

```bash
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pip install geopandas rasterio shapely pyogrio numpy
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale medium --opensource
```

## 常用参数

```bash
python run_benchmarks.py --scale medium
python run_benchmarks.py --scale medium --opensource
python run_benchmarks.py --scale medium --multiprocess --mp-workers 4
python run_benchmarks.py --category vector --scale small
python run_benchmarks.py --scale medium --generate-data
```

## 常见问题

### GUI 启动失败

- 检查 ArcGIS Pro 或 ArcGIS Desktop 是否已安装。
- 改用 `python launch_gui.py` 查看是否有报错。

### `arcpy` 不可用

- 必须使用 ArcGIS 自带 Python 解释器运行。

### 开源库未安装

- 在 GUI 中点击“安装开源库”。
- 或手动运行上面的 `pip install` 命令。

### 文件锁定

- 关闭 ArcMap、ArcGIS Pro 和相关属性表窗口。
- 删除 `C:\temp\arcgis_benchmark_data` 下对应目录后重试。

### 内存不足

- 改用 `tiny` 或 `small` 规模。
