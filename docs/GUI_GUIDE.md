# 图形界面详细使用指南

> 面向 `v1.0.0` 当前界面；不再使用旧版“五步向导”说明。

## 推荐启动方式

### 推荐

直接双击：

```text
启动工具.vbs
```

### 其他方式

```bash
python launch_gui.py
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" benchmark_gui_modern.py
```

## 界面结构

### 顶部标题区

- 显示项目名称与副标题。
- 右上角语言按钮可切换中英文。

### 左侧侧栏

主要负责设置参数：

- Python 2.7 / Python 3.x 路径。
- 测试运行次数与预热次数。
- 数据规模多选。
- 当前规模的参数编辑。
- 临时数据目录。
- 是否使用时间戳文件夹。
- 多进程与开源库选项。
- 打开生成结果文件夹。
- 字体缩放。

### 主内容区

- 总进度条。
- 当前任务提示。
- ETA 预计剩余时间。
- 实时日志输出。
- 日志工具栏：`Clear / Save / Copy`。

### 底部控制区

- “开始测试”
- “停止测试”
- “高级设置”

## 一次标准运行怎么做

### 1. 确认环境

- Python 2.7 指向 ArcGIS Desktop 自带解释器。
- Python 3.x 指向 ArcGIS Pro 自带解释器。
- 如需开源库对比，确认开源状态为可用。

### 2. 选择规模

推荐顺序：

1. 第一次先选 `tiny`。
2. 验证无误后再选 `medium` 或 `large`。
3. 需要批量测试时，可以一次勾选多个规模。

### 3. 选择附加能力

- “多进程”：用于额外对比单进程/多进程表现。
- “开源库”：在 Python 3.x 环境中增加 GeoPandas / Rasterio 方案对比。

### 4. 启动测试

- 点击“开始测试”。
- 观察日志中是否正确输出当前规模、解释器路径和输出目录。

### 5. 查看结果

- 点击“打开生成结果文件夹”。
- 每个规模目录下都应有四份报告和 `data\py2|py3|os` 原始结果目录。

## 输出目录说明

默认结构如下：

```text
C:\temp\arcgis_benchmark_data\<时间戳>\
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
    └── ...
```

说明：

- `comparison_report.md` 为主阅读报告。
- `comparison_table.tex` 可直接用于论文排版。
- `comparison_data.csv` 便于 Excel 继续分析。
- `comparison_data.json` 保留原始结构化结果。

## 高级设置里有什么

高级设置对话框提供：

- Python 路径浏览与环境验证。
- 运行次数、预热次数、worker 数。
- 五级数据规模参数的细粒度编辑。
- 保存哪些结果、是否使用时间戳目录、保留天数。
- 是否记住上次设置。

## 常见场景建议

### 只做快速验证

- 规模选 `tiny`
- 关闭多进程
- 关闭开源库

### 做论文主实验

- 规模选 `medium`
- 运行次数至少 3
- 如需替代方案讨论，启用开源库

### 做性能放大对比

- 同时勾选 `small / standard / medium`
- 保持相同运行次数
- 统一在同一时间戳目录下留档

## 常见问题

### 看不到开源库结果

- 先确认 Python 3.x 路径正确。
- 再确认开源库状态已通过检查。

### 日志太多

- 可以用 `Save` 保存日志。
- 如只想降低长任务心跳频率，可修改 `config/settings.py` 中的 `PROGRESS_HEARTBEAT_INTERVAL`。

### 想继续复用已有测试数据

- 主流程会优先复用同规模数据库。
- 如果想强制重建，可改用命令行加 `--generate-data`。
