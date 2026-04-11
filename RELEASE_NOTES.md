# v1.0.0 发布说明

发布日期：`2026-04-03`

## 2026-04-11 维护更新（未发版）

- `standard` 已切换为按测试项单独调参，目标是把 12 项尽量推入 30-90 秒区间。
- 每次运行都会生成 `benchmark_run.log` 与 `benchmark_manifest.json`，用于回溯与复现。
- 独立中文验证网页默认只勾选 `tiny + small`，不影响原有桌面 GUI。
- 当前进度与后续调参任务已收口到 `HANDOFF.md`。

## 发布定位

`v1.0.0` 作为本项目首个正式发布整理版本，目标是把当前工具链收口为一套可以直接交付、直接复现、直接写入论文方法部分的基准测试工具。

## 本次发布重点

- 启动入口统一为现代 GUI，推荐使用 `启动工具.vbs`。
- GUI 已支持多规模勾选、进度条、ETA、日志保存/复制、结果目录直开。
- 开源库对比流程已纳入主界面，支持自动探测与安装。
- 结果目录统一为 `<时间戳>\<规模>\data\py2|py3|os` 结构。
- 数据规模梯度已重新校准，`large` 上限调整为旧版 `medium` 的一半。
- 报告输出统一为 `comparison_report.md / comparison_table.tex / comparison_data.csv / comparison_data.json`。
- README、快速开始、GUI 使用说明及扩展研究文档已按当前实现同步更新。

## v1.0.0 能力范围

### 主功能

- ArcGIS Desktop Python 2.7 与 ArcGIS Pro Python 3.x 基准对比。
- GeoPandas / Rasterio 开源方案三向对比。
- 五级数据规模：`tiny / small / standard / medium / large`。
- 多进程对比选项与进度心跳日志。
- 中文报告与论文友好的 LaTeX 表格输出。

### 主推荐入口

- `启动工具.vbs`
- `launch_gui.py`
- `launch_gui.bat`

### 保留的兼容入口

- `launch.vbs`
- `start_gui_hidden.vbs`
- `启动工具_系统Python.vbs`

## 与旧版说明相比的统一口径

- 不再使用旧版“五步向导”界面描述。
- 默认结果不再强调仓库内 `results\` 目录，而是以 `C:\temp\arcgis_benchmark_data` 为主输出根目录。
- 如果一次运行多个规模，则每个规模单独生成一套报告。
- GUI 中主要操作按钮为“开始测试”“停止测试”“打开生成结果文件夹”，而不是旧版“开始全自动测试”“导出报告”。

## 已知约束

- 主流程需要 ArcGIS Desktop 与 ArcGIS Pro 运行环境。
- 开源库对比仅在 Python 3.x 环境下可用。
- 桌面软件窗口 vs 独立解释器的扩展研究脚本仍保留旧式 `results\` 辅助目录，详见 `docs/DESKTOP_TEST_GUIDE.md`。

## 发布前建议复核

1. 使用 `启动工具.vbs` 运行一次 `tiny` 规模完整验证。
2. 检查 `C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\` 下四类报告文件是否完整。
3. 如需发布开源库对比能力，确认 Python 3.x 环境中 `geopandas / rasterio / shapely / pyogrio / numpy` 可用。
4. 如需附带命令行示例，确认 `python scripts\run_both_versions.py` 能正常执行。
