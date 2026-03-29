@echo off
chcp 65001 >nul
echo ==========================================
echo 清理 ArcGIS Benchmark 临时数据
echo ==========================================
echo.

if exist "C:\temp\arcgis_benchmark_data" (
    echo 正在删除测试数据...
    rmdir /s /q "C:\temp\arcgis_benchmark_data"
    echo.
    echo ✅ 已清理: C:\temp\arcgis_benchmark_data
) else (
    echo 没有找到测试数据目录
)

echo.
pause
