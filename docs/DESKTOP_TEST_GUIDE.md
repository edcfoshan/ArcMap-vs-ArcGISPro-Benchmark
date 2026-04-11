# 桌面软件窗口 vs 独立解释器 测试指南

> 这是扩展研究流程，不属于 `v1.0.0` 主 GUI 的默认执行链路。

## 当前状态

- 主流程已经统一输出 `benchmark_run.log` 和 `benchmark_manifest.json`，方便复现与回溯。
- 这份文档仍然只描述扩展研究流程，不替代主 GUI 的 `C:\temp\arcgis_benchmark_data` 输出链路。
- 当前交接与未完成调参见 `HANDOFF.md`。

## 适用场景

如果你想额外比较以下四种运行方式，可以使用本指南：

1. 独立 Python 2.7
2. 独立 Python 3.x
3. ArcMap Python 窗口
4. ArcGIS Pro Python 窗格

## 先理解当前状态

### 主发布流程

主 GUI 和主命令行默认把结果输出到：

```text
C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\
```

### 扩展研究脚本

桌面窗口扩展脚本仍使用仓库内的旧式辅助目录：

```text
results\raw
results\tables
```

因此，做四环境对比时，需要把主流程生成的独立解释器结果复制到 `results\raw` 中，再运行桌面窗口脚本和合并脚本。

## 第一步：准备独立解释器结果

先用主工具跑出 Python 2.7 与 Python 3.x 的基准结果，然后把以下文件复制到仓库的 `results\raw` 目录：

- `benchmark_results_py2.json`
- `benchmark_results_py3.json`

通常可从主输出目录中找到它们，例如：

```text
C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\data\py2\benchmark_results_py2.json
C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\data\py3\benchmark_results_py3.json
```

复制目标：

```text
results\raw\benchmark_results_py2.json
results\raw\benchmark_results_py3.json
```

## 第二步：修改桌面脚本中的项目路径

在执行前，先修改以下文件里的 `project_path`：

- `scripts/for_arcmap.py`
- `scripts/for_arcgis_pro.py`

把它改成当前仓库的真实绝对路径，例如：

```python
project_path = r"C:\Users\Administrator\Documents\ArcMap-vs-ArcGISPro-Benchmark"
```

否则脚本会继续使用旧示例路径，无法正常导入项目模块。

## 第三步：在 ArcMap 中执行

1. 打开 ArcMap。
2. 打开 Python 窗口。
3. 将 `scripts/for_arcmap.py` 全部内容复制进去执行。
4. 等待脚本完成。

执行完成后，结果会写入：

```text
results\raw\benchmark_results_arcmap.json
```

## 第四步：在 ArcGIS Pro 中执行

1. 打开 ArcGIS Pro。
2. 打开 Python 窗格。
3. 将 `scripts/for_arcgis_pro.py` 全部内容复制进去执行。
4. 等待脚本完成。

执行完成后，结果会写入：

```text
results\raw\benchmark_results_arcgis_pro.json
```

## 第五步：合并分析

当四类结果都准备好后，执行：

```bash
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" desktop_automation\merge_desktop_results.py
```

默认会读取：

```text
results\raw\
```

并输出到：

```text
results\tables\
```

主要输出文件：

- `desktop_comparison_report.md`
- `desktop_comparison_data.csv`
- 如需和主流程结果对照，建议同时查看主目录中的 `benchmark_run.log` 与 `benchmark_manifest.json`。

## 推荐参数

桌面窗口测试建议先用 `small` 起步；这五档规模的含义与主 README 一致。

```python
DATA_SCALE = 'small'
TEST_RUNS = 1
WARMUP_RUNS = 0
```

其中 `standard` 仍是主流程推荐，`medium` / `large` 更适合更长时间的重负载测试。

这样更适合人工操作，也能减少 ArcMap 内存压力。

## 注意事项

- ArcMap 为 32 位，尽量避免直接跑大规模数据。
- 四种运行方式必须使用相同的数据规模与运行次数，结果才有可比性。
- 如果桌面窗口中出现路径错误，优先检查 `project_path` 是否已改成当前仓库路径。
