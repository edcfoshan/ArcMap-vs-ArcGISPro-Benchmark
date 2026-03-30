#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ArcGIS Python Performance Benchmark - Simple GUI
简化版图形界面，一键自动运行
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import subprocess
import threading
import json
import re
import shutil
import webbrowser
from datetime import datetime

# Python 2/3 compatibility for tkinter
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
except ImportError:
    import Tkinter as tk
    import ttk
    from ScrolledText import ScrolledText
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Default Python paths (will be auto-detected if possible)
DEFAULT_PYTHON27_PATH = r"C:\Python27\ArcGIS10.8\python.exe"
DEFAULT_PYTHON3_PATH = r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"


def find_python27():
    """Auto-detect Python 2.7 installation"""
    # Check common locations
    possible_paths = [
        r"C:\Python27\ArcGIS10.8\python.exe",
        r"C:\Python27\ArcGIS10.7\python.exe",
        r"C:\Python27\ArcGIS10.6\python.exe",
        r"C:\Python27\python.exe",
        r"C:\Python27\ArcGIS10.5\python.exe",
    ]
    
    # Check environment variable
    if 'PYTHON27_PATH' in os.environ:
        possible_paths.insert(0, os.environ['PYTHON27_PATH'])
    
    # Check config file
    config_file = os.path.join(SCRIPT_DIR, 'python_paths.config')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith('PYTHON27='):
                        path = line.split('=', 1)[1].strip()
                        possible_paths.insert(0, path)
        except:
            pass
    
    # Return first existing path
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def find_python3():
    """Auto-detect Python 3.x (ArcGIS Pro) installation"""
    # Check common locations
    possible_paths = [
        r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe",
        r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3-clone\python.exe",
        r"C:\ProgramData\Anaconda3\envs\arcgispro-py3\python.exe",
    ]
    
    # Check environment variable
    if 'PYTHON3_PATH' in os.environ:
        possible_paths.insert(0, os.environ['PYTHON3_PATH'])
    
    # Check config file
    config_file = os.path.join(SCRIPT_DIR, 'python_paths.config')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith('PYTHON3='):
                        path = line.split('=', 1)[1].strip()
                        possible_paths.insert(0, path)
        except:
            pass
    
    # Return first existing path
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


# Auto-detect Python paths
PYTHON27_PATH = find_python27() or DEFAULT_PYTHON27_PATH
PYTHON3_PATH = find_python3() or DEFAULT_PYTHON3_PATH


class SimpleBenchmarkGUI(object):
    """Simplified GUI - One click to run all"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ArcGIS Python 性能对比测试工具")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        # State variables
        self.is_running = False
        self.current_task = ""
        self.should_stop = False
        self.current_process = None
        
        # Settings variables
        self.runs_var = tk.StringVar(value="3")
        self.warmup_var = tk.StringVar(value="0")
        self.data_scale_var = tk.StringVar(value="tiny")
        
        # Create UI
        self._create_ui()
        
        # Set close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Initial log
        self._log_banner()
        self._check_environment()
    
    def _create_ui(self):
        """Create simplified UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== Header =====
        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header,
            text="ArcGIS Python 2.7 vs Python 3.x 性能对比测试",
            font=("Microsoft YaHei", 16, "bold")
        ).pack()
        
        ttk.Label(
            header,
            text="一键自动完成全部测试流程",
            font=("Microsoft YaHei", 10),
            foreground="gray"
        ).pack()
        
        # ===== Settings Panel (Two Rows) =====
        settings_frame = ttk.LabelFrame(main_frame, text="测试设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Row 1: Data scale selection + All scales button + Description
        row1_frame = ttk.Frame(settings_frame)
        row1_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(row1_frame, text="数据规模:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        
        # Scale data mapping
        self.scale_data = {
            'tiny': {'name': '超小', 'fishnet': '2,500', 'raster': '25万', 'time': '1-2分钟'},
            'small': {'name': '小型', 'fishnet': '10,000', 'raster': '100万', 'time': '5-10分钟'},
            'standard': {'name': '标准', 'fishnet': '250,000', 'raster': '2,500万', 'time': '15-30分钟'},
            'medium': {'name': '中型', 'fishnet': '1,000,000', 'raster': '1亿', 'time': '30-60分钟'},
            'large': {'name': '大型', 'fishnet': '25,000,000', 'raster': '9亿', 'time': '2-4小时'}
        }
        
        scale_combo = ttk.Combobox(
            row1_frame,
            textvariable=self.data_scale_var,
            values=["tiny", "small", "standard", "medium", "large"],
            width=12,
            state="readonly",
            font=("Microsoft YaHei", 9)
        )
        scale_combo.pack(side=tk.LEFT, padx=5)
        
        # All scales run button (moved from bottom button area)
        self.all_scales_btn = tk.Button(
            row1_frame,
            text="🔄 五级连跑",
            font=("Microsoft YaHei", 9, "bold"),
            bg="#FF9800",
            fg="white",
            activebackground="#F57C00",
            command=self._start_all_scales_test,
            height=1,
            width=12,
            cursor="hand2"
        )
        self.all_scales_btn.pack(side=tk.LEFT, padx=10)
        
        # Scale description with data volume
        self.scale_desc_label = ttk.Label(
            row1_frame,
            text="超小: 渔网2,500 | 栅格25万 | 1-2分钟",
            font=("Microsoft YaHei", 9),
            foreground="blue"
        )
        self.scale_desc_label.pack(side=tk.LEFT, padx=10)
        
        # Update description when scale changes
        scale_combo.bind("<<ComboboxSelected>>", self._update_scale_desc)
        
        # Row 2: Test options (Runs, Warmup, Multiprocess, Open-source)
        row2_frame = ttk.Frame(settings_frame)
        row2_frame.pack(fill=tk.X)
        
        # Runs
        ttk.Label(row2_frame, text="循环:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        tk.Spinbox(
            row2_frame,
            from_=1,
            to=20,
            width=5,
            textvariable=self.runs_var,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT)
        ttk.Label(row2_frame, text="次", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(2, 15))
        
        # Warmup
        ttk.Label(row2_frame, text="预热:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        tk.Spinbox(
            row2_frame,
            from_=0,
            to=5,
            width=5,
            textvariable=self.warmup_var,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT)
        ttk.Label(row2_frame, text="次", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(2, 15))
        
        # Multiprocess options
        self.mp_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            row2_frame,
            text="多进程对比",
            variable=self.mp_var,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        self.mp_workers_var = tk.StringVar(value="4")
        ttk.Label(row2_frame, text="进程数:", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(2, 2))
        tk.Spinbox(
            row2_frame,
            from_=2,
            to=16,
            width=4,
            textvariable=self.mp_workers_var,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        # Open-source options (Python 3.x only)
        self.opensource_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            row2_frame,
            text="开源包对比",
            variable=self.opensource_var,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        # ===== Log Window (Main Focus) =====
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Log text with larger font
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state=tk.DISABLED,
            bg="#f8f8f8"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Tag configurations for colors
        self.log_text.tag_configure("header", foreground="#0066cc", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("success", foreground="#009900", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("error", foreground="#cc0000", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("warning", foreground="#ff6600")
        self.log_text.tag_configure("info", foreground="#333333")
        self.log_text.tag_configure("progress", foreground="#0066cc")
        
        # ===== Control Buttons =====
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # Start button (Large)
        self.start_btn = tk.Button(
            btn_frame,
            text=">>> 开始全自动测试",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            command=self._start_full_test,
            height=2,
            cursor="hand2"
        )
        self.start_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Export button
        self.export_btn = tk.Button(
            btn_frame,
            text="📄 导出报告",
            font=("Microsoft YaHei", 11),
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            command=self._export_report,
            height=2,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings button
        self.settings_btn = tk.Button(
            btn_frame,
            text="⚙️ 设置",
            font=("Microsoft YaHei", 11),
            bg="#9E9E9E",
            fg="white",
            activebackground="#757575",
            command=self._show_settings,
            height=2,
            cursor="hand2"
        )
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear log button
        ttk.Button(
            btn_frame,
            text="清空日志",
            command=self._clear_log
        ).pack(side=tk.RIGHT, padx=5)
        
        # ===== Status Bar =====
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, borderwidth=1)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(
            status_frame,
            text="就绪 - 点击「开始全自动测试」按钮开始",
            font=("Microsoft YaHei", 9),
            padding=(5, 3)
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(side=tk.RIGHT, padx=5, pady=3)
    
    def _update_scale_desc(self, event=None):
        """Update scale description with data volume"""
        scale = self.data_scale_var.get()
        data = self.scale_data.get(scale, {})
        if data:
            text = "{name}: 渔网{fishnet} | 栅格{raster} | {time}".format(**data)
            self.scale_desc_label.config(text=text)
    
    def _log_banner(self):
        """Display welcome banner"""
        self._log("=" * 70, "header")
        self._log("  ArcGIS Python 性能对比测试工具", "header")
        self._log("=" * 70, "header")
        self._log("")
        self._log("本工具将自动完成以下流程：")
        self._log("  1. 验证 Python 2.7 和 Python 3.x 环境")
        self._log("  2. 生成测试数据（渔网、随机点、栅格等）")
        self._log("  3. 使用 Python 2.7 运行基准测试")
        self._log("  4. 使用 Python 3.x 运行基准测试")
        self._log("  5. 分析结果并生成对比报告")
        self._log("")
        self._log("数据存储位置：")
        self._log("  - 测试数据：C:\\temp\\arcgis_benchmark_data")
        self._log("  - 测试结果：软件目录\\results")
        self._log("")
        self._log("预计耗时：")
        self._log("  - 超小数据：约 1-2 分钟 (快速验证)")
        self._log("  - 小型数据：约 5-10 分钟")
        self._log("  - 标准数据：约 15-30 分钟")
        self._log("  - 中型数据：约 30-60 分钟")
        self._log("  - 大型数据：约 2-4 小时")
        self._log("")
        self._log("提示：", "warning")
        self._log("  - 测试过程中请勿关闭 ArcGIS 相关程序", "warning")
        self._log("  - 测试数据存储在 C:\\temp，可随时手动删除", "warning")
        self._log("")
        self._log("点击「开始全自动测试」按钮开始...", "success")
        self._log("")
    
    def _check_environment(self):
        """Quick environment check"""
        py27_ok = os.path.exists(PYTHON27_PATH)
        py3_ok = os.path.exists(PYTHON3_PATH)
        
        if not py27_ok:
            self._log("⚠ 警告: Python 2.7 未找到: {}".format(PYTHON27_PATH), "warning")
        if not py3_ok:
            self._log("⚠ 警告: Python 3.x 未找到: {}".format(PYTHON3_PATH), "warning")
        
        if py27_ok and py3_ok:
            self._log("[OK] 检测到两个 Python 环境", "success")
    
    def _show_settings(self):
        """Show settings dialog for Python paths and open-source packages"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("650x420")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (650 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (420 // 2)
        settings_window.geometry("+{}+{}".format(x, y))
        
        # ===== Python Paths Section =====
        paths_frame = ttk.LabelFrame(settings_window, text="Python 路径设置", padding="10")
        paths_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Python 2.7 path
        ttk.Label(paths_frame, text="Python 2.7:", font=("Microsoft YaHei", 10)).pack(pady=(5, 5), anchor=tk.W)
        
        py27_frame = ttk.Frame(paths_frame)
        py27_frame.pack(fill=tk.X)
        
        py27_var = tk.StringVar(value=PYTHON27_PATH)
        py27_entry = ttk.Entry(py27_frame, textvariable=py27_var, font=("Consolas", 9))
        py27_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_py27():
            path = filedialog.askopenfilename(
                title="选择 Python 2.7 可执行文件",
                filetypes=[("Python Executable", "python.exe"), ("All Files", "*.*")]
            )
            if path:
                py27_var.set(path)
        
        ttk.Button(py27_frame, text="浏览...", command=browse_py27).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Python 3.x path
        ttk.Label(paths_frame, text="Python 3.x:", font=("Microsoft YaHei", 10)).pack(pady=(10, 5), anchor=tk.W)
        
        py3_frame = ttk.Frame(paths_frame)
        py3_frame.pack(fill=tk.X)
        
        py3_var = tk.StringVar(value=PYTHON3_PATH)
        py3_entry = ttk.Entry(py3_frame, textvariable=py3_var, font=("Consolas", 9))
        py3_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def browse_py3():
            path = filedialog.askopenfilename(
                title="选择 Python 3.x 可执行文件",
                filetypes=[("Python Executable", "python.exe"), ("All Files", "*.*")]
            )
            if path:
                py3_var.set(path)
        
        ttk.Button(py3_frame, text="浏览...", command=browse_py3).pack(side=tk.RIGHT, padx=(5, 0))
        
        # ===== Open Source Packages Section =====
        os_frame = ttk.LabelFrame(settings_window, text="开源库管理 (Python 3.x)", padding="10")
        os_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status label
        self.os_status_var = tk.StringVar(value="点击'检查开源包'查看安装状态")
        os_status_label = ttk.Label(
            os_frame, 
            textvariable=self.os_status_var,
            font=("Microsoft YaHei", 9),
            foreground="gray"
        )
        os_status_label.pack(pady=(0, 10), anchor=tk.W)
        
        # Buttons frame
        os_btn_frame = ttk.Frame(os_frame)
        os_btn_frame.pack(fill=tk.X)
        
        def check_os_packages():
            """Check which open-source packages are installed"""
            if not os.path.exists(py3_var.get()):
                messagebox.showerror("错误", "Python 3.x 路径无效，请先设置正确的路径")
                return
            
            required_packages = ['geopandas', 'rasterio', 'shapely', 'numpy', 'pyproj']
            missing = []
            installed = []
            
            for pkg in required_packages:
                try:
                    # Try to import using Python 3
                    cmd = [py3_var.get(), "-c", "import {}".format(pkg)]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        installed.append(pkg)
                    else:
                        missing.append(pkg)
                except Exception:
                    missing.append(pkg)
            
            if missing:
                self.os_status_var.set("缺少包: {}".format(", ".join(missing)))
                os_status_label.config(foreground="red")
                
                msg = "检测到以下开源包未安装:\n\n"
                msg += "\n".join(["  • " + pkg for pkg in missing])
                msg += "\n\n已安装:\n"
                msg += "\n".join(["  ✓ " + pkg for pkg in installed]) if installed else "  (无)"
                msg += "\n\n是否需要联网下载并安装这些包？"
                
                if messagebox.askyesno("开源包检查", msg):
                    install_os_packages(missing)
            else:
                self.os_status_var.set("所有开源包已安装 ✓")
                os_status_label.config(foreground="green")
                messagebox.showinfo("开源包检查", "✓ 所有开源包已正确安装！\n\n" + 
                                   "\n".join(["  ✓ " + pkg for pkg in installed]))
        
        def install_os_packages(packages=None):
            """Install open-source packages using pip"""
            if not os.path.exists(py3_var.get()):
                messagebox.showerror("错误", "Python 3.x 路径无效，请先设置正确的路径")
                return
            
            # If no specific packages provided, check first
            if packages is None:
                check_os_packages()
                return
            
            # Confirm installation
            pkg_list = ", ".join(packages)
            if not messagebox.askyesno("确认安装", 
                "将使用 pip 安装以下包:\n\n{}\n\n".format(pkg_list) +
                "这将从互联网下载并安装，可能需要几分钟时间。\n" +
                "安装完成后请重新检查。\n\n是否继续？"):
                return
            
            # Show progress dialog
            progress_window = tk.Toplevel(settings_window)
            progress_window.title("安装开源包")
            progress_window.geometry("450x300")
            progress_window.transient(settings_window)
            progress_window.grab_set()
            
            # Center
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (450 // 2)
            y = (progress_window.winfo_screenheight() // 2) - (300 // 2)
            progress_window.geometry("+{}+{}".format(x, y))
            
            ttk.Label(progress_window, text="正在安装开源包...", 
                     font=("Microsoft YaHei", 11, "bold")).pack(pady=(15, 10))
            
            # Python 2/3 compatibility for scrolledtext
            try:
                from tkinter.scrolledtext import ScrolledText
            except ImportError:
                from ScrolledText import ScrolledText
            
            progress_text = ScrolledText(
                progress_window, wrap=tk.WORD, font=("Consolas", 9), height=10
            )
            progress_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            close_btn = ttk.Button(progress_window, text="关闭", command=progress_window.destroy)
            close_btn.pack(pady=10)
            close_btn.config(state=tk.DISABLED)
            
            def do_install():
                success_count = 0
                failed_packages = []
                
                for pkg in packages:
                    progress_text.insert(tk.END, "正在安装 {}...\n".format(pkg))
                    progress_text.see(tk.END)
                    progress_window.update()
                    
                    try:
                        # Use subprocess to install
                        cmd = [py3_var.get(), "-m", "pip", "install", pkg, "--user"]
                        result = subprocess.run(
                            cmd, capture_output=True, text=True,
                            timeout=300  # 5 minute timeout
                        )
                        
                        if result.returncode == 0:
                            progress_text.insert(tk.END, "  ✓ {} 安装成功\n".format(pkg))
                            success_count += 1
                        else:
                            progress_text.insert(tk.END, "  ✗ {} 安装失败\n".format(pkg))
                            progress_text.insert(tk.END, "    错误: {}\n".format(result.stderr[:200]))
                            failed_packages.append(pkg)
                    except subprocess.TimeoutExpired:
                        progress_text.insert(tk.END, "  ✗ {} 安装超时\n".format(pkg))
                        failed_packages.append(pkg)
                    except Exception as e:
                        progress_text.insert(tk.END, "  ✗ {} 安装出错: {}\n".format(pkg, str(e)))
                        failed_packages.append(pkg)
                    
                    progress_text.see(tk.END)
                    progress_window.update()
                
                progress_text.insert(tk.END, "\n" + "="*50 + "\n")
                progress_text.insert(tk.END, "安装完成: {}/{} 成功\n".format(success_count, len(packages)))
                if failed_packages:
                    progress_text.insert(tk.END, "失败: {}\n".format(", ".join(failed_packages)))
                    progress_text.insert(tk.END, "\n建议: 手动运行以下命令安装:\n")
                    progress_text.insert(tk.END, "{} -m pip install {} --user\n".format(
                        py3_var.get(), " ".join(failed_packages)))
                
                progress_text.see(tk.END)
                close_btn.config(state=tk.NORMAL)
                
                # Update status
                if success_count == len(packages):
                    self.os_status_var.set("所有开源包已安装 ✓")
                    os_status_label.config(foreground="green")
                elif success_count > 0:
                    self.os_status_var.set("部分安装 ({}/{})".format(success_count, len(packages)))
                    os_status_label.config(foreground="orange")
                else:
                    self.os_status_var.set("安装失败，请手动安装")
                    os_status_label.config(foreground="red")
            
            threading.Thread(target=do_install, daemon=True).start()
        
        ttk.Button(os_btn_frame, text="🔍 检查开源包", 
                  command=check_os_packages).pack(side=tk.LEFT, padx=5)
        ttk.Button(os_btn_frame, text="📥 安装开源包", 
                  command=lambda: install_os_packages(None)).pack(side=tk.LEFT, padx=5)
        
        # Required packages info
        ttk.Label(os_frame, text="所需包: geopandas, rasterio, shapely, numpy, pyproj", 
                 font=("Microsoft YaHei", 8), foreground="gray").pack(pady=(10, 0), anchor=tk.W)
        
        # ===== Bottom Buttons =====
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(pady=15)
        
        def save_settings():
            global PYTHON27_PATH, PYTHON3_PATH
            PYTHON27_PATH = py27_var.get()
            PYTHON3_PATH = py3_var.get()
            
            # Save to config file
            config_file = os.path.join(SCRIPT_DIR, 'python_paths.config')
            try:
                with open(config_file, 'w') as f:
                    f.write("PYTHON27={}\n".format(PYTHON27_PATH))
                    f.write("PYTHON3={}\n".format(PYTHON3_PATH))
                self._log("设置已保存", "success")
            except Exception as e:
                self._log("保存设置失败: {}".format(e), "error")
            
            settings_window.destroy()
            
            # Re-check environment
            self._check_environment()
        
        def test_paths():
            py27_ok = os.path.exists(py27_var.get())
            py3_ok = os.path.exists(py3_var.get())
            
            msg = "Python 2.7: {}\nPython 3.x: {}".format(
                "✓ 找到" if py27_ok else "✗ 未找到",
                "✓ 找到" if py3_ok else "✗ 未找到"
            )
            
            if py27_ok and py3_ok:
                messagebox.showinfo("路径检查", msg)
            else:
                messagebox.showwarning("路径检查", msg + "\n\n请检查路径设置。")
        
        ttk.Button(btn_frame, text="测试路径", command=test_paths).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Help text
        ttk.Label(
            settings_window, 
            text="提示: 也可以通过设置 PYTHON27_PATH 和 PYTHON3_PATH 环境变量来配置路径",
            font=("Microsoft YaHei", 8),
            foreground="gray"
        ).pack(pady=(5, 0))
    
    def _log(self, message, tag="info"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = "[{}] {}\n".format(timestamp, message)
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry, tag)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        print(log_entry.strip())
        self.root.update_idletasks()
    
    def _log_section(self, title):
        """Log section header"""
        self._log("")
        self._log("=" * 70, "header")
        self._log(">>> {}".format(title), "header")
        self._log("=" * 70, "header")
    
    def _log_success(self, message):
        """Log success message"""
        self._log("[OK] {}".format(message), "success")
    
    def _log_error(self, message):
        """Log error message"""
        self._log("[ERROR] {}".format(message), "error")
    
    def _set_running(self, running):
        """Set running state"""
        self.is_running = running
        if running:
            self.start_btn.config(
                text="⏹ 停止测试",
                bg="#f44336",
                activebackground="#d32f2f",
                command=self._stop_test
            )
            self.status_label.config(text="正在运行测试...")
            self.progress.start()
        else:
            self.start_btn.config(
                text=">>> 开始全自动测试",
                bg="#4CAF50",
                activebackground="#45a049",
                command=self._start_full_test
            )
            self.status_label.config(text="就绪")
            self.progress.stop()
    
    def _on_closing(self):
        """Handle window close"""
        if self.is_running:
            if messagebox.askyesno(
                "确认关闭",
                "测试正在运行中，确定要关闭吗？\n\n正在执行: {}".format(self.current_task),
                icon='warning'
            ):
                self.should_stop = True
                if self.current_process:
                    try:
                        self.current_process.terminate()
                        self.current_process.wait(timeout=3)
                    except:
                        try:
                            self.current_process.kill()
                        except:
                            pass
                self.root.destroy()
                os._exit(0)
        else:
            if messagebox.askyesno("确认关闭", "确定要退出程序吗？"):
                self.root.destroy()
                os._exit(0)
    
    def _kill_processes(self):
        """Kill running test processes"""
        # Only kill child processes of current test, not all Python
        # The flag should_stop will cause the thread to exit gracefully
        pass  # Let the thread handle graceful shutdown via should_stop flag
    
    def _stop_test(self):
        """Stop running test"""
        if messagebox.askyesno("确认停止", "确定要停止当前测试吗？\n\n已完成的步骤会保留结果。"):
            self.should_stop = True
            self._log("正在停止测试...", "warning")
            self._kill_processes()
            self._log("测试已停止", "warning")
            self._set_running(False)
            # Enable export button if we have results
            results_dir = os.path.join(SCRIPT_DIR, "results", "tables")
            if os.path.exists(results_dir) and os.listdir(results_dir):
                self.export_btn.config(state=tk.NORMAL)
    
    def _apply_settings(self):
        """Apply settings to config file"""
        try:
            runs = int(self.runs_var.get())
            warmup = int(self.warmup_var.get())
            scale = self.data_scale_var.get()
        except:
            runs, warmup, scale = 3, 1, 'medium'
        
        config_path = os.path.join(SCRIPT_DIR, "config", "settings.py")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = re.sub(r'TEST_RUNS\s*=\s*\d+', 'TEST_RUNS = {}'.format(runs), content)
            content = re.sub(r'WARMUP_RUNS\s*=\s*\d+', 'WARMUP_RUNS = {}'.format(warmup), content)
            content = re.sub(r"DATA_SCALE\s*=\s*['\"]\w+['\"]", "DATA_SCALE = '{}'".format(scale), content)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            scale_names = {'tiny': '超小', 'small': '小型', 'standard': '标准', 'medium': '中型', 'large': '大型'}
            self._log("设置已应用: {}数据, {}次循环, {}次预热".format(
                scale_names.get(scale, scale), runs, warmup
            ))
            return True
        except Exception as e:
            self._log("设置应用失败: {}".format(e), "error")
            return False
    
    def _run_command(self, cmd, task_name, check_stop=True):
        """Run command and stream output with proper encoding handling"""
        self.current_task = task_name
        self.current_process = None
        
        # Set environment to ensure UTF-8 output
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Read output line by line with encoding handling
            while True:
                if self.should_stop and check_stop:
                    self._log("收到停止信号，正在终止当前任务...", "warning")
                    self.current_process.terminate()
                    try:
                        self.current_process.wait(timeout=5)
                    except:
                        self.current_process.kill()
                    return False
                
                # Read raw bytes
                raw_line = self.current_process.stdout.readline()
                if not raw_line:
                    break
                
                # Try to decode with multiple encodings
                line = self._decode_line(raw_line)
                if line:
                    self._log(line)
            
            self.current_process.wait()
            return_code = self.current_process.returncode
            self.current_process = None
            return return_code == 0
            
        except Exception as e:
            self._log_error("执行失败: {}".format(e))
            return False
        finally:
            self.current_process = None
    
    def _decode_line(self, raw_bytes):
        """Decode bytes to string with multiple encoding attempts"""
        # Remove trailing newline
        raw_bytes = raw_bytes.rstrip(b'\n').rstrip(b'\r')
        if not raw_bytes:
            return None
        
        # Try encodings in order of preference
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'cp936', 'latin-1']
        
        for encoding in encodings:
            try:
                return raw_bytes.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        
        # If all fail, use replace mode with utf-8
        return raw_bytes.decode('utf-8', errors='replace')
    
    def _start_full_test(self):
        """Start full automated test"""
        self.should_stop = False
        self._set_running(True)
        self.export_btn.config(state=tk.DISABLED)
        
        # Clear previous log and show banner
        self._clear_log()
        self._log_banner()
        
        # Run in thread
        thread = threading.Thread(target=self._run_full_test_sequence)
        thread.daemon = True
        thread.start()
    
    def _start_all_scales_test(self):
        """Start test for all five scales sequentially"""
        if not messagebox.askyesno(
            "确认五级连跑",
            "这将依次运行所有五个数据规模（超小→小型→标准→中型→大型）。\n\n"
            "预计总耗时：\n"
            "  - 超小：1-2 分钟\n"
            "  - 小型：5-10 分钟\n"
            "  - 标准：15-30 分钟\n"
            "  - 中型：30-60 分钟\n"
            "  - 大型：2-4 小时\n\n"
            "总计约 4-6 小时，确定要继续吗？"
        ):
            return
        
        self.should_stop = False
        self._set_running(True)
        self.export_btn.config(state=tk.DISABLED)
        self.all_scales_btn.config(state=tk.DISABLED)
        
        # Clear previous log and show banner
        self._clear_log()
        
        # Run in thread
        thread = threading.Thread(target=self._run_all_scales_sequence)
        thread.daemon = True
        thread.start()
    
    def _run_all_scales_sequence(self):
        """Run tests for all scales sequentially"""
        from config import settings
        
        all_scales = ['tiny', 'small', 'standard', 'medium', 'large']
        scale_names = {
            'tiny': '超小数据',
            'small': '小型数据', 
            'standard': '标准数据',
            'medium': '中型数据',
            'large': '大型数据'
        }
        
        # Collect results from all scales
        all_scale_results = {}
        
        try:
            for i, scale in enumerate(all_scales, 1):
                if self.should_stop:
                    self._log("\n用户停止了测试", "warning")
                    break
                
                self._log_section("五级连跑 - {}/5: {}".format(i, scale_names.get(scale, scale)))
                
                # Update settings
                self.data_scale_var.set(scale)
                if not self._apply_settings_internal():
                    self._log_error("应用 {} 设置失败，跳过".format(scale))
                    continue
                
                # Run full test sequence for this scale
                success = self._run_single_scale_test(scale)
                
                if success:
                    # Store results path
                    all_scale_results[scale] = os.path.join(SCRIPT_DIR, "results", "tables")
                    self._log_success("{} 测试完成".format(scale_names.get(scale, scale)))
                else:
                    self._log_error("{} 测试失败".format(scale_names.get(scale, scale)))
                
                self._log("")
                self._log("=" * 70, "header")
                self._log("  {}/5 完成，{}后自动继续下一级别...".format(
                    i, "3秒" if i < len(all_scales) else "结束"
                ), "header")
                self._log("=" * 70, "header")
                self._log("")
                
                # Wait before next scale (except for last one)
                if i < len(all_scales) and not self.should_stop:
                    import time
                    time.sleep(3)
            
            # Generate comprehensive report
            if all_scale_results:
                self._generate_all_scales_report(all_scale_results)
            
            self._log_section("五级连跑完成")
            self._log_success("所有级别测试已完成！")
            
            # Show completion dialog
            self.root.after(0, lambda: self._show_all_scales_completion_dialog(all_scale_results))
            
        except Exception as e:
            self._log_error("五级连跑发生错误: {}".format(str(e)))
            import traceback
            self._log(traceback.format_exc())
        
        finally:
            self._set_running(False)
            self.all_scales_btn.config(state=tk.NORMAL)
    
    def _apply_settings_internal(self):
        """Apply settings without GUI feedback"""
        try:
            scale = self.data_scale_var.get()
            runs = int(self.runs_var.get())
            warmup = int(self.warmup_var.get())
            
            # Update config
            mp_enabled = self.mp_var.get()
            mp_workers = int(self.mp_workers_var.get())
            
            content = '''# -*- coding: utf-8 -*-
DATA_SCALE = '{}'
TEST_RUNS = {}
WARMUP_RUNS = {}
MULTIPROCESS_CONFIG = {{
    'enabled': {},
    'num_workers': {},
    'scales': ['standard', 'medium', 'large']
}}
'''.format(scale, runs, warmup, mp_enabled, mp_workers)
            
            config_path = os.path.join(SCRIPT_DIR, "config", "user_settings.py")
            with open(config_path, 'w') as f:
                f.write(content)
            
            return True
        except Exception:
            return False
    
    def _run_single_scale_test(self, scale):
        """Run full test sequence for a single scale"""
        try:
            # Clean old outputs
            self._cleanup_old_test_data()
            
            # Step 1: Check env
            if not self._step1_check_env():
                return False
            
            # Step 2: Generate data
            if not self._step2_generate_data():
                return False
            
            # Step 3: Python 2.7 test
            if self.should_stop:
                return False
            if not self._step3_py27_test():
                return False
            
            # Step 4: Python 3.x test
            if self.should_stop:
                return False
            if not self._step4_py3_test():
                return False
            
            # Step 5: Analyze
            if self.should_stop:
                return False
            if not self._step5_analyze():
                return False
            
            return True
            
        except Exception as e:
            self._log_error("测试过程错误: {}".format(str(e)))
            return False
    
    def _generate_all_scales_report(self, all_scale_results):
        """Generate comprehensive report comparing all scales"""
        try:
            import json
            
            output_dir = os.path.join(SCRIPT_DIR, "results", "tables")
            report_path = os.path.join(output_dir, "all_scales_comparison.md")
            
            lines = []
            lines.append("# ArcGIS Python 性能对比 - 全规模综合报告\n")
            lines.append("*生成时间：{}*\n".format(datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')))
            
            lines.append("## 测试规模汇总\n")
            lines.append("| 规模 | 渔网多边形 | 栅格像素 | 预计耗时 |")
            lines.append("|------|-----------|---------|---------|")
            
            scale_info = {
                'tiny': ('2,500 (50×50)', '25万', '1-2分钟'),
                'small': ('10,000 (100×100)', '100万', '5-10分钟'),
                'standard': ('250,000 (500×500)', '2500万', '15-30分钟'),
                'medium': ('1,000,000 (1000×1000)', '1亿', '30-60分钟'),
                'large': ('25,000,000 (5000×5000)', '9亿', '2-4小时')
            }
            
            for scale in ['tiny', 'small', 'standard', 'medium', 'large']:
                if scale in all_scale_results:
                    info = scale_info.get(scale, ('-', '-', '-'))
                    lines.append("| **{}** | {} | {} | {} |".format(scale.upper(), info[0], info[1], info[2]))
            
            lines.append("")
            
            # Add summary for each scale
            for scale in ['tiny', 'small', 'standard', 'medium', 'large']:
                if scale not in all_scale_results:
                    continue
                
                lines.append("## {} 规模详细结果\n".format(scale.upper()))
                
                # Load comparison data
                json_path = os.path.join(all_scale_results[scale], "comparison_data.json")
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    stats = data.get('statistics', {})
                    lines.append("- 测试项目总数: {}".format(stats.get('total_tests', 0)))
                    lines.append("- Python 3.x 更快: {} ({:.1f}%)".format(
                        stats.get('py3_faster', 0),
                        stats.get('py3_faster', 0) / stats.get('total_tests', 1) * 100
                    ))
                    lines.append("- Python 2.7 更快: {} ({:.1f}%)".format(
                        stats.get('py2_faster', 0),
                        stats.get('py2_faster', 0) / stats.get('total_tests', 1) * 100
                    ))
                    lines.append("- 平均加速比: {:.2f}x".format(stats.get('average_speedup', 0)))
                    lines.append("")
                
                lines.append("[查看详细报告](comparison_report.md)\n")
            
            lines.append("---")
            lines.append("*报告由 ArcGIS Python 性能对比测试工具自动生成*")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            self._log_success("全规模综合报告已生成: {}".format(report_path))
            
        except Exception as e:
            self._log_error("生成全规模报告失败: {}".format(str(e)))
    
    def _show_all_scales_completion_dialog(self, all_scale_results):
        """Show completion dialog for all scales test"""
        dialog = tk.Toplevel(self.root)
        dialog.title("五级连跑完成")
        dialog.geometry("450x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry("+{}+{}".format(x, y))
        
        # Message
        msg_frame = tk.Frame(dialog, padx=20, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True)
        
        completed = len(all_scale_results)
        tk.Label(
            msg_frame,
            text="五级连跑已完成！".format(completed),
            font=("Microsoft YaHei", 12, "bold"),
            fg="#4CAF50"
        ).pack(pady=(0, 10))
        
        tk.Label(
            msg_frame,
            text="已完成 {}/5 个级别的测试\n\n"
                 "每个级别的详细报告保存在 results/tables/ 目录\n"
                 "综合对比报告: all_scales_comparison.md".format(completed),
            font=("Microsoft YaHei", 9),
            wraplength=400,
            justify=tk.CENTER
        ).pack(pady=(0, 15))
        
        # Buttons frame
        btn_frame = tk.Frame(dialog, padx=20, pady=10)
        btn_frame.pack(fill=tk.X)
        
        def open_results():
            results_dir = os.path.join(SCRIPT_DIR, "results", "tables")
            if os.path.exists(results_dir):
                webbrowser.open(os.path.realpath(results_dir))
            dialog.destroy()
        
        def open_all_scales_md():
            md_path = os.path.join(SCRIPT_DIR, "results", "tables", "all_scales_comparison.md")
            if os.path.exists(md_path):
                webbrowser.open(md_path)
            dialog.destroy()
        
        tk.Button(
            btn_frame,
            text="打开结果文件夹",
            font=("Microsoft YaHei", 10),
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            command=open_results,
            width=14
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="打开综合报告",
            font=("Microsoft YaHei", 10),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            command=open_all_scales_md,
            width=14
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="关闭",
            font=("Microsoft YaHei", 10),
            command=dialog.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=5)
    
    def _cleanup_old_test_data(self):
        """Clean up old benchmark outputs but keep test data"""
        temp_data_dir = r"C:\temp\arcgis_benchmark_data"
        
        # Only delete output files (shp, gdb outputs) but keep input data
        # The input data will be checked and reused by generate_test_data.py
        if os.path.exists(temp_data_dir):
            self._log("清理旧的基准测试输出文件...")
            try:
                # Delete shapefile outputs from previous runs
                for item in os.listdir(temp_data_dir):
                    item_path = os.path.join(temp_data_dir, item)
                    # Delete V*_output.shp, V*_output files
                    if item.startswith("V") and "_output" in item:
                        try:
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path, ignore_errors=True)
                            else:
                                os.remove(item_path)
                            self._log("  删除: {}".format(item))
                        except:
                            pass
                self._log("[OK] 旧输出文件已清理（测试数据已保留）")
            except Exception as e:
                self._log("  警告: 清理时出错: {}".format(str(e)), "warning")
        else:
            self._log("无旧数据需要清理")
    
    def _run_full_test_sequence(self):
        """Run complete test sequence"""
        try:
            # Clean up old test data before starting
            self._cleanup_old_test_data()
            
            # Apply settings
            self._apply_settings()
            
            # Step 1: Environment check
            if self.should_stop:
                return
            self._log_section("步骤 1/5: 环境验证")
            if not self._step1_check_env():
                self._set_running(False)
                return
            
            # Step 2: Generate data
            if self.should_stop:
                return
            self._log_section("步骤 2/5: 生成测试数据")
            if not self._step2_generate_data():
                self._set_running(False)
                return
            
            # Step 3: Python 2.7 test
            if self.should_stop:
                return
            self._log_section("步骤 3/5: Python 2.7 基准测试")
            if not self._step3_py27_test():
                self._set_running(False)
                return
            
            # Step 4: Python 3.x test
            if self.should_stop:
                return
            self._log_section("步骤 4/5: Python 3.x 基准测试")
            if not self._step4_py3_test():
                self._set_running(False)
                return
            
            # Step 5: Analyze
            if self.should_stop:
                return
            self._log_section("步骤 5/5: 分析结果")
            if not self._step5_analyze():
                self._set_running(False)
                return
            
            # All done
            self._log_section("测试完成")
            self._log_success("所有测试步骤已成功完成！")
            self._log("")
            
            # Auto export to temp with timestamp
            export_success, export_path = self._auto_export_report()
            if export_success:
                self._log("自动导出位置: {}".format(export_path), "success")
            
            self._log("生成的报告文件：", "success")
            self._log("  - comparison_report.md - Markdown报告")
            self._log("  - comparison_table.tex - LaTeX表格")
            self._log("  - comparison_data.csv - Excel数据")
            self._log("")
            
            self.export_btn.config(state=tk.NORMAL)
            
            # Show custom dialog with two options
            self._show_completion_dialog(export_path)
            
        except Exception as e:
            if self.should_stop:
                self._log("")
                self._log("=" * 70, "warning")
                self._log(">>> 测试已停止", "warning")
                self._log("=" * 70, "warning")
                self._log("")
                self._log("已完成的步骤可以正常使用：", "info")
                self._log("  - 如果步骤2完成，测试数据已生成", "info")
                self._log("  - 如果步骤3或4完成，可以导出部分结果", "info")
                self._log("")
                self._log("点击「开始全自动测试」可从上次停止处继续", "info")
            else:
                self._log_error("发生错误: {}".format(str(e)))
                messagebox.showerror("错误", "测试过程中发生错误:\n{}".format(str(e)))
        
        finally:
            self._set_running(False)
    
    def _step1_check_env(self):
        """Step 1: Check environment"""
        errors = []
        
        # Check Python 2.7
        if os.path.exists(PYTHON27_PATH):
            result = subprocess.run([PYTHON27_PATH, "--version"], capture_output=True, text=True)
            version = result.stdout.strip() or result.stderr.strip()
            self._log("[OK] Python 2.7: {}".format(version))
        else:
            errors.append("Python 2.7 未找到")
            self._log_error("Python 2.7 未找到: {}".format(PYTHON27_PATH))
        
        # Check Python 3.x
        if os.path.exists(PYTHON3_PATH):
            result = subprocess.run([PYTHON3_PATH, "--version"], capture_output=True, text=True)
            version = result.stdout.strip() or result.stderr.strip()
            self._log("[OK] Python 3.x: {}".format(version))
        else:
            errors.append("Python 3.x 未找到")
            self._log_error("Python 3.x 未找到: {}".format(PYTHON3_PATH))
        
        # Check arcpy
        for py_path, name in [(PYTHON27_PATH, "Python 2.7"), (PYTHON3_PATH, "Python 3.x")]:
            if os.path.exists(py_path):
                result = subprocess.run(
                    [py_path, "-c", "import arcpy; print('OK')"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    self._log("[OK] arcpy ({}): 可用".format(name))
                else:
                    errors.append("{}: arcpy 不可用".format(name))
        
        if errors:
            self._log_error("环境检查失败，请检查 ArcGIS 安装")
            return False
        
        self._log_success("环境验证通过")
        return True
    
    def _step2_generate_data(self):
        """Step 2: Generate or reuse test data using Python 3.x"""
        scale = self.data_scale_var.get()
        self._log("检查/生成测试数据（规模: {}）...".format(scale.upper()))
        self._log("数据库: benchmark_data_{}.gdb".format(scale))
        self._log("")
        self._log("说明:")
        self._log("  - 如果数据已存在且规模匹配，将直接复用")
        self._log("  - 如需强制重新生成，请手动删除 C:\\temp\\arcgis_benchmark_data")
        
        if not os.path.exists(PYTHON3_PATH):
            self._log_error("Python 3.x 未找到，无法生成数据")
            return False
        
        self._log("\n检查/生成测试数据...")
        cmd = [PYTHON3_PATH, os.path.join(SCRIPT_DIR, "data", "generate_test_data.py")]
        
        if self._run_command(cmd, "生成测试数据"):
            self._log_success("测试数据准备完成")
            return True
        else:
            self._log_error("测试数据准备失败")
            self._log("提示：请关闭所有 ArcGIS 程序后重试", "warning")
            return False
    
    def _step3_py27_test(self):
        """Step 3: Python 2.7 test (单进程 + 多进程)"""
        if not os.path.exists(PYTHON27_PATH):
            self._log_error("Python 2.7 未找到")
            return False
        
        self._log("正在使用 Python 2.7 (ArcGIS Desktop) 执行基准测试...")
        self._log("测试项目: V1-V6 矢量测试, R1-R4 栅格测试, M1-M2 混合测试")
        
        cmd = [PYTHON27_PATH, os.path.join(SCRIPT_DIR, "run_benchmarks.py")]
        
        # 多进程测试
        if self.mp_var.get():
            cmd.extend(["--multiprocess", "--mp-workers", str(self.mp_workers_var.get())])
            self._log("已启用多进程对比测试（{}进程）".format(self.mp_workers_var.get()))
        
        if self._run_command(cmd, "Python 2.7 测试"):
            self._log_success("Python 2.7 测试完成")
            return True
        else:
            self._log_error("Python 2.7 测试失败")
            return False
    
    def _step4_py3_test(self):
        """Step 4: Python 3.x test (单进程 + 多进程 + 开源测试)"""
        """Step 4: Python 3.x test (单进程 + 多进程)"""
        """Step 4: Python 3.x test (单进程 + 多进程 + 开源测试)"""
        if not os.path.exists(PYTHON3_PATH):
            self._log_error("Python 3.x 未找到")
            return False
        
        self._log("正在使用 Python 3.x (ArcGIS Pro) 执行基准测试...")
        self._log("测试项目: V1-V6 矢量测试, R1-R4 栅格测试, M1-M2 混合测试")
        
        cmd = [PYTHON3_PATH, os.path.join(SCRIPT_DIR, "run_benchmarks.py")]
        
        # 多进程测试
        if self.mp_var.get():
            cmd.extend(["--multiprocess", "--mp-workers", str(self.mp_workers_var.get())])
            self._log("已启用多进程对比测试（{}进程）".format(self.mp_workers_var.get()))
        
        # 开源库测试
        if self.opensource_var.get():
            cmd.append("--opensource")
            self._log("已启用开源库对比测试 (GeoPandas/Rasterio)")
        
        if self._run_command(cmd, "Python 3.x 测试"):
            self._log_success("Python 3.x 测试完成")
            return True
        else:
            self._log_error("Python 3.x 测试失败")
            return False
    
    def _step5_analyze(self):
        """Step 5: Analyze results"""
        cmd = [sys.executable, os.path.join(SCRIPT_DIR, "analyze_results.py")]
        
        if self._run_command(cmd, "分析结果"):
            self._log_success("分析报告生成完成")
            return True
        else:
            self._log_error("分析报告生成失败")
            return False
    
    def _auto_export_report(self):
        """Auto export report to C:\temp with timestamp"""
        try:
            results_dir = os.path.join(SCRIPT_DIR, "results", "tables")
            if not os.path.exists(results_dir):
                return False, None
            
            # Create timestamped directory in temp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = os.path.join(r"C:\temp", "arcgis_benchmark_results_{}".format(timestamp))
            
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            copied = []
            for filename in os.listdir(results_dir):
                src = os.path.join(results_dir, filename)
                if os.path.isfile(src):
                    dst = os.path.join(export_dir, filename)
                    shutil.copy2(src, dst)
                    copied.append(filename)
            
            self._log_success("自动导出 {} 个文件到 temp".format(len(copied)))
            return True, export_dir
            
        except Exception as e:
            self._log_error("自动导出失败: {}".format(e))
            return False, None
    
    def _show_completion_dialog(self, export_path):
        """Show completion dialog with two options"""
        dialog = tk.Toplevel(self.root)
        dialog.title("测试完成")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry("+{}+{}".format(x, y))
        
        # Message
        msg_frame = tk.Frame(dialog, padx=20, pady=20)
        msg_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            msg_frame,
            text="所有测试步骤已成功完成！",
            font=("Microsoft YaHei", 12, "bold"),
            fg="#4CAF50"
        ).pack(pady=(0, 10))
        
        tk.Label(
            msg_frame,
            text="报告已自动导出到:\n{}".format(export_path if export_path else "导出失败"),
            font=("Microsoft YaHei", 9),
            wraplength=350,
            justify=tk.CENTER
        ).pack(pady=(0, 15))
        
        # Buttons frame
        btn_frame = tk.Frame(dialog, padx=20, pady=10)
        btn_frame.pack(fill=tk.X)
        
        def open_folder():
            if export_path and os.path.exists(export_path):
                webbrowser.open(os.path.realpath(export_path))
            dialog.destroy()
        
        def open_md():
            if export_path:
                md_path = os.path.join(export_path, "comparison_report.md")
                if os.path.exists(md_path):
                    webbrowser.open(md_path)
            dialog.destroy()
        
        tk.Button(
            btn_frame,
            text="打开报告文件夹",
            font=("Microsoft YaHei", 10),
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            command=open_folder,
            width=16
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="打开MD文件",
            font=("Microsoft YaHei", 10),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            command=open_md,
            width=14
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="关闭",
            font=("Microsoft YaHei", 10),
            command=dialog.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=5)
    
    def _export_report(self):
        """Export report to selected location"""
        export_dir = filedialog.askdirectory(title="选择导出目录")
        if not export_dir:
            return
        
        try:
            results_dir = os.path.join(SCRIPT_DIR, "results", "tables")
            if not os.path.exists(results_dir):
                messagebox.showerror("导出失败", "结果文件不存在，请先完成测试！")
                return
            
            self._log_section("导出报告")
            
            copied = []
            for filename in os.listdir(results_dir):
                src = os.path.join(results_dir, filename)
                dst = os.path.join(export_dir, filename)
                shutil.copy2(src, dst)
                copied.append(filename)
                self._log("已导出: {}".format(filename))
            
            self._log_success("成功导出 {} 个文件到:\n{}".format(len(copied), export_dir))
            messagebox.showinfo("导出成功", "已导出 {} 个文件".format(len(copied)))
            
        except Exception as e:
            self._log_error("导出失败: {}".format(e))
            messagebox.showerror("导出失败", str(e))
    
    def _clear_log(self):
        """Clear log window"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = SimpleBenchmarkGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
