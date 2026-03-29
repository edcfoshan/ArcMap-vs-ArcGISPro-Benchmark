# 桌面软件 vs 独立解释器 测试指南

## 研究目标

对比四种运行方式的性能差异：
1. ✅ **独立 Python 2.7**（已完成）
2. ✅ **独立 Python 3.x**（已完成）
3. ⏳ **ArcMap Python 窗口**（需手动执行）
4. ⏳ **ArcGIS Pro Python 窗格**（需手动执行）

## 测试原理

### 为什么要做这个对比？

| 运行方式 | 特点 | 预期性能 |
|----------|------|----------|
| 独立解释器 | 无GUI开销，直接执行 | 最快 |
| 桌面软件内 | 有GUI、许可检查等开销 | 较慢 |

### 预期结果
- 独立解释器 > 桌面软件内运行
- 差距可能在 5-30% 之间
- 复杂任务差距可能更大

---

## 操作步骤

### 第一步：完成独立解释器测试（已完成）

使用 GUI 工具或命令行完成：
```bash
# Python 2.7
C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py

# Python 3.x
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py
```

结果文件：
- `results/raw/benchmark_results_py2.json`
- `results/raw/benchmark_results_py3.json`

---

### 第二步：ArcMap Python 窗口测试

#### 1. 打开 ArcMap
- 启动 ArcMap 10.x
- 等待完全加载

#### 2. 打开 Python 窗口
- 菜单：Geoprocessing > Python
- 或者按 `Ctrl + Alt + P`

#### 3. 执行测试脚本

**方法一：直接复制粘贴代码**

打开文件 `scripts/for_arcmap.py`，复制全部内容，粘贴到 ArcMap Python 窗口，按 Enter 执行。

**方法二：使用 import**

在 Python 窗口中输入：
```python
import sys
sys.path.insert(0, r"D:\测试arcmap与gispro的运行速度\arcgis_performance_benchmark")
exec(open(r"D:\测试arcmap与gispro的运行速度\arcgis_performance_benchmark\scripts\for_arcmap.py").read())
```

#### 4. 等待完成
- 测试会自动运行 12 项基准测试
- 每个测试会显示进度
- 完成后会提示结果保存位置

#### 5. 结果文件
- `results/raw/benchmark_results_arcmap.json`

---

### 第三步：ArcGIS Pro Python 窗格测试

#### 1. 打开 ArcGIS Pro
- 启动 ArcGIS Pro
- 可以新建一个空白项目

#### 2. 打开 Python 窗格
- 菜单：Analysis > Python
- 或者按 `Ctrl + 1`

#### 3. 执行测试脚本

**方法一：直接复制粘贴代码**

打开文件 `scripts/for_arcgis_pro.py`，复制全部内容，粘贴到 Pro Python 窗格，按 Enter 执行。

**方法二：使用 import**

在 Python 窗格中输入：
```python
import sys
sys.path.insert(0, r"D:\测试arcmap与gispro的运行速度\arcgis_performance_benchmark")
exec(open(r"D:\测试arcmap与gispro的运行速度\arcgis_performance_benchmark\scripts\for_arcgis_pro.py").read())
```

#### 4. 等待完成
- 测试会自动运行 12 项基准测试
- 完成后会提示结果保存位置

#### 5. 结果文件
- `results/raw/benchmark_results_arcgis_pro.json`

---

### 第四步：合并分析结果

当四种运行方式都测试完成后，运行合并分析工具：

```bash
# 使用 Python 3
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" desktop_automation\merge_desktop_results.py
```

或者双击 GUI 中的「合并桌面软件结果」按钮（如果有）。

生成的报告：
- `results/tables/desktop_comparison_report.md`
- `results/tables/desktop_comparison_data.csv`

---

## 数据规模建议

由于桌面软件内运行需要人工操作，建议使用**小型数据**：

编辑 `config/settings.py`：
```python
DATA_SCALE = 'small'  # 小型数据
TEST_RUNS = 1         # 只运行1次
WARMUP_RUNS = 0       # 无预热
```

这样每次测试约 5-10 分钟，便于操作。

---

## 预期研究成果

### 可以回答的问题

1. **桌面软件运行慢多少？**
   - ArcMap Python 窗口 vs 独立 Python 2.7
   - ArcGIS Pro Python 窗格 vs 独立 Python 3.x

2. **不同任务的差异？**
   - 简单任务（如字段计算）差异较小
   - 复杂任务（如叠加分析）差异较大

3. **实际建议**
   - 批量处理建议使用独立解释器
   - 交互式开发可以使用桌面软件

### 论文价值

- 为 GIS 自动化最佳实践提供数据支持
- 量化桌面软件的运行时开销
- 指导用户选择合适的运行方式

---

## 注意事项

1. **测试环境一致性**
   - 在同一台电脑上测试
   - 关闭其他占用资源的程序
   - 确保 ArcGIS 许可可用

2. **ArcMap 特定注意**
   - ArcMap 是 32 位程序，内存有限
   - 大型数据测试可能导致内存不足
   - 建议使用小型数据

3. **ArcGIS Pro 特定注意**
   - Pro 是 64 位，性能更好
   - 但需要更多内存

4. **结果可比性**
   - 确保使用相同的数据规模
   - 确保使用相同的循环次数
   - 记录测试时的系统状态

---

## 替代方案

如果自动化测试有困难，可以改为**手动记录**：

1. 在桌面软件中执行单个测试
2. 手动记录执行时间
3. 创建对比表格
4. 这种方法虽然繁琐，但更灵活

---

## 技术支持

如果在测试过程中遇到问题：
1. 检查 ArcGIS 许可是否正常
2. 检查 Python 路径是否正确
3. 检查数据文件是否存在
4. 查看错误日志排查问题
