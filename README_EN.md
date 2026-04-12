# ArcGIS Python2, Python3 & Open-Source Performance Benchmark Tool

> Current version: `v1.0.0`

## Overview

This tool performs unified benchmarking across three stacks on the same Windows machine:

- **ArcGIS Desktop** (Python 2.7 + arcpy)
- **ArcGIS Pro** (Python 3.x + arcpy)
- **Open-Source GIS** (GeoPandas + Rasterio + Shapely)

It generates reproducible reports in Markdown, LaTeX, CSV and JSON, suitable for academic papers, statistical analysis and result archiving.

`v1.0.0` is the first release-oriented version with a unified entry point, modern GUI, web verification console and cleaned-up output directory structure.

---

## Core Capabilities (v1.0)

- **6 core benchmark tasks** covering vector, raster and mixed operations.
- **Three-way comparison**: Python 2.7, Python 3.x and open-source libraries.
- **Modern Tkinter GUI** with multi-scale selection, progress bar, ETA, log copy/save and one-click result folder opening.
- **Local web console** for quick validation runs (tiny / small).
- **Five data scales**: `tiny`, `small`, `standard`, `medium`, `large`.
- **Multiprocess comparison** and open-source dependency detection / auto-installation.
- **Unified report exports**: Markdown, LaTeX, CSV, JSON.

---

## Two Entry Points

| Entry Point | File | Best For |
|-------------|------|----------|
| **Main GUI** | `ArcGIS基准测试工具.vbs` | Full custom benchmark runs with all parameters |
| **Web Console** | `打开网页控制台.bat` | Quick validation (tiny / small), environment smoke-test |

### Main GUI

1. Double-click `ArcGIS基准测试工具.vbs`.
2. On first launch a dialog will show auto-detected Python 2.7 / Python 3.x paths. Confirm or click **Auto-detect**.
3. Select one or more data scales.
4. Optionally enable **Multiprocess** and/or **Open-Source** tests.
5. Click **Run Tests**.
6. When finished, click **Open Results Folder**.

### Web Console

1. Double-click `打开网页控制台.bat`.
2. Your browser opens `http://127.0.0.1:8765`.
3. Use the **Fast Preset** (1 run, 0 warmup, auto-generate data) for a quick smoke-test.
4. Click **Start Verification**.
5. Watch per-scale stage progress and logs in real time.
6. After completion, preview and download `comparison_report.md` directly from the page.

---

## System Requirements

### Mandatory

- Windows OS
- ArcGIS Desktop 10.x (Python 2.7)
- ArcGIS Pro 3.x (Python 3.x)
- ArcGIS Advanced license recommended

### Open-Source Dependencies (Python 3 only)

Install via GUI (click **Install Open-Source Packages**) or manually:

```bash
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" -m pip install geopandas rasterio shapely pyogrio numpy
```

### Recommended Hardware

| Scale | RAM | Notes |
|-------|-----|-------|
| `tiny` / `small` | 8 GB | Quick validation |
| `standard` | 16 GB | Regular full run (recommended) |
| `medium` / `large` | 32 GB+ | Heavy-load / overnight run |

---

## Where to Find Results

Every run creates a timestamped folder under the default output root `C:\temp\arcgis_benchmark_data`.

### Quick way: `latest.txt`

A `latest.txt` file is written to the output root after each run. Open it with any text editor to get the absolute path of the most recent result folder.

### Directory Layout

```text
C:\temp\arcgis_benchmark_data\
└── 20250412_143052\               <-- timestamp root
    ├── comparison_report.md         <-- cross-scale summary report
    ├── comparison_data.json
    ├── benchmark_results_py2.json   <-- raw Py2 results
    ├── benchmark_results_py3.json   <-- raw Py3 results
    ├── benchmark_results_os.json    <-- raw open-source results
    ├── tiny\                        <-- per-scale subfolder
    │   ├── comparison_report.md
    │   ├── benchmark_results_py2.json
    │   ├── benchmark_results_py3.json
    │   ├── benchmark_results_os.json
    │   ├── benchmark_run.log
    │   ├── benchmark_manifest.json
    │   └── data\                    <-- intermediate datasets (shp/gdb/tif)
    │       └── ...
    └── small\
        └── ...
```

Notes:

- **Root folder** (timestamp directory) keeps summary reports and JSON/CSV files for easy discovery.
- **`data/` subfolder** hosts intermediate GIS datasets (`.gdb`, `.shp`, `.tif`) so the root stays clean.
- Every scale folder contains `benchmark_manifest.json` with Python/dependency versions, Git commit hash, hardware info and random seed for reproducibility.

---

## Data Scales

| Scale | Typical Duration | Typical Use Case | Disk Usage |
|-------|------------------|------------------|------------|
| `tiny` | 5–10 min | Quick validation, debugging | ~500 MB |
| `small` | 20–40 min | Functional test, small full comparison | ~2 GB |
| `standard` | 1–3 h | Regular full run (recommended) | ~4–6 GB |
| `medium` | 3–8 h | Heavy-load comparison | ~8–12 GB |
| `large` | 6–16 h | Stress test / overnight run | ~12–20 GB |

### Key Parameters by Scale

| Scale | Fishnet rows×cols | Random points | Intersect features | Constant raster size |
|-------|-------------------|---------------|--------------------|----------------------|
| `tiny` | 50 × 50 | 1,000 | 10,000 + 10,000 | 500 |
| `small` | 125 × 125 | 12,500 | 125,000 + 125,000 | 1,250 |
| `standard` | 250 × 250 | 25,000 | 250,000 + 250,000 | 2,500 |
| `medium` | 375 × 375 | 37,500 | 375,000 + 375,000 | 3,750 |
| `large` | 500 × 500 | 50,000 | 500,000 + 500,000 | 5,000 |

---

## Command-Line Usage

### 1. Verify Environment

```bash
C:\Python27\ArcGIS10.8\python.exe test_setup.py
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" test_setup.py
```

### 2. Run a Single Stack

```bash
C:\Python27\ArcGIS10.8\python.exe run_benchmarks.py --scale standard
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale standard
```

### 3. Enable Open-Source Comparison

```bash
"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" run_benchmarks.py --scale standard --opensource
```

### 4. Common Parameters

```bash
python run_benchmarks.py --scale standard
python run_benchmarks.py --scale standard --opensource
python run_benchmarks.py --scale standard --multiprocess --mp-workers 4
python run_benchmarks.py --category vector --scale small
python run_benchmarks.py --scale standard --generate-data
```

---

## Troubleshooting

### 1. File Lock (`ERROR 000464`)

- Close ArcMap, ArcGIS Pro and any open attribute tables.
- Delete the corresponding test directory under `C:\temp\arcgis_benchmark_data` and retry.

### 2. Open-Source Libraries Missing

- In the GUI, the status label explicitly shows missing package names (e.g. `rasterio`, `shapely`).
- Click **Install Open-Source Packages** to fix automatically.
- Or run the `pip install` command shown above manually.

### 3. Python Not Found

- Make sure ArcGIS Desktop and ArcGIS Pro are properly installed.
- Re-specify the Python 2.7 and Python 3.x paths in the GUI settings.

### 4. Report Not Generated

- Ensure both `py2` and `py3` benchmarks completed successfully.
- If open-source was enabled, also verify that `data\os` contains result files.

### 5. Adjust Heartbeat Log Frequency

Edit `PROGRESS_HEARTBEAT_INTERVAL` in `config/settings.py`:

- `0` — disable heartbeat logs.
- Positive integer — output heartbeat every N seconds.

---

## Project Structure

```text
.
├── ArcGIS基准测试工具.vbs          Recommended GUI launcher
├── 打开网页控制台.bat               Web console launcher
├── benchmark_gui_modern.py         Main Tkinter GUI
├── verification_console/           Web console (Flask + static UI)
├── run_benchmarks.py               CLI runner
├── analyze_results.py              Report generator
├── config/settings.py              Global configuration
├── utils/settings_manager.py       GUI config & i18n manager
├── docs/                           Additional docs
└── README.md / QUICKSTART.md       Chinese docs
```

---

## License

This tool is intended for academic research and educational use.
