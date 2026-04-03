# ArcGIS Python2、3 与开源库性能对比测试工具 - 简化版

## 怎么启动

直接双击：

```text
启动工具.vbs
```

## 怎么用

1. 确认 Python 2.7 和 Python 3.x 路径正确。
2. 勾选一个或多个数据规模。
3. 按需启用“多进程”或“开源库”。
4. 点击“开始测试”。
5. 完成后点击“打开生成结果文件夹”。

## 界面里最重要的几个位置

- 左侧：测试参数、规模选择、路径设置。
- 中间：总进度、当前任务、ETA。
- 下方日志区：实时输出详细执行信息。
- 日志工具栏：`Clear / Save / Copy`。

## 结果在哪

默认生成到：

```text
C:\temp\arcgis_benchmark_data\<时间戳>\<规模>\
```

每个规模目录下都会有：

- `comparison_report.md`
- `comparison_table.tex`
- `comparison_data.csv`
- `comparison_data.json`

## 规模怎么选

| 规模 | 建议用途 |
|------|----------|
| `tiny` | 先做一次快速验证 |
| `small` | 功能测试 |
| `standard` | 日常对比 |
| `medium` | 论文主实验 |
| `large` | 大样本正式实验 |

## 注意事项

1. 测试过程中不要关闭 ArcMap、ArcGIS Pro 或相关属性表窗口。
2. 如需开源库对比，必须保证 Python 3.x 环境中已安装相关依赖。
3. 如果遇到文件锁定，先关闭 GIS 软件，再清理 `C:\temp\arcgis_benchmark_data` 对应目录。
