# 快速开始指南

> 面向 `v1.0.0`

本工具提供两种使用入口：**主工具（GUI）** 用于完整自定义跑测，**网页控制台** 用于快速验证。根据你的场景选择即可。

---

## 一、主工具（GUI）：完整自定义跑测

### 1. 启动 GUI

推荐直接双击根目录下的：

```text
ArcGIS基准测试工具.vbs
```

也可以手动运行：

```bash
python benchmark_gui_modern.py
```

> 首次启动时，会弹出引导对话框展示自动检测到的 Python 2.7 / Python 3.x 路径，确认后即可开始。

### 2. 选择测试参数

- **Python 路径**：确认 Python 2.7 与 Python 3.x 路径可用（如为空，点击"自动检测"）。
- **数据规模**：勾选一个或多个规模：`tiny / small / standard / medium / large`。
- **测试次数**：`Test runs` 为正式计时次数，`Warmup runs` 为预热次数（消除文件缓存偏差）。
- **多进程**：勾选后可调整 `MP workers`（并行 worker 数）。
- **开源库**：勾选后若提示"缺少依赖"，可点击"安装开源库"一键修复。

### 3. 开始测试

- 点击"开始测试"。
- 查看进度条、ETA 和日志输出。
- 测试完成后点击"打开生成结果文件夹"。

---

## 二、网页控制台：快速验证（tiny / small）

适合只想快速验证环境或对比链路是否正常的场景。

### 1. 启动网页控制台

双击根目录下的：

```text
打开网页控制台.bat
```

浏览器会自动打开 `http://127.0.0.1:8765`。

### 2. 快速跑测

- 默认已勾选 `tiny + small`。
- 可点击"快速预设"（1 次运行、0 次预热、自动生成数据）。
- 点击"开始验证"后，页面会显示各规模的阶段进度与日志。
- 完成后可直接在页面预览并下载 `comparison_report.md`。

---

## 三、跑完后在哪里找结果

每次跑测都会生成一个带时间戳的文件夹，最新结果可通过以下方式快速找到：

### 方式 1：latest.txt 索引

在默认输出根目录下会生成 `latest.txt`：

```text
C:\temp\arcgis_benchmark_data\latest.txt
```

用记事本打开即可看到最新结果文件夹的绝对路径。

### 方式 2：GUI / 网页控制台直接打开

- **GUI**：点击"打开生成结果文件夹"。
- **网页控制台**：结果面板中有"打开结果文件夹"按钮。

### 结果目录结构示例

```text
C:\temp\arcgis_benchmark_data\
└── 20250412_143052\               <-- 时间戳根目录
    ├── comparison_report.md         <-- 跨规模汇总报告（分析完成后生成）
    ├── comparison_data.json
    ├── benchmark_results_py2.json   <-- Py2 原始结果
    ├── benchmark_results_py3.json   <-- Py3 原始结果
    ├── benchmark_results_os.json    <-- 开源库原始结果
    ├── tiny\                        <-- 规模子目录
    │   ├── comparison_report.md
    │   ├── benchmark_results_py2.json
    │   ├── benchmark_results_py3.json
    │   ├── benchmark_results_os.json
    │   ├── benchmark_run.log
    │   ├── benchmark_manifest.json
    │   └── data\                    <-- 中间数据集（shp/gdb/tif）
    │       └── ...
    └── small\
        └── ...
```

说明：

- **根目录**（时间戳目录）保留汇总报告与 JSON/CSV，方便一眼找到。
- **`data/` 子目录** 存放 `.gdb`、`.shp`、`.tif` 等中间数据集，避免根目录 cluttered。
- 每个规模目录下都有独立的 `benchmark_manifest.json`，记录了本次运行的 Python/依赖版本、Git Commit、硬件信息，便于复现。

---

## 四、命令行方式（高级）

### 环境验证

```bash
C:\Python27\ArcGIS10.8\python.exe test_setup.py
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_setup.py
```

### 手动跑单个版本

```bash
C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py --scale standard
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale standard
```

### 启用开源库对比

```bash
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pip install geopandas rasterio shapely pyogrio numpy
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale standard --opensource
```

### 常用参数

```bash
python run_benchmarks.py --scale standard
python run_benchmarks.py --scale standard --opensource
python run_benchmarks.py --scale standard --multiprocess --mp-workers 4
python run_benchmarks.py --category vector --scale small
python run_benchmarks.py --scale standard --generate-data
```

---

## 五、常见问题

### GUI 启动失败

- 检查 ArcGIS Pro 或 ArcGIS Desktop 是否已安装。
- 改用 `python benchmark_gui_modern.py` 查看具体报错。

### `arcpy` 不可用

- 必须使用 ArcGIS 自带 Python 解释器运行。

### 开源库未安装或缺少依赖

- 在 GUI 的"开源库"区域会显式提示缺少的包名（如 `rasterio`、`shapely`）。
- 点击"安装开源库"即可一键修复。
- 或手动运行上方的 `pip install` 命令。

### 文件锁定

- 关闭 ArcMap、ArcGIS Pro 和相关属性表窗口。
- 删除 `C:\temp\arcgis_benchmark_data` 下对应目录后重试。

### 内存不足

- 改用 `tiny` 或 `small` 规模。
