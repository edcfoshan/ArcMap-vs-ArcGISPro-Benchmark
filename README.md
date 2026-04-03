# ArcGIS Python2、3 与开源库性能对比测试工具

> 当前文档适用版本：`v1.0.0`

## 项目简介

本项目用于在同一台 Windows 机器上，对 ArcGIS Desktop (Python 2.7)、ArcGIS Pro (Python 3.x) 以及开源 GIS 库方案进行统一基准测试，输出可直接用于论文写作、统计分析和结果归档的报告文件。

`v1.0.0` 是首个面向正式发布整理的版本，已经统一启动入口、GUI 操作路径、结果目录结构与中文文档说明。

## v1.0 核心能力

- 12 项 GIS 基准测试，覆盖矢量、栅格、混合操作。
- 支持 Python 2.7、Python 3.x 与开源库方案的两向或三向对比。
- 提供现代化 GUI，支持多规模勾选、进度条、ETA、日志保存/复制、结果目录直开。
- 支持五级数据规模：`tiny`、`small`、`standard`、`medium`、`large`。
- 支持多进程对比与开源库可用性检测/安装。
- 报告统一输出为 `Markdown / LaTeX / CSV / JSON` 四种格式。

## 文档导航

- `QUICKSTART.md`：最短路径上手说明。
- `GUI_v2_使用说明.md`：当前 GUI 的完整使用说明。
- `docs/GUI_GUIDE.md`：图形界面详细操作指南。
- `docs/README_SIMPLE.md`：面向直接使用者的简化版说明。
- `RELEASE_NOTES.md`：`v1.0.0` 发布说明与发布前复核建议。
- `docs/DESKTOP_TEST_GUIDE.md`：桌面软件窗口 vs 独立解释器扩展研究指南。
- `制作EXE说明.md`：GUI 打包为 EXE 的说明。

## 推荐启动方式

| 方式 | 入口 | 说明 |
|------|------|------|
| 推荐 | `启动工具.vbs` | 无黑窗口启动，优先使用 ArcGIS Pro Python 环境 |
| 兼容 | `launch_gui.bat` | 批处理方式隐藏启动 |
| 兼容 | `python launch_gui.py` | 由启动器自动选择合适解释器 |
| 兼容 | `launch.vbs` / `start_gui_hidden.vbs` | 历史兼容入口，仍可使用 |
| 备用 | `启动工具_系统Python.vbs` | 使用系统 `pythonw`，仅在环境完整时建议使用 |

## GUI 快速流程

1. 双击 `启动工具.vbs`。
2. 首次启动时确认 Python 2.7 与 Python 3.x 路径正确。
3. 勾选一个或多个数据规模，可选启用“多进程”与“开源库”。
4. 点击“开始测试”。
5. 测试完成后点击“打开生成结果文件夹”查看报告。

如果一次勾选多个规模，程序会在同一时间戳目录下为每个规模分别生成一套结果，互不覆盖。

## 命令行用法

### 1. 环境验证

```bash
C:\Python27\ArcGIS10.8\python.exe test_setup.py
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_setup.py
```

### 2. 单独运行某个版本

```bash
C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py --scale medium
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale medium
```

### 3. 启用开源库对比

```bash
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale medium --opensource
```

### 4. 自动跑双版本

```bash
python scripts\run_both_versions.py
```

### 5. 单独分析结果

```bash
python analyze_results.py --results-dir C:\temp\arcgis_benchmark_data\<时间戳>\<规模> --output-dir C:\temp\arcgis_benchmark_data\<时间戳>\<规模>
```

## 测试内容

### 矢量测试（6 项）

| ID | 名称 | 说明 |
|----|------|------|
| V1 | CreateFishnet | 创建渔网多边形 |
| V2 | CreateRandomPoints | 生成随机点 |
| V3 | Buffer | 缓冲区分析 |
| V4 | Intersect | 叠加分析 |
| V5 | SpatialJoin | 空间连接 |
| V6 | CalculateField | 字段计算 |

### 栅格测试（4 项）

| ID | 名称 | 说明 |
|----|------|------|
| R1 | CreateConstantRaster | 创建常量栅格 |
| R2 | Resample | 栅格重采样 |
| R3 | Clip | 栅格裁剪 |
| R4 | RasterCalculator | 栅格计算 |

### 混合测试（2 项）

| ID | 名称 | 说明 |
|----|------|------|
| M1 | PolygonToRaster | 矢转栅 |
| M2 | RasterToPoint | 栅转矢 |

## 数据规模

| 规模 | 预计时间 | 典型用途 | 典型磁盘需求 |
|------|----------|----------|--------------|
| `tiny` | 1-2 分钟 | 快速验证、调试 | 约 500MB |
| `small` | 5-10 分钟 | 功能测试 | 约 2GB |
| `standard` | 15-30 分钟 | 日常验证 | 约 5GB |
| `medium` | 30-60 分钟 | 性能对比、论文主结果 | 约 10GB |
| `large` | 2-4 小时 | 学术研究大样本 | 约 30GB |

### 关键参数概览

| 规模 | 渔网行列 | 随机点 | 叠加要素 | 常量栅格尺寸 |
|------|----------|--------|----------|--------------|
| `tiny` | 50 × 50 | 1,000 | 10,000 + 10,000 | 500 |
| `small` | 100 × 100 | 10,000 | 100,000 + 100,000 | 1,000 |
| `standard` | 500 × 500 | 50,000 | 300,000 + 300,000 | 5,000 |
| `medium` | 1000 × 1000 | 100,000 | 1,000,000 + 1,000,000 | 10,000 |
| `large` | 5000 × 5000 | 500,000 | 5,000,000 + 5,000,000 | 30,000 |

## 输出目录结构

默认输出根目录为 `C:\temp\arcgis_benchmark_data`。主流程下的结构如下：

```text
C:\temp\arcgis_benchmark_data\
└── <时间戳>\
    ├── tiny\
    │   ├── comparison_report.md
    │   ├── comparison_table.tex
    │   ├── comparison_data.csv
    │   ├── comparison_data.json
    │   └── data\
    │       ├── py2\
    │       ├── py3\
    │       └── os\
    └── medium\
        ├── comparison_report.md
        └── data\
            ├── py2\
            ├── py3\
            └── os\
```

说明：

- 报告文件位于每个规模目录根部。
- `data\py2`、`data\py3`、`data\os` 分别保存各方案原始结果与运行产物。
- 仓库内的 `results\` 目录仅保留给旧脚本或桌面扩展研究流程，不是主 GUI 默认输出位置。

## 系统要求

### 必需组件

- Windows 操作系统。
- ArcGIS Desktop 10.x（Python 2.7）。
- ArcGIS Pro 3.x（Python 3.x）。
- 建议 ArcGIS Advanced 许可。

### 开源对比依赖

开源库对比仅在 Python 3.x 环境下可用，可通过 GUI 自动安装，也可手动执行：

```bash
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pip install geopandas rasterio shapely pyogrio numpy
```

### 建议硬件

| 场景 | 建议内存 | 备注 |
|------|----------|------|
| `tiny` / `small` | 8GB | 验证与快速测试 |
| `standard` / `medium` | 16GB | 推荐日常环境 |
| `large` | 32GB 及以上 | 适合论文最终实验 |

## 项目结构

```text
.
├── benchmark_gui_modern.py         主 GUI
├── launch_gui.py                   GUI 启动器
├── 启动工具.vbs                    推荐启动入口
├── run_benchmarks.py               命令行执行器
├── analyze_results.py              报告分析器
├── scripts\run_both_versions.py    双版本连续执行脚本
├── benchmarks\                     基准测试实现
├── config\settings.py              全局配置
├── utils\settings_manager.py       GUI 配置与语言管理
├── docs\                           辅助说明文档
├── desktop_automation\             桌面软件扩展研究脚本
└── results\                        旧脚本/扩展研究遗留目录
```

## v1.0 发布整理要点

- 启动入口统一为现代 GUI，推荐使用 `启动工具.vbs`。
- 文档统一为当前界面口径，不再描述旧版“五步向导”界面。
- 结果目录统一为 `<时间戳>\<规模>\data\py2|py3|os` 布局。
- GUI 支持多规模勾选、语言切换、字体缩放、日志保存/复制。
- 三向对比报告与中文输出说明已同步完善。

## 故障排除

### 1. 文件锁定

症状：`ERROR 000464`

处理方式：

- 关闭 ArcMap、ArcGIS Pro 与相关属性表窗口。
- 删除 `C:\temp\arcgis_benchmark_data` 下对应测试目录后重试。

### 2. 开源库不可用

症状：GUI 中开源库状态显示未安装，或命令行报 `ModuleNotFoundError`

处理方式：

- 在 GUI 中点击“安装开源库”。
- 或手动执行上文的 `pip install` 命令。

### 3. Python 环境未找到

处理方式：

- 确认 ArcGIS Desktop 与 ArcGIS Pro 已正确安装。
- 在 GUI 中重新指定 Python 2.7 与 Python 3.x 路径。

### 4. 报告未生成

处理方式：

- 确认 `py2` 与 `py3` 结果都已成功生成。
- 如果启用了开源库，也确认 `data\os` 下存在结果文件。

### 5. 需要调整心跳日志频率

可在 `config/settings.py` 中修改 `PROGRESS_HEARTBEAT_INTERVAL`：

- `0`：关闭心跳日志。
- 正整数：按秒输出长任务进度心跳。

## 许可证

本工具面向学术研究与教学场景整理。
