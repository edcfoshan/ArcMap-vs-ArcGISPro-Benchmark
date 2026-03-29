#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Launcher for the GUI application
Selects the best available Python interpreter
"""
from __future__ import print_function
import sys
import os
import subprocess

PYTHON3_PATH = r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUI_SCRIPT = os.path.join(SCRIPT_DIR, "benchmark_gui.py")

def main():
    print("=" * 50)
    print("ArcGIS Python 性能对比测试工具启动器")
    print("=" * 50)
    
    # Try Python 3 first (better GUI support)
    if os.path.exists(PYTHON3_PATH):
        print("使用 ArcGIS Pro Python 3 启动 GUI...")
        python_exe = PYTHON3_PATH
    else:
        print("使用当前 Python 启动 GUI...")
        python_exe = sys.executable
    
    try:
        subprocess.call([python_exe, GUI_SCRIPT])
    except KeyboardInterrupt:
        print("\n用户取消")
    except Exception as e:
        print("启动失败: {}".format(e))
        input("按回车键退出...")

if __name__ == '__main__':
    main()
