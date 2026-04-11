# 桌面软件窗口 vs 独立解释器 研究说明

## 当前状态

- 主流程已经统一输出 `benchmark_run.log` 和 `benchmark_manifest.json`，桌面窗口对比仅作为扩展研究补充。
- 这份说明已和 `docs/DESKTOP_TEST_GUIDE.md`、`HANDOFF.md` 一起作为当前交接入口，后续优先维护这些文档。

## 这份文档讲什么

本文件用于说明一个扩展研究方向：比较脚本在桌面软件窗口内执行，与在独立解释器中执行时的性能差异。

它不是主发布版 `v1.0.0` 的默认使用流程，而是附加研究主题。
这份扩展研究沿用主 README 的五档规模含义：`tiny` 快速验证，`small` 小规模测试，`standard` 常规完整运行（主流程推荐），`medium` 重负载完整对比，`large` 压力测试 / 过夜运行。
因此这里仍建议先从 `small` 起步，但不改变 `standard` 作为主流程推荐规模的定位。

## 对比对象

建议对比四种环境：

1. 独立 Python 2.7
2. 独立 Python 3.x
3. ArcMap Python 窗口
4. ArcGIS Pro Python 窗格

## 研究价值

- 量化桌面 GIS 软件带来的运行时开销。
- 评估 GUI、许可检查与交互环境对脚本性能的影响。
- 为“批处理应该放在哪里跑”提供更直接的经验依据。

## 当前仓库里的支持情况

### 已有内容

- `scripts/for_arcmap.py`
- `scripts/for_arcgis_pro.py`
- `desktop_automation/merge_desktop_results.py`

### 需要注意

- 这些扩展脚本仍基于仓库内 `results\raw` 与 `results\tables` 辅助目录。
- 在使用前，需要把 `scripts/for_arcmap.py` 和 `scripts/for_arcgis_pro.py` 里的 `project_path` 改成当前仓库真实路径。
- 主 GUI 默认输出在 `C:\temp\arcgis_benchmark_data`，如果要参加四环境合并分析，需要手动把独立解释器结果复制到 `results\raw`。

## 建议的实施方式

### 推荐流程

1. 先用主工具跑出独立 Python 2.7 与 Python 3.x 结果。
2. 将 `benchmark_results_py2.json` 与 `benchmark_results_py3.json` 复制到 `results\raw`。
3. 在 ArcMap 与 ArcGIS Pro 窗口中分别执行脚本。
4. 用 `desktop_automation\merge_desktop_results.py` 合并分析。

### 推荐参数

- 数据规模优先 `small`
- `TEST_RUNS = 1`
- `WARMUP_RUNS = 0`

这样更适合人工介入流程，也能减少 ArcMap 崩溃或锁定风险。

## 预期结论方向

- 独立解释器通常会快于桌面窗口。
- ArcGIS Pro 预计整体优于 ArcMap。
- 简单任务差距较小，复杂叠加或栅格任务差距可能更明显。

## 进一步参考

- `docs/DESKTOP_TEST_GUIDE.md`：具体操作步骤。
- `HANDOFF.md`：当前进度与后续调参任务。
