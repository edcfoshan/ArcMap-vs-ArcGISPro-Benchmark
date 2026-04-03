# ArcGIS Python2、3 与开源库性能对比测试工具 - 开发指南

## 项目概述

本项目是一个用于对比分析 ArcGIS Desktop (Python 2.7)、ArcGIS Pro (Python 3.x) 以及开源库方案在相同硬件环境下处理 GIS 数据性能差异的基准测试工具。主要用于学术研究，生成可用于论文的对比数据。

### 核心功能

- **性能基准测试**: 涵盖矢量数据、栅格数据、混合操作共12项测试
- **双版本对比**: 自动对比 Python 2.7 和 Python 3.x 的执行效率
- **图形界面**: 提供现代 GUI，支持多规模勾选与一键运行
- **报告生成**: 自动生成 Markdown、LaTeX、CSV、JSON 格式的报告

### 系统要求

- Windows 操作系统
- ArcGIS Desktop 10.x (Python 2.7)
- ArcGIS Pro 3.x (Python 3.x)
- 建议 16GB 以上内存
- C:\temp 磁盘空间需求：小型测试约5GB，大型测试约50GB

## 项目结构

```
.
├── benchmark_gui_modern.py   # 主图形界面程序（入口点）
├── run_benchmarks.py         # 命令行基准测试执行器
├── analyze_results.py        # 结果分析与报告生成器
├── launch_gui.py             # GUI 启动器
├── launch_gui.bat            # Windows 批处理兼容启动
├── 启动工具.vbs             # 推荐：无黑窗口启动 GUI
├── test_setup.py             # 环境测试脚本
├── config/
│   └── settings.py           # 全局配置（数据规模、循环次数等）
├── benchmarks/
│   ├── base_benchmark.py     # 基准测试基类
│   ├── vector_benchmarks.py  # 矢量数据测试（6项）
│   ├── raster_benchmarks.py  # 栅格数据测试（4项）
│   └── mixed_benchmarks.py   # 混合测试（2项）
├── utils/
│   ├── timer.py              # 高精度计时器与内存监控
│   ├── arcgis_env.py         # ArcGIS 环境检测
│   └── result_exporter.py    # 多格式结果导出
├── data/
│   └── generate_test_data.py # 测试数据生成器
├── scripts/
│   ├── for_arcmap.py         # ArcMap Python 窗口专用脚本
│   └── for_arcgis_pro.py     # ArcGIS Pro Python 窗格专用脚本
├── desktop_automation/       # 桌面软件自动化测试相关
├── C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\  # 测试结果输出根目录
│   ├── data\py2              # Python 2.7 原始结果与数据
│   ├── data\py3              # Python 3.x 原始结果与数据
│   ├── data\os               # 开源库原始结果与数据
│   └── comparison_report.md  # 当前规模目录根部报告文件
└── *.md                      # 各类文档
```

## 技术栈

- **编程语言**: Python 2.7 / Python 3.x（双版本兼容）
- **GUI 框架**: Tkinter（Python 标准库）
- **GIS 库**: ArcPy (ArcGIS 自带)
- **编码规范**: 所有文件使用 UTF-8 编码，包含 `# -*- coding: utf-8 -*-` 声明
- **兼容性**: 使用 `from __future__` 实现 Python 2/3 兼容

## 关键配置

### Python 解释器路径

在 `benchmark_gui_modern.py` 中硬编码：
- Python 2.7: `C:\Python27\ArcGIS10.8\python.exe`
- Python 3.x: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`

### 数据存储位置

- **测试数据**: `C:\temp\arcgis_benchmark_data`（大文件，自动清理输出但不清理输入数据）
  - 数据库按规模命名：`benchmark_data_tiny.gdb`、`benchmark_data_small.gdb` 等
  - 支持数据复用：相同规模的数据库会被自动识别并复用
  - **测试结果**: `C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\`（小文件，保留）

### 数据规模配置 (`config/settings.py`)

```python
DATA_SCALE = 'tiny'  # 可选: 'tiny', 'small', 'standard', 'medium', 'large'
TEST_RUNS = 3        # 正式测试循环次数
WARMUP_RUNS = 1      # 预热次数（不计入结果）
```

| 规模 | 预计时间 | 磁盘需求 | 适用场景 |
|------|----------|----------|----------|
| tiny | 1-2分钟 | ~500MB | 快速验证 |
| small | 5-10分钟 | ~2GB | 快速测试 |
| medium | 30-60分钟 | ~10GB | 日常测试（推荐） |
| large | 2-4小时 | ~30GB | 学术论文 |

## 运行方式

### 1. 图形界面方式（推荐）

```bash
# 双击启动（无黑窗口，推荐）
启动工具.vbs

# 兼容方式
launch_gui.bat

# 或使用 Python 启动
python launch_gui.py

# 或直接运行
python benchmark_gui_modern.py
```

### 2. 命令行方式

```bash
# 步骤1: 验证环境
C:\Python27\ArcGIS10.8\python.exe test_setup.py
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_setup.py

# 步骤2: 生成测试数据
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" data\generate_test_data.py

# 步骤3: Python 2.7 测试
C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py

# 步骤4: Python 3.x 测试
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py

# 步骤5: 分析结果
python analyze_results.py
```

## 测试项目列表

### 矢量数据测试 (6项)
| 测试ID | 测试名称 | 说明 |
|--------|----------|------|
| V1 | CreateFishnet | 创建渔网多边形 |
| V2 | CreateRandomPoints | 生成随机点 |
| V3 | Buffer | 缓冲区分析 |
| V4 | Intersect | 叠加分析 |
| V5 | SpatialJoin | 空间连接 |
| V6 | CalculateField | 字段计算 |

### 栅格数据测试 (4项)
| 测试ID | 测试名称 | 说明 |
|--------|----------|------|
| R1 | CreateConstantRaster | 创建常量栅格 |
| R2 | Resample | 栅格重采样 |
| R3 | Clip | 栅格裁剪 |
| R4 | RasterCalculator | 栅格计算 |

### 混合测试 (2项)
| 测试ID | 测试名称 | 说明 |
|--------|----------|------|
| M1 | PolygonToRaster | 矢转栅 |
| M2 | RasterToPoint | 栅转矢 |

## 代码风格指南

### Python 2/3 兼容性

所有代码必须同时兼容 Python 2.7 和 Python 3.x：

```python
# 文件头必须包含
# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

# 字符串格式化使用 .format() 而非 f-string
print("Time: {:.4f}s".format(elapsed_time))

# Python 2/3 兼容的导入
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    import Tkinter as tk
    import ttk
```

### 文件编码

- 所有 `.py` 文件必须使用 UTF-8 编码
- 所有 `.md` 文件使用中文编写
- 读写文件时显式指定 `encoding='utf-8'`

### 注释规范

- 使用中文注释
- 类和函数使用 docstring 说明
- 关键逻辑添加行注释

## 开发工作流

### 添加新测试项

1. 在 `benchmarks/` 下找到对应类别的文件
2. 继承 `BaseBenchmark` 类
3. 实现 `setup()`, `run_single()`, `teardown()` 方法
4. 在对应的 `get_all_benchmarks()` 中添加新测试类

示例：
```python
class VX_NewTest(BaseBenchmark):
    def __init__(self):
        super(VX_NewTest, self).__init__("VX_NewTest", "vector")
    
    def setup(self):
        arcpy.env.workspace = settings.DATA_DIR
        arcpy.env.overwriteOutput = True
    
    def run_single(self):
        # 执行测试操作
        return {'result': value}
    
    def teardown(self):
        # 清理临时文件
        pass
```

### 修改数据规模

编辑 `config/settings.py` 中的对应配置字典：
- `VECTOR_CONFIG_TINY/SMALL/MEDIUM/LARGE`
- `RASTER_CONFIG_TINY/SMALL/MEDIUM/LARGE`

## 故障排除

### 常见问题

1. **文件锁定错误** (`ERROR 000464`)
   - 关闭所有 ArcGIS 程序
   - 手动删除 `C:\temp\arcgis_benchmark_data`
   - 重新运行测试

2. **编码错误** (`'gbk' codec can't decode`)
   - 已在 GUI 中自动处理为 UTF-8
   - 无法解码的字符显示为 `�`，不影响结果

3. **找不到 Python 环境**
   - 检查 `benchmark_gui_modern.py` 中的路径配置
   - 确认 ArcGIS 已正确安装

4. **内存不足**
   - 减小 `config/settings.py` 中的数据规模
   - 或使用更小规模的预设

### 调试技巧

- 使用 `tiny` 数据规模进行快速验证
- 查看日志输出了解详细执行过程
- 运行 `test_setup.py` 检查环境配置

### 数据复用说明

1. **自动复用**
   - 如果 `C:\temp\arcgis_benchmark_data\benchmark_data_{规模}.gdb` 存在且数据完整
   - 工具会自动跳过生成步骤，直接使用现有数据
   - 大幅节省重复测试的时间

2. **强制重新生成**
   - 删除对应规模的数据库文件夹
   - 或运行 `python data\generate_test_data.py --force`

3. **清理所有数据**
   - 手动删除整个 `C:\temp\arcgis_benchmark_data` 目录
   - 或使用工具中的"清理旧数据"功能（只清理输出文件，保留输入数据）

## 安全注意事项

1. **数据安全**: 测试数据存储在 `C:\temp`，不会永久保留
2. **许可要求**: 需要 ArcGIS Advanced 级别许可
3. **权限要求**: 需要写入 `C:\temp` 和项目目录的权限
4. **进程安全**: 测试过程中请勿强制关闭 ArcGIS 进程

## 输出文件说明

测试完成后在 `C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\` 生成：

- `comparison_report.md` - Markdown 格式完整报告
- `comparison_table.tex` - LaTeX 表格（可直接插入论文）
- `comparison_data.csv` - CSV 数据（可用 Excel 分析）
- `comparison_data.json` - JSON 原始数据

## 扩展开发

### 添加新的输出格式

在 `utils/result_exporter.py` 的 `ResultExporter` 类中添加新方法。

### 添加新的分析维度

在 `analyze_results.py` 中修改统计计算逻辑。

### 支持更多 ArcGIS 版本

在 `utils/arcgis_env.py` 的 `detect_arcgis_installations()` 中添加新路径。

## 更新记录

### 2026-03-29 重要更新

#### 1. 智能数据复用机制
- **数据库命名**: 按数据规模命名（`benchmark_data_tiny.gdb`、`benchmark_data_small.gdb` 等）
- **自动检查**: 生成数据前检查现有数据是否匹配当前规模要求
- **跳过生成**: 数据完整且规模匹配时直接复用，大幅节省时间
- **清理优化**: 只删除基准测试输出文件，保留测试数据供复用

#### 2. 数据共享（单数据库）
- 改为只用 Python 3.x 生成一次数据
- Py2 和 Py3 共用同一个数据库文件
- **注意**: 依赖 ArcGIS Pro 和 Desktop 的数据库格式兼容性

#### 3. 报告全中文化
- `comparison_report.md` 完全中文化
- 添加统计摘要、测试项目说明等详细内容

#### 4. 详细日志输出
- 步骤 2 显示数据生成进度和详细信息
- 测试执行时显示 Py2/Py3 版本标识
- 每个测试项显示耗时、内存峰值等详细信息

#### 5. 编码问题修复
- 所有 Unicode 特殊字符（✓、✗、━、▶ 等）替换为 ASCII 兼容字符
- 修复 Windows GBK 编码导致的乱码问题
- 添加多编码解码支持（UTF-8 → GBK → GB2312 → ...）
