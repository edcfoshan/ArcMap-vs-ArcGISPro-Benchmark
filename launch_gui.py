#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI launcher that prefers the ArcGIS Pro Python environment.
"""
from __future__ import print_function, division, absolute_import

import os
import subprocess


def find_python():
    """Find a suitable Python interpreter for launching the GUI."""
    candidates = [
        r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\pythonw.exe",
        r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe",
        r"C:\Python312\pythonw.exe",
        r"C:\Python311\pythonw.exe",
        r"C:\Python310\pythonw.exe",
        r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\pythonw.exe",
        r"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\pythonw.exe",
        r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\pythonw.exe",
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    try:
        for command in (['where', 'pythonw'], ['where', 'python']):
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().splitlines()[0]
    except Exception:
        pass

    return None


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    gui_script = os.path.join(script_dir, 'benchmark_gui_modern.py')

    python_path = find_python()
    if python_path:
        subprocess.Popen([python_path, gui_script], cwd=script_dir)
    else:
        subprocess.Popen(['python', gui_script], cwd=script_dir)


if __name__ == '__main__':
    main()
