# GUI 打包为 EXE 说明

## 适用范围

本说明面向 `v1.0.0` GUI 打包。仓库当前没有内置 `create_exe.py` 或 `convert_icon.py`，建议直接使用 `PyInstaller` 或 `auto-py-to-exe`。

> 说明：这里的 EXE 仅负责桌面 GUI，本仓库新增的中文验证网页 `verification_console/` 仍然是独立浏览器页面，不属于 EXE 打包主目标。

## 方法一：PyInstaller（推荐）

### 1. 安装依赖

```bash
pip install pyinstaller pillow
```

### 2. 确认图标文件

仓库已自带：

```text
resources\icon.ico
```

### 3. 在仓库根目录执行打包命令

```powershell
pyinstaller `
  --name ArcGISBenchmark-v1.0 `
  --windowed `
  --clean `
  --icon resources\icon.ico `
  --add-data "config;config" `
  --add-data "utils;utils" `
  --add-data "benchmarks;benchmarks" `
  --add-data "data;data" `
  --add-data "resources;resources" `
  benchmark_gui_modern.py
```

### 4. 产物位置

```text
dist\ArcGISBenchmark-v1.0.exe
```

如果改为非 `--onefile` 模式，则 `dist\ArcGISBenchmark-v1.0\` 目录下会包含完整运行文件。

## 方法二：auto-py-to-exe

```bash
pip install auto-py-to-exe
auto-py-to-exe
```

建议配置：

- Script Location：`benchmark_gui_modern.py`
- Onefile：按需选择
- Console Window：`Window Based`
- Icon：`resources\icon.ico`
- Additional Files：`config`、`utils`、`benchmarks`、`data`、`resources`

## 打包建议

### 建议优先打包 GUI 主程序

- 主目标是 `benchmark_gui_modern.py`
- 不需要把 `launch_gui.py`、`启动工具.vbs` 一起打进 EXE
- VBS 和 BAT 启动器更适合源码发布包，不是 EXE 主入口

### 发布前建议检查

1. EXE 能正常拉起 GUI。
2. GUI 中 Python 路径可手动选择。
3. `tiny` 规模测试能够跑通。
4. 结果目录与报告文件能正常生成。
5. 运行目录里能看到 `benchmark_run.log` 与 `benchmark_manifest.json`。

## 注意事项

1. ArcGIS 相关环境不一定能被完整静态打包，发布 EXE 时仍应说明需要本机具备 ArcGIS 环境。
2. 单文件 EXE 体积通常较大，首次启动也会更慢。
3. 杀毒软件可能会对 PyInstaller 产物误报，发布前最好做一次本机白名单验证。
