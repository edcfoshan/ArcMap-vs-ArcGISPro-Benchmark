# ArcGIS Python 2.7 vs Python 3.x 性能对比测试工具

## 项目简介

本工具用于对比分析 ArcGIS Desktop (Python 2.7) 与 ArcGIS Pro (Python 3.x) 在相同硬件环境下处理 GIS 数据的性能差异。

## 快速开始

### 1. 启动工具

双击启动（无黑窗口）：
```
启动工具.vbs
```

### 2. 运行测试

- 在 GUI 中选择数据规模（小型/中型/大型）
- 点击「开始全自动测试」按钮
- 等待测试完成

### 3. 导出报告

测试完成后，点击「导出报告」按钮选择保存位置。

## 测试内容

### 矢量数据测试 (6项)
| 测试项 | 说明 |
|--------|------|
| V1_CreateFishnet | 创建渔网多边形 |
| V2_CreateRandomPoints | 生成随机点 |
| V3_Buffer | 缓冲区分析 |
| V4_Intersect | 叠加分析 |
| V5_SpatialJoin | 空间连接 |
| V6_CalculateField | 字段计算 |

### 栅格数据测试 (4项)
| 测试项 | 说明 |
|--------|------|
| R1_CreateConstantRaster | 创建常量栅格 |
| R2_Resample | 栅格重采样 |
| R3_Clip | 栅格裁剪 |
| R4_RasterCalculator | 栅格计算 |

### 混合测试 (2项)
| 测试项 | 说明 |
|--------|------|
| M1_PolygonToRaster | 矢转栅 |
| M2_RasterToPoint | 栅转矢 |

## 数据规模

| 规模 | 数据量 | 预计时间 | 适用场景 |
|------|--------|----------|----------|
| 小型 | 标准1/10 | 5-10分钟 | 快速测试 |
| 中型 | 标准规模 | 30-60分钟 | 日常测试（推荐） |
| 大型 | 超大规格 | 2-4小时 | 学术论文 |

## 输出报告

测试完成后自动生成以下报告：

- **comparison_report.md** - Markdown格式报告（可直接阅读）
- **comparison_table.tex** - LaTeX表格（可直接插入论文）
- **comparison_data.csv** - Excel数据（可进一步分析）
- **comparison_data.json** - JSON原始数据

## 系统要求

- Windows 操作系统
- ArcGIS Desktop 10.x 或 ArcGIS Pro 3.x
- Python 2.7 和 Python 3.x 环境
- 建议 16GB 以上内存
- 磁盘空间：C:\temp 需要有足够空间（小型5GB / 中型20GB / 大型50GB）

## 数据存储

测试数据将存储在 `C:\temp\arcgis_benchmark_data`，而非软件目录：
- ✅ 便于统一管理临时数据
- ✅ 可随时手动删除清理
- ✅ 避免占用项目目录空间

测试结果（小文件）仍存储在软件目录的 `results` 文件夹中。

## 测试结果示例

```
测试项目          | Python 2.7 | Python 3.x | 加速比
------------------|------------|------------|--------
CreateFishnet     | 0.998s     | 1.040s     | 0.96x
CreateRandomPoints| 0.371s     | 0.437s     | 0.85x
Buffer            | 1.193s     | 1.088s     | 1.10x
Intersect         | 11.974s    | 7.463s     | 1.60x
SpatialJoin       | 5.130s     | 6.029s     | 0.85x
CalculateField    | 9.101s     | 6.746s     | 1.35x
------------------|------------|------------|--------
平均加速比        |            |            | 1.12x
```

## 许可证

本工具仅供学术研究使用。

## 作者

ArcGIS Python 性能研究小组
