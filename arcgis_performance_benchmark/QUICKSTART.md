# 快速开始指南

## 推荐使用图形界面

最简单的方式是使用图形界面：

```bash
# 双击启动（Windows）
launch_gui.bat

# 或使用 Python 启动
python launch_gui.py
```

然后按照界面上的 1→2→3→4→5 步骤点击执行即可。

---

## 命令行方式（备选）

如果 GUI 无法使用，可以使用命令行：

### 1. 验证环境

```bash
# Python 2.7
C:\Python27\ArcGIS10.8\python.exe test_setup.py

# Python 3.x
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_setup.py
```

### 2. 运行完整测试流程

```bash
# 步骤1：使用 Python 2.7 生成数据并运行测试
C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py --generate-data

# 步骤2：使用 Python 3.x 运行测试（使用已生成的数据）
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py

# 步骤3：分析结果（使用任一 Python 版本）
python analyze_results.py
```

### 3. 自动运行两个版本

```bash
python run_both_versions.py
```

---

## 查看结果

分析完成后，查看生成的报告：

```bash
# Markdown 报告（可直接在浏览器或 Markdown 编辑器中查看）
results/tables/comparison_report.md

# LaTeX 表格（可直接插入论文）
results/tables/comparison_table.tex

# CSV 数据（可用 Excel 打开）
results/tables/comparison_data.csv
```

---

## 调整测试设置

在 GUI 界面的"测试设置"区域，可以直接修改：

| 设置项 | 默认值 | 说明 |
|--------|--------|------|
| **循环次数** | 3 次 | 每项测试执行的次数，越多结果越稳定 |
| **预热次数** | 1 次 | 正式测试前的预热运行次数 |
| **数据规模** | 中小型 | 中小型（快速测试）或大型（学术论文）|

或者手动编辑 `config/settings.py`：

```python
# 循环次数
TEST_RUNS = 3

# 预热次数
WARMUP_RUNS = 1

# 数据规模（False=中小型, True=大型）
USE_LARGE_SCALE = False
```

---

## 常用命令

```bash
# 仅运行矢量测试
run_benchmarks.py --category vector

# 仅运行栅格测试
run_benchmarks.py --category raster

# 增加测试次数（提高统计可靠性）
run_benchmarks.py --runs 10 --warmup 2

# 指定输出目录
run_benchmarks.py --output-dir D:\benchmark_results
```

---

## 故障排除

### GUI 无法启动

1. 检查是否安装了 ArcGIS Pro（推荐）或 ArcGIS Desktop
2. 尝试使用命令行方式运行
3. 检查 Python 路径是否正确

### 问题：arcpy 不可用
**解决**：确保使用 ArcGIS 自带的 Python 解释器运行脚本

### 问题：内存不足
**解决**：在 `config/settings.py` 中减小数据规模

### 问题：许可错误
**解决**：确保 ArcGIS 许可为 Advanced 级别

### 问题：结果文件未生成
**解决**：检查 `results/` 目录是否有写入权限

---

## 论文写作建议

1. **方法部分**：描述测试环境、数据规模、测试项目
2. **结果部分**：使用生成的表格和图表
3. **讨论部分**：分析 Python 3.x 性能优势的原因

生成的 LaTeX 表格示例：

```latex
\begin{table}[htbp]
\centering
\caption{ArcGIS Python 性能对比}
\input{results/tables/comparison_table.tex}
\end{table}
```
