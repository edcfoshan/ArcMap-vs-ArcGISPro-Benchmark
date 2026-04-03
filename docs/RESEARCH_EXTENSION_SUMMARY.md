# 研究扩展总结：桌面软件窗口 vs 独立解释器

## 一句话结论

这个扩展研究值得做，但它属于主发布版之外的附加课题，当前流程仍需要人工参与。

## 为什么值得做

- 能量化 ArcMap / ArcGIS Pro 桌面窗口带来的运行时开销。
- 能为“交互开发”和“批处理生产”给出更清晰的经验建议。
- 对论文讨论部分和工程实践建议都很有价值。

## 当前仓库已经具备的支撑

- `scripts/for_arcmap.py`
- `scripts/for_arcgis_pro.py`
- `desktop_automation/merge_desktop_results.py`
- `docs/DESKTOP_TEST_GUIDE.md`

## 目前仍然需要人工处理的地方

- ArcMap 与 ArcGIS Pro 需要人工打开。
- 需要把窗口脚本粘贴到对应 Python 窗口/窗格执行。
- 需要先把主流程生成的独立解释器结果复制到 `results\raw`。
- 需要把窗口脚本里的 `project_path` 修改为当前仓库真实路径。

## 推荐实施顺序

1. 用主 GUI 或主命令行跑出独立 Python 2.7 / 3.x 结果。
2. 复制 `benchmark_results_py2.json` 与 `benchmark_results_py3.json` 到 `results\raw`。
3. 在 ArcMap 与 ArcGIS Pro 中执行窗口脚本。
4. 运行 `desktop_automation\merge_desktop_results.py` 生成扩展对比报告。

## 推荐参数

- `DATA_SCALE = 'small'`
- `TEST_RUNS = 1`
- `WARMUP_RUNS = 0`

## 风险点

- ArcMap 是 32 位，容易受内存限制影响。
- 如果路径没改对，窗口脚本会直接失败。
- 如果四类结果的运行次数或数据规模不一致，最终结论不可比。

## 建议定位

对外发布 `v1.0.0` 时，建议把这一部分表述为：

- “扩展研究能力”
- “附加对比流程”
- “默认主流程之外的研究补充”

而不是主产品默认按钮路径，避免用户误以为 GUI 内部已经完全打通四环境合并分析。
