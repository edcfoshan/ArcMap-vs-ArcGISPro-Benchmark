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
PYTHON27_PATH = r"C:\Python27\ArcGIS10.8\python.exe"
PYTHON3_PATH = r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


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
        
        # ===== Settings Panel =====
        settings_frame = ttk.LabelFrame(main_frame, text="测试设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Scale selection
        ttk.Label(settings_frame, text="数据规模:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=5)
        scale_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.data_scale_var,
            values=["tiny", "small", "medium", "large"],
            width=12,
            state="readonly",
            font=("Microsoft YaHei", 9)
        )
        scale_combo.pack(side=tk.LEFT, padx=5)
        
        # Scale description
        self.scale_desc_label = ttk.Label(
            settings_frame,
            text="超小: 极速验证，约1-2分钟",
            font=("Microsoft YaHei", 9),
            foreground="blue"
        )
        self.scale_desc_label.pack(side=tk.LEFT, padx=10)
        
        # Update description when scale changes
        scale_combo.bind("<<ComboboxSelected>>", self._update_scale_desc)
        
        # Runs
        ttk.Label(settings_frame, text="循环:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(30, 5))
        tk.Spinbox(
            settings_frame,
            from_=1,
            to=20,
            width=5,
            textvariable=self.runs_var,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT)
        ttk.Label(settings_frame, text="次", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=2)
        
        # Warmup
        ttk.Label(settings_frame, text="预热:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=(20, 5))
        tk.Spinbox(
            settings_frame,
            from_=0,
            to=5,
            width=5,
            textvariable=self.warmup_var,
            font=("Microsoft YaHei", 9)
        ).pack(side=tk.LEFT)
        ttk.Label(settings_frame, text="次", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=2)
        
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
            text="▶ 开始全自动测试",
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
        """Update scale description"""
        scale = self.data_scale_var.get()
        descs = {
            'tiny': '超小: 极速验证，约1-2分钟',
            'small': '小型: 快速测试，数据量为标准1/10',
            'medium': '中型: 标准测试规模（推荐）',
            'large': '大型: 学术论文级别，耗时较长'
        }
        self.scale_desc_label.config(text=descs.get(scale, ''))
    
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
        self._log("  • 测试数据：C:\\temp\\arcgis_benchmark_data")
        self._log("  • 测试结果：软件目录\\results")
        self._log("")
        self._log("预计耗时：")
        self._log("  • 超小数据：约 1-2 分钟 (快速验证)")
        self._log("  • 小型数据：约 5-10 分钟")
        self._log("  • 中型数据：约 30-60 分钟")
        self._log("  • 大型数据：约 2-4 小时")
        self._log("")
        self._log("提示：", "warning")
        self._log("  • 测试过程中请勿关闭 ArcGIS 相关程序", "warning")
        self._log("  • 测试数据存储在 C:\\temp，可随时手动删除", "warning")
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
            self._log("✓ 检测到两个 Python 环境", "success")
    
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
        self._log("━" * 70, "header")
        self._log("▶ {}".format(title), "header")
        self._log("━" * 70, "header")
    
    def _log_success(self, message):
        """Log success message"""
        self._log("✓ {}".format(message), "success")
    
    def _log_error(self, message):
        """Log error message"""
        self._log("✗ {}".format(message), "error")
    
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
                text="▶ 开始全自动测试",
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
            
            scale_names = {'tiny': '超小', 'small': '小型', 'medium': '中型', 'large': '大型'}
            self._log("设置已应用: {}数据, {}次循环, {}次预热".format(
                scale_names.get(scale, scale), runs, warmup
            ))
            return True
        except Exception as e:
            self._log("设置应用失败: {}".format(e), "error")
            return False
    
    def _run_command(self, cmd, task_name, check_stop=True):
        """Run command and stream output"""
        self.current_task = task_name
        self.current_process = None
        
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            for line in self.current_process.stdout:
                if self.should_stop and check_stop:
                    self._log("收到停止信号，正在终止当前任务...", "warning")
                    self.current_process.terminate()
                    try:
                        self.current_process.wait(timeout=5)
                    except:
                        self.current_process.kill()
                    return False
                
                line = line.strip()
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
    
    def _run_full_test_sequence(self):
        """Run complete test sequence"""
        try:
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
            self._log("生成的报告文件：", "success")
            self._log("  • comparison_report.md - Markdown报告")
            self._log("  • comparison_table.tex - LaTeX表格")
            self._log("  • comparison_data.csv - Excel数据")
            self._log("")
            self._log("点击「导出报告」按钮可导出到指定位置", "success")
            
            self.export_btn.config(state=tk.NORMAL)
            messagebox.showinfo("测试完成", "所有测试步骤已成功完成！\n\n点击「导出报告」按钮可导出报告。")
            
        except Exception as e:
            if self.should_stop:
                self._log("")
                self._log("━" * 70, "warning")
                self._log("▶ 测试已停止", "warning")
                self._log("━" * 70, "warning")
                self._log("")
                self._log("已完成的步骤可以正常使用：", "info")
                self._log("  • 如果步骤2完成，测试数据已生成", "info")
                self._log("  • 如果步骤3或4完成，可以导出部分结果", "info")
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
            self._log("✓ Python 2.7: {}".format(version))
        else:
            errors.append("Python 2.7 未找到")
            self._log_error("Python 2.7 未找到: {}".format(PYTHON27_PATH))
        
        # Check Python 3.x
        if os.path.exists(PYTHON3_PATH):
            result = subprocess.run([PYTHON3_PATH, "--version"], capture_output=True, text=True)
            version = result.stdout.strip() or result.stderr.strip()
            self._log("✓ Python 3.x: {}".format(version))
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
                    self._log("✓ arcpy ({}): 可用".format(name))
                else:
                    errors.append("{}: arcpy 不可用".format(name))
        
        if errors:
            self._log_error("环境检查失败，请检查 ArcGIS 安装")
            return False
        
        self._log_success("环境验证通过")
        return True
    
    def _step2_generate_data(self):
        """Step 2: Generate test data"""
        py_path = PYTHON3_PATH if os.path.exists(PYTHON3_PATH) else PYTHON27_PATH
        cmd = [py_path, os.path.join(SCRIPT_DIR, "data", "generate_test_data.py")]
        
        if self._run_command(cmd, "生成测试数据"):
            self._log_success("测试数据生成完成")
            return True
        else:
            self._log_error("测试数据生成失败")
            self._log("提示：请关闭所有 ArcGIS 程序后重试", "warning")
            return False
    
    def _step3_py27_test(self):
        """Step 3: Python 2.7 test"""
        if not os.path.exists(PYTHON27_PATH):
            self._log_error("Python 2.7 未找到")
            return False
        
        cmd = [PYTHON27_PATH, os.path.join(SCRIPT_DIR, "run_benchmarks.py")]
        
        if self._run_command(cmd, "Python 2.7 测试"):
            self._log_success("Python 2.7 测试完成")
            return True
        else:
            self._log_error("Python 2.7 测试失败")
            return False
    
    def _step4_py3_test(self):
        """Step 4: Python 3.x test"""
        if not os.path.exists(PYTHON3_PATH):
            self._log_error("Python 3.x 未找到")
            return False
        
        cmd = [PYTHON3_PATH, os.path.join(SCRIPT_DIR, "run_benchmarks.py")]
        
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
