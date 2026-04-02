#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ArcGIS Python Performance Benchmark - Modern UI Design
现代化美观界面设计 - Material Design风格
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import subprocess
import threading
import json
import time
import webbrowser
from datetime import datetime, timedelta

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
except ImportError:
    import Tkinter as tk
    import ttk
    from ScrolledText import ScrolledText
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from utils.settings_manager import SettingsManager, get_text, DEFAULT_CONFIG

# 现代化配色方案 - Material Design
COLORS = {
    'bg_primary': '#f5f7fa',       # 主背景色 - 浅灰蓝
    'bg_secondary': '#ffffff',     # 卡片背景 - 纯白
    'bg_header': '#1a237e',        # 头部深蓝
    'accent_primary': '#3949ab',   # 主强调色 - 靛蓝
    'accent_secondary': '#5c6bc0', # 次强调色
    'accent_success': '#43a047',   # 成功绿
    'accent_warning': '#fb8c00',   # 警告橙
    'accent_danger': '#e53935',    # 危险红
    'text_primary': '#212121',     # 主文字 - 深灰
    'text_secondary': '#757575',   # 次文字 - 中灰
    'text_light': '#ffffff',       # 浅色文字
    'border': '#e0e0e0',           # 边框色
    'hover': '#e8eaf6',            # 悬停色
}


# 当前项目的 benchmark 数量用于 GUI 进度估算
DEFAULT_ARCPY_REGULAR_BENCHMARKS = 12
DEFAULT_ARCPY_MULTIPROCESS_BENCHMARKS = 5
DEFAULT_OS_REGULAR_BENCHMARKS = 12
DEFAULT_OS_MULTIPROCESS_BENCHMARKS = 5
OPEN_SOURCE_PACKAGES = ('geopandas', 'rasterio', 'shapely', 'pyogrio', 'numpy')


class ModernButton(tk.Canvas):
    """圆角按钮控件"""
    def __init__(self, parent, text, command=None, bg_color=None, fg_color=None,
                 width=120, height=40, radius=8, font_size=12, bold=True, **kwargs):
        self.bg_color = bg_color or COLORS['accent_primary']
        self.fg_color = fg_color or COLORS['text_light']
        self.hover_color = self._lighten_color(self.bg_color)
        self.pressed_color = self._darken_color(self.bg_color)
        self.command = command
        self.radius = radius

        super().__init__(parent, width=width, height=height, bg=parent.cget('bg'),
                        highlightthickness=0, cursor='hand2', **kwargs)

        self.font = ('Microsoft YaHei', font_size, 'bold' if bold else 'normal')
        self.text = text

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_press)
        self.bind('<ButtonRelease-1>', self._on_release)
        # 延迟绘制，等待 Canvas 尺寸确定
        self.after(10, lambda: self._draw_button(self.bg_color))

    def _lighten_color(self, hex_color, factor=0.15):
        """变亮颜色"""
        r = int(min(255, int(hex_color[1:3], 16) + 255 * factor))
        g = int(min(255, int(hex_color[3:5], 16) + 255 * factor))
        b = int(min(255, int(hex_color[5:7], 16) + 255 * factor))
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)

    def _darken_color(self, hex_color, factor=0.15):
        """变暗颜色"""
        r = int(max(0, int(hex_color[1:3], 16) - 255 * factor))
        g = int(max(0, int(hex_color[3:5], 16) - 255 * factor))
        b = int(max(0, int(hex_color[5:7], 16) - 255 * factor))
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)

    def _draw_button(self, color):
        """绘制圆角按钮"""
        self.delete('all')
        width = self.winfo_width()
        height = self.winfo_height()

        # 绘制圆角矩形
        self.create_rounded_rect(2, 2, width-2, height-2, self.radius, fill=color, outline='')

        # 添加文字
        self.create_text(width//2, height//2, text=self.text, fill=self.fg_color,
                        font=self.font, anchor='center')

    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """创建圆角矩形"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _on_enter(self, event):
        self._draw_button(self.hover_color)

    def _on_leave(self, event):
        self._draw_button(self.bg_color)

    def _on_press(self, event):
        self._draw_button(self.pressed_color)

    def _on_release(self, event):
        self._draw_button(self.hover_color)
        if self.command:
            self.command()

    def config(self, **kwargs):
        """配置按钮属性"""
        if 'text' in kwargs:
            self.text = kwargs['text']
            self._draw_button(self.bg_color)
        if 'state' in kwargs:
            state = kwargs['state']
            if state == 'disabled':
                self.unbind('<Enter>')
                self.unbind('<Leave>')
                self.unbind('<Button-1>')
                self.unbind('<ButtonRelease-1>')
                self.config(cursor='')
                # 灰色显示
                gray = '#9e9e9e'
                self.delete('all')
                width = self.winfo_width()
                height = self.winfo_height()
                self.create_rounded_rect(2, 2, width-2, height-2, self.radius, fill=gray, outline='')
                self.create_text(width//2, height//2, text=self.text, fill=self.fg_color,
                                font=self.font, anchor='center')
            elif state == 'normal':
                self.bind('<Enter>', self._on_enter)
                self.bind('<Leave>', self._on_leave)
                self.bind('<Button-1>', self._on_press)
                self.bind('<ButtonRelease-1>', self._on_release)
                self.config(cursor='hand2')
                self._draw_button(self.bg_color)


class CardFrame(tk.Frame):
    """卡片式框架"""
    def __init__(self, parent, title=None, **kwargs):
        super().__init__(parent, bg=COLORS['bg_secondary'], **kwargs)

        # 添加阴影效果（通过边框模拟）
        self.config(highlightbackground=COLORS['border'], highlightthickness=1)

        if title:
            self.title_label = tk.Label(
                self, text=title, bg=COLORS['bg_secondary'],
                fg=COLORS['accent_primary'], font=('Microsoft YaHei', 13, 'bold'),
                anchor='w', padx=15, pady=10
            )
            self.title_label.pack(fill='x')

            # 分隔线
            separator = tk.Frame(self, height=2, bg=COLORS['border'])
            separator.pack(fill='x', padx=15)


class SettingsDialog(tk.Toplevel):
    """设置对话框"""

    def __init__(self, parent, settings_manager):
        tk.Toplevel.__init__(self, parent)
        self.parent = parent
        self.sm = settings_manager
        self.title(self.sm.get_text('settings_title'))
        self.geometry("900x700")
        self.minsize(800, 600)
        self.configure(bg=COLORS['bg_primary'])

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self._create_styles()
        self._create_ui()
        self._load_settings()

        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry("+{}+{}".format(x, y))

    def _create_styles(self):
        """创建ttk样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 配置样式使用与主窗口一致的字体
        base_size = int(12 * self.sm.get('ui_settings.font_scale', 1.0))

        self.style.configure('Modern.TFrame', background=COLORS['bg_primary'])
        self.style.configure('Card.TFrame', background=COLORS['bg_secondary'])

        self.style.configure('Modern.TLabel',
                           background=COLORS['bg_primary'],
                           foreground=COLORS['text_primary'],
                           font=('Microsoft YaHei', base_size))

        self.style.configure('Modern.TButton',
                           font=('Microsoft YaHei', base_size),
                           padding=5)

        self.style.configure('Modern.TCheckbutton',
                           font=('Microsoft YaHei', base_size),
                           background=COLORS['bg_secondary'])

        self.style.configure('Modern.TLabelframe',
                           background=COLORS['bg_secondary'],
                           font=('Microsoft YaHei', base_size, 'bold'))

        self.style.configure('Modern.TLabelframe.Label',
                           font=('Microsoft YaHei', base_size, 'bold'),
                           background=COLORS['bg_secondary'])

    def _create_ui(self):
        """创建设置对话框UI - 简化版"""
        # 主容器
        main_frame = tk.Frame(self, bg=COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 简化为垂直布局，不使用Notebook
        canvas = tk.Canvas(main_frame, bg=COLORS['bg_primary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=COLORS['bg_primary'])

        content_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content_frame, anchor='nw', width=900)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 语言设置
        lang_frame = tk.LabelFrame(content_frame, text=self.sm.get_text('label_language'),
                                   bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                                   font=('Microsoft YaHei', 11, 'bold'), padx=10, pady=10)
        lang_frame.pack(fill=tk.X, pady=5, padx=5)
        self.lang_var = tk.StringVar(value=self.sm.get('language', 'zh'))
        tk.Radiobutton(lang_frame, text="中文", variable=self.lang_var, value='zh',
                      bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                      font=('Microsoft YaHei', 11), selectcolor=COLORS['accent_primary']).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(lang_frame, text="English", variable=self.lang_var, value='en',
                      bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                      font=('Microsoft YaHei', 11), selectcolor=COLORS['accent_primary']).pack(side=tk.LEFT, padx=10)

        # Python路径
        py_frame = tk.LabelFrame(content_frame, text="Python " + self.sm.get_text('menu_settings'),
                                bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                                font=('Microsoft YaHei', 11, 'bold'), padx=10, pady=10)
        py_frame.pack(fill=tk.X, pady=5, padx=5)

        py27_row = tk.Frame(py_frame, bg=COLORS['bg_secondary'])
        py27_row.pack(fill=tk.X, pady=3)
        tk.Label(py27_row, text='Python 2.7:', bg=COLORS['bg_secondary'], font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        self.py27_var = tk.StringVar(value=self.sm.get('python_paths.python27', ''))
        tk.Entry(py27_row, textvariable=self.py27_var, font=('Microsoft YaHei', 10), width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(py27_row, text=self.sm.get_text('btn_browse'), command=lambda: self._browse_python(self.py27_var), bg=COLORS['accent_secondary'], fg='white', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(py27_row, text=self.sm.get_text('btn_verify'), command=lambda: self._verify_python(self.py27_var.get(), '2.7'), bg=COLORS['accent_primary'], fg='white', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=2)

        py3_row = tk.Frame(py_frame, bg=COLORS['bg_secondary'])
        py3_row.pack(fill=tk.X, pady=3)
        tk.Label(py3_row, text='Python 3.x:', bg=COLORS['bg_secondary'], font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        self.py3_var = tk.StringVar(value=self.sm.get('python_paths.python3', ''))
        tk.Entry(py3_row, textvariable=self.py3_var, font=('Microsoft YaHei', 10), width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        tk.Button(py3_row, text=self.sm.get_text('btn_browse'), command=lambda: self._browse_python(self.py3_var), bg=COLORS['accent_secondary'], fg='white', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(py3_row, text=self.sm.get_text('btn_verify'), command=lambda: self._verify_python(self.py3_var.get(), '3.x'), bg=COLORS['accent_primary'], fg='white', font=('Microsoft YaHei', 9)).pack(side=tk.LEFT, padx=2)

        # 测试设置
        test_frame = tk.LabelFrame(content_frame, text=self.sm.get_text('settings_title'),
                                  bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                                  font=('Microsoft YaHei', 11, 'bold'), padx=10, pady=10)
        test_frame.pack(fill=tk.X, pady=5, padx=5)

        runs_row = tk.Frame(test_frame, bg=COLORS['bg_secondary'])
        runs_row.pack(fill=tk.X, pady=2)
        tk.Label(runs_row, text=self.sm.get_text('label_runs'), bg=COLORS['bg_secondary'], font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        self.runs_var = tk.IntVar(value=self.sm.get('test_settings.runs', 3))
        tk.Spinbox(runs_row, from_=1, to=10, textvariable=self.runs_var, width=8, font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=5)

        warmup_row = tk.Frame(test_frame, bg=COLORS['bg_secondary'])
        warmup_row.pack(fill=tk.X, pady=2)
        tk.Label(warmup_row, text=self.sm.get_text('label_warmup'), bg=COLORS['bg_secondary'], font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        self.warmup_var = tk.IntVar(value=self.sm.get('test_settings.warmup', 1))
        tk.Spinbox(warmup_row, from_=0, to=5, textvariable=self.warmup_var, width=8, font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=5)

        workers_row = tk.Frame(test_frame, bg=COLORS['bg_secondary'])
        workers_row.pack(fill=tk.X, pady=2)
        tk.Label(workers_row, text=self.sm.get_text('label_workers'), bg=COLORS['bg_secondary'], font=('Microsoft YaHei', 10)).pack(side=tk.LEFT)
        self.workers_var = tk.IntVar(value=self.sm.get('test_settings.mp_workers', 4))
        tk.Spinbox(workers_row, from_=1, to=16, textvariable=self.workers_var, width=8, font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=5)

        # 选项复选框
        self.mp_var = tk.BooleanVar(value=self.sm.get('test_settings.enable_multiprocess', False))
        cb_frame = tk.Frame(test_frame, bg='white', padx=10, pady=8, highlightbackground='black', highlightthickness=2)
        cb_frame.pack(fill=tk.X, pady=5)
        tk.Checkbutton(cb_frame, text=self.sm.get_text('chk_multiprocess'), variable=self.mp_var,
                      bg='white', fg=COLORS['text_primary'], font=('Microsoft YaHei', 12),
                      selectcolor='white', activebackground='white', cursor='hand2').pack(anchor=tk.W)

        self.os_var = tk.BooleanVar(value=self.sm.get('test_settings.enable_opensource', False))
        cb_frame2 = tk.Frame(test_frame, bg='white', padx=10, pady=8, highlightbackground='black', highlightthickness=2)
        cb_frame2.pack(fill=tk.X, pady=5)
        tk.Checkbutton(cb_frame2, text=self.sm.get_text('chk_opensource'), variable=self.os_var,
                      bg='white', fg=COLORS['text_primary'], font=('Microsoft YaHei', 12),
                      selectcolor='white', activebackground='white', cursor='hand2').pack(anchor=tk.W)

        # 数据规模
        scale_frame = tk.LabelFrame(content_frame, text=self.sm.get_text('label_scale'),
                                   bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                                   font=('Microsoft YaHei', 11, 'bold'), padx=10, pady=10)
        scale_frame.pack(fill=tk.X, pady=5, padx=5)

        scale_select = tk.Frame(scale_frame, bg=COLORS['bg_secondary'])
        scale_select.pack(fill=tk.X, pady=(0, 10))
        self.edit_scale_var = tk.StringVar(value=self.sm.get('test_settings.data_scale', 'tiny'))
        tk.OptionMenu(scale_select, self.edit_scale_var, 'tiny', 'small', 'standard', 'medium', 'large',
                     command=lambda _: self._load_scale_settings()).pack(side=tk.LEFT, padx=5)
        tk.Button(scale_select, text=self.sm.get_text('btn_reset'), bg=COLORS['accent_secondary'],
                 fg='white', font=('Microsoft YaHei', 9), command=self._reset_current_scale).pack(side=tk.LEFT, padx=10)

        # 参数设置区域
        self.scale_params_frame = tk.Frame(scale_frame, bg=COLORS['bg_secondary'])
        self.scale_params_frame.pack(fill=tk.X)

        self.scale_param_vars = {}
        params = [
            ('fishnet_rows', self.sm.get_text('param_fishnet')),
            ('random_points', self.sm.get_text('param_random_points')),
            ('buffer_points', self.sm.get_text('param_buffer')),
            ('intersect_features', self.sm.get_text('param_intersect')),
            ('spatial_join_points', self.sm.get_text('param_spatial_join')),
            ('calculate_field_records', self.sm.get_text('param_calculate')),
            ('constant_raster_size', self.sm.get_text('param_raster')),
        ]

        for key, label in params:
            row = tk.Frame(self.scale_params_frame, bg=COLORS['bg_secondary'])
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label, width=30, bg=COLORS['bg_secondary'],
                    font=('Microsoft YaHei', 10), anchor='w').pack(side=tk.LEFT)
            var = tk.IntVar()
            self.scale_param_vars[key] = var
            tk.Spinbox(row, from_=1, to=10000000, textvariable=var, width=12,
                      font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=5)

        self._load_scale_settings()

        # 结果设置
        result_frame = tk.LabelFrame(content_frame, text=self.sm.get_text('tab_results'),
                                    bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                                    font=('Microsoft YaHei', 11, 'bold'), padx=10, pady=10)
        result_frame.pack(fill=tk.X, pady=5, padx=5)

        self.save_py2_var = tk.BooleanVar(value=self.sm.get('result_settings.save_py2_results', True))
        r1 = tk.Frame(result_frame, bg='white', padx=10, pady=5, highlightbackground='black', highlightthickness=2)
        r1.pack(fill=tk.X, pady=3)
        tk.Checkbutton(r1, text=self.sm.get_text('chk_py2'), variable=self.save_py2_var,
                      bg='white', fg=COLORS['text_primary'], font=('Microsoft YaHei', 11),
                      selectcolor='white', activebackground='white').pack(anchor=tk.W)

        self.save_py3_var = tk.BooleanVar(value=self.sm.get('result_settings.save_py3_results', True))
        r2 = tk.Frame(result_frame, bg='white', padx=10, pady=5, highlightbackground='black', highlightthickness=2)
        r2.pack(fill=tk.X, pady=3)
        tk.Checkbutton(r2, text=self.sm.get_text('chk_py3'), variable=self.save_py3_var,
                      bg='white', fg=COLORS['text_primary'], font=('Microsoft YaHei', 11),
                      selectcolor='white', activebackground='white').pack(anchor=tk.W)

        self.save_os_var = tk.BooleanVar(value=self.sm.get('result_settings.save_os_results', True))
        r3 = tk.Frame(result_frame, bg='white', padx=10, pady=5, highlightbackground='black', highlightthickness=2)
        r3.pack(fill=tk.X, pady=3)
        tk.Checkbutton(r3, text=self.sm.get_text('chk_os'), variable=self.save_os_var,
                      bg='white', fg=COLORS['text_primary'], font=('Microsoft YaHei', 11),
                      selectcolor='white', activebackground='white').pack(anchor=tk.W)

        # 底部按钮 - 固定在主窗口底部，不在滚动区域内
        btn_frame = tk.Frame(self, bg=COLORS['bg_primary'], padx=10, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Button(btn_frame, text=self.sm.get_text('menu_exit'), bg=COLORS['text_secondary'],
                 fg=COLORS['text_light'], font=('Microsoft YaHei', 11), relief='flat',
                 cursor='hand2', width=10, command=self.destroy).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text=self.sm.get_text('btn_reset'), bg=COLORS['accent_warning'],
                 fg=COLORS['text_light'], font=('Microsoft YaHei', 11), relief='flat',
                 cursor='hand2', width=10, command=self._reset_defaults).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text=self.sm.get_text('btn_save_settings'), bg=COLORS['accent_success'],
                 fg=COLORS['text_light'], font=('Microsoft YaHei', 11), relief='flat',
                 cursor='hand2', width=10, command=self._save_settings).pack(side=tk.RIGHT, padx=5)


    def _browse_python(self, var):
        """浏览选择Python可执行文件"""
        filename = filedialog.askopenfilename(
            title=self.sm.get_text('label_python27'),
            filetypes=[("Python Executable", "python.exe"), ("All Files", "*.*")]
        )
        if filename:
            var.set(filename)

    def _verify_python(self, path, version):
        """验证Python环境"""
        if not path or not os.path.exists(path):
            messagebox.showerror(
                self.sm.get_text('status_error'),
                self.sm.get_text('msg_invalid_python')
            )
            return

        def notify(kind, title, body):
            def _show():
                dialog = getattr(messagebox, kind)
                dialog(title, body, parent=self)
            self.after(0, _show)

        def verify():
            try:
                result = subprocess.run(
                    [path, "-c", "import sys; print(sys.version)"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    notify(
                        'showinfo',
                        self.sm.get_text('msg_verify_ok'),
                        "Python {}:\n{}".format(version, result.stdout.strip())
                    )
                else:
                    notify(
                        'showerror',
                        self.sm.get_text('msg_verify_fail'),
                        result.stderr
                    )
            except Exception as e:
                notify(
                    'showerror',
                    self.sm.get_text('msg_verify_fail'),
                    str(e)
                )

        threading.Thread(target=verify).start()

    def _load_settings(self):
        """加载所有设置到UI"""
        self._load_scale_settings()

    def _load_scale_settings(self):
        """加载当前规模的设置"""
        scale = self.edit_scale_var.get()
        config = self.sm.get_scale_config(scale)

        for key, var in self.scale_param_vars.items():
            if key in config:
                var.set(config[key])

    def _reset_current_scale(self):
        """重置当前规模为默认值"""
        scale = self.edit_scale_var.get()
        defaults = DEFAULT_CONFIG['data_scale_custom'].get(scale, {})
        for key, var in self.scale_param_vars.items():
            if key in defaults:
                var.set(defaults[key])

    def _save_settings(self):
        """保存所有设置"""
        # Basic settings
        self.sm.set('language', self.lang_var.get())
        self.sm.set('python_paths.python27', self.py27_var.get())
        self.sm.set('python_paths.python3', self.py3_var.get())
        self.sm.set('test_settings.runs', self.runs_var.get())
        self.sm.set('test_settings.warmup', self.warmup_var.get())
        self.sm.set('test_settings.enable_multiprocess', self.mp_var.get())
        self.sm.set('test_settings.mp_workers', self.workers_var.get())
        self.sm.set('test_settings.enable_opensource', self.os_var.get())

        # Scale settings
        scale = self.edit_scale_var.get()
        for key, var in self.scale_param_vars.items():
            self.sm.set_scale_config(scale, key, var.get())

        # Result settings
        self.sm.set('result_settings.save_py2_results', self.save_py2_var.get())
        self.sm.set('result_settings.save_py3_results', self.save_py3_var.get())
        self.sm.set('result_settings.save_os_results', self.save_os_var.get())
        self.sm.set('result_settings.use_timestamp_folder', self.timestamp_var.get())
        self.sm.set('result_settings.retention_days', self.retention_var.get())

        # UI settings
        self.sm.set('ui_settings.remember_last_settings', self.remember_var.get())
        self.sm.set('ui_settings.font_scale', self.font_scale_var.get())

        if self.sm.save_config():
            messagebox.showinfo(
                self.sm.get_text('msg_config_saved'),
                self.sm.get_text('msg_config_saved')
            )
            self.parent._on_settings_changed()
            # Notify to restart for font scale to take effect
            if self.font_scale_var.get() != self.parent.font_scale:
                messagebox.showinfo(
                    "Restart Required",
                    "Font scale changes will take effect after restart."
                )
        else:
            messagebox.showerror(
                self.sm.get_text('status_error'),
                "Failed to save configuration"
            )

    def _reset_defaults(self):
        """重置所有设置为默认值"""
        if messagebox.askyesno(
            self.sm.get_text('btn_reset'),
            "Reset all settings to default values?"
        ):
            self.sm.reset_to_defaults()
            self._load_settings()
            messagebox.showinfo(
                self.sm.get_text('msg_config_saved'),
                self.sm.get_text('msg_config_loaded')
            )


class ModernBenchmarkGUI(object):
    """现代化主GUI类"""

    def __init__(self, root):
        self.root = root
        self.sm = SettingsManager()
        self.font_scale = self.sm.get('ui_settings.font_scale', 1.0)

        # 自动检测Python路径（如果未设置）
        if not self.sm.get('python_paths.python27') or not self.sm.get('python_paths.python3'):
            detected = self.sm.auto_detect_python_paths()
            if detected['python27'] or detected['python3']:
                self.sm.save_config()

        # 状态变量
        self.is_running = False
        self.should_stop = False
        self.current_process = None
        self.start_time = None
        self.completed_tests = 0
        self.total_tests = 0
        self.test_queue = []
        self.current_output_dir = ''
        self.os_available = False
        self.os_missing_modules = []
        self.os_status_reason = ''
        self.os_installing = False

        self._setup_window()
        self._create_styles()
        self._create_ui()
        self._update_language()
        self._refresh_opensource_support()

    def _setup_window(self):
        """设置窗口"""
        self.root.title(self.sm.get_text('app_title'))
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        self.root.configure(bg=COLORS['bg_primary'])

        # 设置DPI感知
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

        # 设置图标
        icon_path = os.path.join(SCRIPT_DIR, 'resources', 'icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_styles(self):
        """创建ttk样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        base_size = int(12 * self.font_scale)

        # 自定义样式
        self.style.configure('Modern.TFrame', background=COLORS['bg_primary'])
        self.style.configure('Card.TFrame', background=COLORS['bg_secondary'])

        self.style.configure('Modern.TLabel',
                           background=COLORS['bg_primary'],
                           foreground=COLORS['text_primary'],
                           font=('Microsoft YaHei', base_size))

        self.style.configure('Title.TLabel',
                           background=COLORS['bg_header'],
                           foreground=COLORS['text_light'],
                           font=('Microsoft YaHei', int(24 * self.font_scale), 'bold'))

        self.style.configure('CardTitle.TLabel',
                           background=COLORS['bg_secondary'],
                           foreground=COLORS['accent_primary'],
                           font=('Microsoft YaHei', int(14 * self.font_scale), 'bold'))

        # 进度条样式
        self.style.configure('Modern.Horizontal.TProgressbar',
                           background=COLORS['accent_primary'],
                           troughcolor=COLORS['border'],
                           borderwidth=0,
                           thickness=int(20 * self.font_scale))

    def _font(self, size, bold=False, color=None):
        """获取字体配置"""
        scaled_size = int(size * self.font_scale)
        weight = 'bold' if bold else 'normal'
        return ('Microsoft YaHei', scaled_size, weight)

    def _create_scrollable_sidebar(self, parent):
        """创建可滚动的左侧栏容器。"""
        sidebar = tk.Frame(parent, bg=COLORS['bg_primary'])
        sidebar.pack(side='left', fill='y', padx=(0, 15))
        sidebar_width = max(int(500 * self.font_scale), 420)
        sidebar.config(width=sidebar_width)
        sidebar.pack_propagate(False)

        canvas = tk.Canvas(sidebar, bg=COLORS['bg_primary'], highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(sidebar, orient='vertical', command=canvas.yview)
        content = tk.Frame(canvas, bg=COLORS['bg_primary'])

        window_id = canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        def _update_scrollregion(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            _sync_scrollbar()

        def _update_content_width(event):
            canvas.itemconfig(window_id, width=event.width)
            _sync_scrollbar()

        def _sync_scrollbar():
            canvas.update_idletasks()
            needs_scroll = content.winfo_reqheight() > canvas.winfo_height()
            is_mapped = scrollbar.winfo_ismapped()
            if needs_scroll and not is_mapped:
                scrollbar.pack(side='right', fill='y')
            elif not needs_scroll and is_mapped:
                scrollbar.pack_forget()

        content.bind('<Configure>', _update_scrollregion)
        canvas.bind('<Configure>', _update_content_width)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.sidebar_canvas = canvas
        self.sidebar_content = content
        self.sidebar_scrollbar = scrollbar
        self.root.after(0, _sync_scrollbar)
        return content

    def _create_big_checkbox(self, parent, text, variable):
        """创建大号复选框，使用浅色背景让勾选更明显"""
        frame = tk.Frame(parent, bg='white')
        frame.pack(anchor='w', fill='x')

        # 使用更大的指示器大小和浅色选中背景
        cb = tk.Checkbutton(frame, text=text, variable=variable,
                           bg='white', fg=COLORS['text_primary'],
                           font=self._font(11), selectcolor='#e3f2fd',  # 浅蓝色背景
                           activebackground='white', cursor='hand2',
                           height=0, anchor='w', padx=4, pady=1)
        cb.pack(anchor='w', fill='x')
        return cb

    def _browse_python_path(self, variable, title=None):
        """选择 Python 可执行文件路径。"""
        filename = filedialog.askopenfilename(
            title=title or self.sm.get_text('label_python27'),
            filetypes=[("Python Executable", "python.exe"), ("All Files", "*.*")]
        )
        if filename:
            variable.set(filename)
            if hasattr(self, 'py3_var') and variable is self.py3_var:
                self._refresh_opensource_support()

    def _browse_directory(self, variable):
        """选择目录。"""
        dirname = filedialog.askdirectory(title=self.sm.get_text('label_data_dir'))
        if dirname:
            variable.set(dirname)

    def _verify_python_path(self, path, version):
        """验证 Python 环境。"""
        if not path or not os.path.exists(path):
            messagebox.showerror(
                self.sm.get_text('status_error'),
                self.sm.get_text('msg_invalid_python')
            )
            return

        def notify(kind, title, body):
            def _show():
                dialog = getattr(messagebox, kind)
                dialog(title, body, parent=self.root)
            self.root.after(0, _show)

        def verify():
            try:
                result = subprocess.run(
                    [path, "-c", "import sys; print(sys.version)"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    notify(
                        'showinfo',
                        self.sm.get_text('msg_verify_ok'),
                        "Python {}:\n{}".format(version, result.stdout.strip())
                    )
                    if version == '3.x':
                        self.root.after(0, self._refresh_opensource_support)
                else:
                    notify(
                        'showerror',
                        self.sm.get_text('msg_verify_fail'),
                        result.stderr
                    )
            except Exception as e:
                notify(
                    'showerror',
                    self.sm.get_text('msg_verify_fail'),
                    str(e)
                )

        threading.Thread(target=verify).start()

    def _probe_opensource_support(self, python3_path=None):
        """检查开源库测试环境是否可用。"""
        if python3_path is None:
            python3_path = self.py3_var.get() if hasattr(self, 'py3_var') else self.sm.get('python_paths.python3', '')

        if not python3_path:
            return False, ['python3'], 'Python 3.x path not configured'
        if not os.path.exists(python3_path):
            return False, ['python3'], 'Python 3.x path does not exist'

        probe_code = (
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "missing = []\n"
            "for module_name in %r:\n"
            "    try:\n"
            "        __import__(module_name)\n"
            "    except Exception:\n"
            "        missing.append(module_name)\n"
            "print('OK' if not missing else 'MISSING:' + ','.join(missing))\n"
        ) % (SCRIPT_DIR, OPEN_SOURCE_PACKAGES)

        try:
            result = subprocess.run(
                [python3_path, '-u', '-c', probe_code],
                capture_output=True,
                text=True,
                timeout=20
            )
            stdout = (result.stdout or '').strip()
            stderr = (result.stderr or '').strip()
            if result.returncode == 0 and stdout == 'OK':
                return True, [], ''

            missing = []
            if stdout.startswith('MISSING:'):
                missing = [item.strip() for item in stdout.split(':', 1)[1].split(',') if item.strip()]
            if not missing:
                missing = list(OPEN_SOURCE_PACKAGES)
            return False, missing, stderr or stdout or 'Open-source benchmarks are unavailable'
        except Exception as e:
            return False, list(OPEN_SOURCE_PACKAGES), str(e)

    def _format_opensource_status(self):
        """生成开源库状态说明文本。"""
        lang = self.sm.get('language', 'zh')
        if self.os_available:
            return '已安装，可启用' if lang == 'zh' else 'Installed and available'

        if self.os_status_reason:
            return '不可用：{}'.format(self.os_status_reason) if lang == 'zh' else 'Unavailable: {}'.format(self.os_status_reason)

        missing = self.os_missing_modules or list(OPEN_SOURCE_PACKAGES)
        return '未安装：{}'.format(', '.join(missing)) if lang == 'zh' else 'Missing: {}'.format(', '.join(missing))

    def _refresh_opensource_support(self):
        """刷新开源库可用性。"""
        available, missing, reason = self._probe_opensource_support()
        self.os_available = available
        self.os_missing_modules = missing
        self.os_status_reason = reason
        if not available and hasattr(self, 'os_var'):
            self.os_var.set(False)
        self._apply_opensource_state()

    def _apply_opensource_state(self):
        """把开源库可用性同步到界面。"""
        lang = self.sm.get('language', 'zh')
        py3_path = self.py3_var.get() if hasattr(self, 'py3_var') else self.sm.get('python_paths.python3', '')
        py3_ready = bool(py3_path and os.path.exists(py3_path))
        checkbox_text = self.sm.get_text('chk_opensource')
        if not self.os_available:
            checkbox_text = checkbox_text + ('（未安装）' if lang == 'zh' else ' (Not installed)')
        if hasattr(self, 'os_checkbox'):
            self.os_checkbox.config(text=checkbox_text)
            self.os_checkbox.config(state='normal' if self.os_available and not self.os_installing else 'disabled')
        if hasattr(self, 'os_status_prefix_label'):
            self.os_status_prefix_label.config(text=self.sm.get_text('label_os_status'))
        if hasattr(self, 'os_status_label'):
            self.os_status_label.config(text=self._format_opensource_status())
        if hasattr(self, 'recheck_os_btn'):
            self.recheck_os_btn.config(text=self.sm.get_text('btn_recheck'))
            self.recheck_os_btn.config(state='normal' if py3_ready and not self.os_installing else 'disabled')
        if hasattr(self, 'install_os_btn'):
            self.install_os_btn.config(text=self.sm.get_text('btn_install_os'))
            self.install_os_btn.config(state='normal' if py3_ready and not self.os_installing else 'disabled')
        if hasattr(self, 'settings_btn'):
            self.settings_btn.config(text=self.sm.get_text('btn_advanced_settings'))

    def _install_opensource_packages(self):
        """安装或修复开源库依赖。"""
        if self.os_installing:
            return

        py3_path = self.py3_var.get() if hasattr(self, 'py3_var') else self.sm.get('python_paths.python3', '')
        if not py3_path or not os.path.exists(py3_path):
            self._log("Python 3.x 路径无效，无法安装开源包", "ERROR")
            return

        self.os_installing = True
        self._apply_opensource_state()
        self._log("开始安装/修复开源包: {}".format(', '.join(OPEN_SOURCE_PACKAGES)), "INFO")
        worker = threading.Thread(
            target=self._install_opensource_packages_worker,
            args=(py3_path,),
        )
        worker.daemon = True
        worker.start()

    def _install_opensource_packages_worker(self, python3_path):
        """后台安装开源库依赖。"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = [
            python3_path,
            '-m', 'pip', 'install',
            '--disable-pip-version-check',
        ] + list(OPEN_SOURCE_PACKAGES)

        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['PYTHONIOENCODING'] = 'utf-8'

        process = None
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                cwd=script_dir
            )

            for line in process.stdout:
                text = line.strip()
                if text:
                    self.root.after(0, lambda m=text: self._log(m, "CMD"))

            process.wait()

            if process.returncode == 0:
                self.root.after(0, lambda: self._log("开源包安装完成，正在重新检测环境...", "SUCCESS"))
            else:
                self.root.after(
                    0,
                    lambda rc=process.returncode: self._log("开源包安装失败，退出码: {}".format(rc), "ERROR")
                )
        except Exception as e:
            self.root.after(0, lambda: self._log("安装开源包时出错: {}".format(str(e)), "ERROR"))
        finally:
            def _finish():
                self.os_installing = False
                self._refresh_opensource_support()

            self.root.after(0, _finish)

    def _create_ui(self):
        """创建主UI"""
        # 顶部标题栏
        self._create_header()

        # 主内容区
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill='both', expand=True, padx=20, pady=15)

        # 左侧控制面板（可滚动）
        left_panel = self._create_scrollable_sidebar(main_container)

        # 右侧内容区
        right_panel = tk.Frame(main_container, bg=COLORS['bg_primary'])
        right_panel.pack(side='left', fill='both', expand=True)

        # 左侧卡片
        self._create_quick_settings_card(left_panel)
        self._create_settings_card(left_panel)
        self._create_test_options_card(left_panel)

        # 右侧卡片
        self._create_progress_card(right_panel)
        self._create_log_card(right_panel)

        # 底部状态栏
        self._create_status_bar()

    def _create_header(self):
        """创建现代化头部"""
        header = tk.Frame(self.root, bg=COLORS['bg_header'], height=int(80 * self.font_scale))
        header.pack(fill='x')
        header.pack_propagate(False)

        # Logo区域
        logo_frame = tk.Frame(header, bg=COLORS['bg_header'])
        logo_frame.pack(side='left', padx=20, pady=10)

        # 图标（使用emoji或文字）
        icon_label = tk.Label(logo_frame, text='', bg=COLORS['bg_header'],
                             fg=COLORS['text_light'], font=('Segoe UI Emoji', int(32 * self.font_scale)))
        icon_label.pack(side='left', padx=(0, 10))

        # 标题
        title_frame = tk.Frame(logo_frame, bg=COLORS['bg_header'])
        title_frame.pack(side='left')

        self.title_label = tk.Label(title_frame, text='', bg=COLORS['bg_header'],
                                   fg=COLORS['text_light'], font=self._font(20, bold=True))
        self.title_label.pack(anchor='w')

        self.subtitle_label = tk.Label(title_frame, text='Performance Benchmark Tool',
                           bg=COLORS['bg_header'], fg='#9fa8da', font=self._font(11))
        self.subtitle_label.pack(anchor='w')

        # 右侧工具按钮
        tools_frame = tk.Frame(header, bg=COLORS['bg_header'])
        tools_frame.pack(side='right', padx=20)

        # 语言切换按钮
        self.lang_btn = tk.Button(tools_frame, text='English', bg=COLORS['accent_secondary'],
                                 fg=COLORS['text_light'], relief='flat', cursor='hand2',
                                 font=self._font(11), padx=15, pady=5,
                                 command=self._toggle_language)
        self.lang_btn.pack(side='right', padx=5)

    def _create_quick_settings_card(self, parent):
        """快速设置卡片"""
        card = CardFrame(parent, title=' Quick Settings')
        card.pack(fill='x', pady=(0, 15), ipadx=10, ipady=10)

        # 数据规模
        scale_frame = tk.Frame(card, bg=COLORS['bg_secondary'])
        scale_frame.pack(fill='x', padx=15, pady=10)

        tk.Label(scale_frame, text=self.sm.get_text('label_scale_select'),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                font=self._font(11)).pack(anchor='w')

        # Store scale names mapping for both directions
        self.scale_names = {
            'tiny': self.sm.get_text('scale_tiny'),
            'small': self.sm.get_text('scale_small'),
            'standard': self.sm.get_text('scale_standard'),
            'medium': self.sm.get_text('scale_medium'),
            'large': self.sm.get_text('scale_large')
        }
        # Reverse mapping: display name -> key
        self.scale_name_to_key = {v: k for k, v in self.scale_names.items()}

        # Default value is the display name
        default_key = self.sm.get('test_settings.data_scale', 'tiny')
        self.scale_var = tk.StringVar(value=self.scale_names.get(default_key, default_key))

        self.scale_menu = tk.OptionMenu(scale_frame, self.scale_var,
                                       *[self.scale_names[k] for k in ['tiny', 'small', 'standard', 'medium', 'large']])
        self.scale_menu.config(font=self._font(12), bg=COLORS['bg_secondary'],
                              fg=COLORS['text_primary'], relief='flat',
                              highlightbackground=COLORS['border'], highlightthickness=1)
        self.scale_menu.pack(fill='x', pady=(5, 0))

    def _create_settings_card(self, parent):
        """常用运行设置卡片。"""
        card = CardFrame(parent, title=' ' + self.sm.get_text('settings_title'))
        card.pack(fill='x', pady=(0, 15), ipadx=10, ipady=10)
        self.settings_card = card

        content = tk.Frame(card, bg=COLORS['bg_secondary'])
        content.pack(fill='x', padx=15, pady=8)

        self.py27_var = tk.StringVar(value=self.sm.get('python_paths.python27', ''))
        py27_row = tk.Frame(content, bg=COLORS['bg_secondary'])
        py27_row.pack(fill='x', pady=2)
        tk.Label(py27_row, text=self.sm.get_text('label_python27'),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                font=self._font(9)).pack(side='left')
        tk.Entry(py27_row, textvariable=self.py27_var, font=self._font(9)).pack(side='left', padx=4, fill='x', expand=True)
        tk.Button(py27_row, text=self.sm.get_text('btn_browse'),
                 command=lambda: self._browse_python_path(self.py27_var),
                 bg=COLORS['accent_secondary'], fg='white', font=self._font(8)).pack(side='left', padx=2)
        tk.Button(py27_row, text=self.sm.get_text('btn_verify'),
                 command=lambda: self._verify_python_path(self.py27_var.get(), '2.7'),
                 bg=COLORS['accent_primary'], fg='white', font=self._font(8)).pack(side='left', padx=2)

        self.py3_var = tk.StringVar(value=self.sm.get('python_paths.python3', ''))
        py3_row = tk.Frame(content, bg=COLORS['bg_secondary'])
        py3_row.pack(fill='x', pady=2)
        tk.Label(py3_row, text=self.sm.get_text('label_python3'),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                font=self._font(9)).pack(side='left')
        tk.Entry(py3_row, textvariable=self.py3_var, font=self._font(9)).pack(side='left', padx=4, fill='x', expand=True)
        tk.Button(py3_row, text=self.sm.get_text('btn_browse'),
                 command=lambda: self._browse_python_path(self.py3_var, self.sm.get_text('label_python3')),
                 bg=COLORS['accent_secondary'], fg='white', font=self._font(8)).pack(side='left', padx=2)
        tk.Button(py3_row, text=self.sm.get_text('btn_verify'),
                 command=lambda: self._verify_python_path(self.py3_var.get(), '3.x'),
                 bg=COLORS['accent_primary'], fg='white', font=self._font(8)).pack(side='left', padx=2)

        self.runs_var = tk.IntVar(value=self.sm.get('test_settings.runs', 3))
        self.warmup_var = tk.IntVar(value=self.sm.get('test_settings.warmup', 1))
        self.workers_var = tk.IntVar(value=self.sm.get('test_settings.mp_workers', 4))
        params_row = tk.Frame(content, bg=COLORS['bg_secondary'])
        params_row.pack(fill='x', pady=(4, 2))

        param_specs = [
            (self.sm.get_text('label_runs'), self.runs_var, 1, 20),
            (self.sm.get_text('label_warmup'), self.warmup_var, 0, 10),
            (self.sm.get_text('label_workers'), self.workers_var, 1, 16),
        ]
        for index, (label_text, var, min_value, max_value) in enumerate(param_specs):
            field = tk.Frame(params_row, bg=COLORS['bg_secondary'])
            field.pack(side='left', fill='x', expand=True, padx=(0 if index == 0 else 6, 0))
            tk.Label(field, text=label_text,
                    bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                    font=self._font(9)).pack(anchor='w')
            tk.Spinbox(field, from_=min_value, to=max_value, textvariable=var, width=6,
                      font=self._font(9)).pack(fill='x', pady=(2, 0))

        self.data_dir_var = tk.StringVar(value=self.sm.get('paths.data_dir', r'C:\temp\arcgis_benchmark_data'))
        data_row = tk.Frame(content, bg=COLORS['bg_secondary'])
        data_row.pack(fill='x', pady=(4, 2))
        tk.Label(data_row, text=self.sm.get_text('label_data_dir'),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                font=self._font(9)).pack(side='left')
        tk.Entry(data_row, textvariable=self.data_dir_var, font=self._font(9)).pack(side='left', padx=4, fill='x', expand=True)
        tk.Button(data_row, text=self.sm.get_text('btn_browse'),
                 command=lambda: self._browse_directory(self.data_dir_var),
                 bg=COLORS['accent_secondary'], fg='white', font=self._font(8)).pack(side='left', padx=2)

        footer_row = tk.Frame(content, bg=COLORS['bg_secondary'])
        footer_row.pack(fill='x', pady=(6, 0))

        self.timestamp_var = tk.BooleanVar(value=self.sm.get('result_settings.use_timestamp_folder', True))
        tk.Checkbutton(footer_row, text=self.sm.get_text('chk_timestamp_folder'),
                      variable=self.timestamp_var, bg=COLORS['bg_secondary'],
                      fg=COLORS['text_primary'], font=self._font(9),
                      selectcolor=COLORS['bg_secondary'], activebackground=COLORS['bg_secondary']).pack(side='left')

        self.settings_btn = tk.Button(
            footer_row,
            text=self.sm.get_text('btn_advanced_settings'),
            bg=COLORS['accent_secondary'], fg=COLORS['text_light'],
            relief='flat', cursor='hand2', font=self._font(9), padx=10, pady=3,
            command=self._open_settings
        )
        self.settings_btn.pack(side='right')

    def _create_test_options_card(self, parent):
        """测试选项卡片"""
        card = CardFrame(parent, title=' Test Options')
        card.pack(fill='x', pady=(0, 15), ipadx=10, ipady=10)

        content = tk.Frame(card, bg=COLORS['bg_secondary'])
        content.pack(fill='x', padx=15, pady=10)

        # 多进程选项 - 使用大号自定义复选框
        self.mp_var = tk.BooleanVar(value=self.sm.get('test_settings.enable_multiprocess', False))
        mp_frame = tk.Frame(content, bg='white', padx=10, pady=8,
                           highlightbackground='black', highlightthickness=1)
        mp_frame.pack(fill='x', pady=(4, 6))
        self._create_big_checkbox(mp_frame, self.sm.get_text('chk_multiprocess'), self.mp_var)

        # 开源库选项 - 使用大号自定义复选框
        self.os_var = tk.BooleanVar(value=self.sm.get('test_settings.enable_opensource', False))
        os_frame = tk.Frame(content, bg='white', padx=10, pady=8,
                           highlightbackground='black', highlightthickness=1)
        os_frame.pack(fill='x', pady=(0, 6))
        self.os_checkbox = self._create_big_checkbox(os_frame, self.sm.get_text('chk_opensource'), self.os_var)
        status_row = tk.Frame(os_frame, bg='white')
        status_row.pack(fill='x', pady=(4, 0))
        self.os_status_prefix_label = tk.Label(status_row, text=self.sm.get_text('label_os_status'),
                                              bg='white', fg=COLORS['text_secondary'], font=self._font(8))
        self.os_status_prefix_label.pack(side='left')
        self.os_status_label = tk.Label(status_row, text='',
                                       bg='white', fg=COLORS['text_primary'],
                                       font=self._font(8))
        self.os_status_label.pack(side='left', padx=(5, 0), fill='x', expand=True)
        self.recheck_os_btn = tk.Button(
            status_row,
            text=self.sm.get_text('btn_recheck'),
            bg=COLORS['accent_secondary'], fg='white', relief='flat',
            cursor='hand2', font=self._font(8), command=self._refresh_opensource_support
        )
        self.recheck_os_btn.pack(side='right', padx=(5, 0))

        self.install_os_btn = tk.Button(
            os_frame,
            text=self.sm.get_text('btn_install_os'),
            bg=COLORS['accent_success'], fg='white', relief='flat',
            cursor='hand2', font=self._font(8), command=self._install_opensource_packages
        )
        self.install_os_btn.pack(fill='x', pady=(6, 0))

        # 打开文件夹按钮
        self.open_temp_btn = tk.Button(
            content,
            text=self.sm.get_text('btn_open_temp'),
            bg=COLORS['bg_primary'], fg=COLORS['accent_primary'],
            relief='flat', font=self._font(10), cursor='hand2',
            command=self._open_temp_folder
        )
        self.open_temp_btn.pack(fill='x', pady=(10, 0), ipady=6)

    def _create_progress_card(self, parent):
        """进度卡片"""
        card = CardFrame(parent, title=' Progress')
        card.pack(fill='x', pady=(0, 15), ipadx=10, ipady=10)

        content = tk.Frame(card, bg=COLORS['bg_secondary'])
        content.pack(fill='x', padx=15, pady=10)

        # 总进度
        tk.Label(content, text=self.sm.get_text('progress_total'),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                font=self._font(11)).pack(anchor='w')

        progress_wrap = tk.Frame(content, bg=COLORS['bg_secondary'])
        progress_wrap.pack(fill='x', pady=(5, 15))

        self.total_progress = tk.Canvas(
            progress_wrap,
            height=int(22 * self.font_scale),
            bg=COLORS['border'],
            highlightthickness=0,
            bd=0
        )
        self.total_progress.pack(fill='x')
        self.total_progress.bind('<Configure>', self._on_total_progress_resize)

        # 当前测试
        tk.Label(content, text=self.sm.get_text('progress_current'),
                bg=COLORS['bg_secondary'], fg=COLORS['text_secondary'],
                font=self._font(11)).pack(anchor='w')

        self.current_test_label = tk.Label(content, text=self.sm.get_text('status_ready'),
                                          bg=COLORS['bg_secondary'],
                                          fg=COLORS['text_primary'],
                                          font=self._font(14, bold=True))
        self.current_test_label.pack(anchor='w', pady=(5, 0))

        self.eta_label = tk.Label(content, text='',
                                 bg=COLORS['bg_secondary'],
                                 fg=COLORS['text_secondary'], font=self._font(11))
        self.eta_label.pack(anchor='w')

        # 控制按钮区
        btn_frame = tk.Frame(content, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill='x', pady=(20, 0))

        # 使用标准按钮避免渲染问题
        self.run_btn = tk.Button(btn_frame, text=' Start Test',
                                bg=COLORS['accent_success'], fg=COLORS['text_light'],
                                relief='flat', cursor='hand2', font=self._font(14, bold=True),
                                padx=30, pady=12, command=self._start_test)
        self.run_btn.pack(side='left', padx=(0, 10))

        self.stop_btn = tk.Button(btn_frame, text=' Stop',
                                 bg=COLORS['accent_danger'], fg=COLORS['text_light'],
                                 relief='flat', cursor='hand2', font=self._font(14, bold=True),
                                 padx=30, pady=12, command=self._stop_test)
        self.stop_btn.pack(side='left')

    def _create_log_card(self, parent):
        """日志卡片"""
        card = CardFrame(parent, title=' Log')
        card.pack(fill='both', expand=True, ipadx=10, ipady=10)

        # 工具栏
        toolbar = tk.Frame(card, bg=COLORS['bg_secondary'])
        toolbar.pack(fill='x', padx=15, pady=(10, 5))

        for text, cmd in [(' Clear', self._clear_log),
                          (' Save', self._save_log),
                          (' Copy', self._copy_log)]:
            btn = tk.Button(toolbar, text=text, bg=COLORS['bg_primary'],
                           fg=COLORS['text_primary'], relief='flat',
                           font=self._font(10), cursor='hand2', command=cmd)
            btn.pack(side='left', padx=(0, 5))

        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            card, wrap='word', font=self._font(11),
            bg='#263238', fg='#aed581',  # 深色背景，绿色文字
            insertbackground='white',
            relief='flat', padx=10, pady=10,
            state='disabled'
        )
        self.log_text.pack(fill='both', expand=True, padx=15, pady=(0, 15))

        # 标签颜色
        self.log_text.tag_configure('INFO', foreground='#aed581')
        self.log_text.tag_configure('SUCCESS', foreground='#69f0ae')
        self.log_text.tag_configure('WARNING', foreground='#ffd54f')
        self.log_text.tag_configure('ERROR', foreground='#ff8a80')
        self.log_text.tag_configure('CMD', foreground='#82b1ff')

    def _create_status_bar(self):
        """状态栏"""
        self.status_bar = tk.Frame(self.root, bg=COLORS['bg_header'], height=30)
        self.status_bar.pack(side='bottom', fill='x')
        self.status_bar.pack_propagate(False)

        self.status_label = tk.Label(self.status_bar, text=self.sm.get_text('status_ready'),
                                    bg=COLORS['bg_header'], fg=COLORS['text_light'],
                                    font=self._font(10))
        self.status_label.pack(side='left', padx=15)

    def _log(self, message, level='INFO'):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_message = '[{}] {}\n'.format(timestamp, message)

        self.log_text.config(state='normal')
        self.log_text.insert('end', full_message, level)
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.config(state='disabled')

    def _save_log(self):
        filename = filedialog.asksaveasfilename(defaultextension='.log')
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, 'end'))

    def _copy_log(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get(1.0, 'end'))

    def _open_temp_folder(self):
        """Open the temp folder currently being used by the running or last test"""
        temp_dir = getattr(self, 'current_output_dir', '') or self.data_dir_var.get().strip() or r'C:\temp\arcgis_benchmark_data'

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        try:
            os.startfile(temp_dir)
        except:
            pass

    def _find_result_files(self, root_dir, keyword):
        """Recursively find benchmark result JSON files under a root folder."""
        matches = []
        if not root_dir or not os.path.isdir(root_dir):
            return matches

        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                lowered = filename.lower()
                if lowered.endswith('.json') and keyword in lowered:
                    matches.append(os.path.join(dirpath, filename))
        return sorted(matches)

    def _open_settings(self):
        """打开设置对话框"""
        SettingsDialog(self.root, self.sm)

    def _on_total_progress_resize(self, event=None):
        """Canvas 尺寸变化时重绘总进度条"""
        self._render_total_progress()

    def _estimate_total_progress_units(self):
        """估算当前测试流程的总进度单位数"""
        py27_path = self.py27_var.get() if hasattr(self, 'py27_var') else self.sm.get('python_paths.python27', '')
        py3_path = self.py3_var.get() if hasattr(self, 'py3_var') else self.sm.get('python_paths.python3', '')
        has_py27 = bool(py27_path and os.path.exists(py27_path))
        has_py3 = bool(py3_path and os.path.exists(py3_path))
        include_mp = bool(self.mp_var.get())
        include_os = bool(self.os_var.get() and self.os_available)

        total = 0

        if has_py27:
            total += 1 + DEFAULT_ARCPY_REGULAR_BENCHMARKS
            if include_mp:
                total += DEFAULT_ARCPY_MULTIPROCESS_BENCHMARKS

        if has_py3:
            total += 1 + DEFAULT_ARCPY_REGULAR_BENCHMARKS
            if include_mp:
                total += DEFAULT_ARCPY_MULTIPROCESS_BENCHMARKS

            if include_os:
                total += 1 + DEFAULT_ARCPY_REGULAR_BENCHMARKS + DEFAULT_OS_REGULAR_BENCHMARKS
                if include_mp:
                    total += DEFAULT_ARCPY_MULTIPROCESS_BENCHMARKS + DEFAULT_OS_MULTIPROCESS_BENCHMARKS

        return total * max(1, len(self.test_queue))

    def _progress_text(self, current, total):
        """格式化进度条内部显示文本"""
        label = self.sm.get_text('progress_total')
        if total <= 0:
            return "{} 0/0 (0%)".format(label)

        width = max(len(str(total)), 2)
        current_str = ("{:0" + str(width) + "d}").format(max(0, current))
        total_str = ("{:0" + str(width) + "d}").format(total)
        percentage = int(round(float(current) / float(total) * 100)) if total > 0 else 0
        return "{} {}/{} ({}%)".format(label, current_str, total_str, percentage)

    def _render_total_progress(self):
        """重绘总进度条"""
        if not hasattr(self, 'total_progress'):
            return

        canvas = self.total_progress
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), int(22 * self.font_scale))
        current = max(0, min(self.completed_tests, self.total_tests))
        total = max(0, self.total_tests)

        canvas.delete('all')
        canvas.create_rectangle(0, 0, width, height, fill=COLORS['border'], outline=COLORS['border'])

        if total > 0:
            fill_width = int(float(current) / float(total) * width)
            if fill_width > 0:
                canvas.create_rectangle(
                    0, 0, fill_width, height,
                    fill=COLORS['accent_primary'],
                    outline=COLORS['accent_primary']
                )

        percentage = float(current) / float(total) if total > 0 else 0
        text_color = COLORS['text_primary'] if percentage < 0.5 else COLORS['text_light']
        canvas.create_text(
            width // 2,
            height // 2,
            text=self._progress_text(current, total),
            fill=text_color,
            font=self._font(10, bold=True)
        )

    def _advance_progress(self, increment=1, test_name=''):
        """推进总进度"""
        self._update_progress(self.completed_tests + increment, self.total_tests, test_name)

    def _update_progress(self, current, total, test_name=''):
        """更新进度显示"""
        total = max(0, int(total))
        current = max(0, int(current))
        if total > 0 and current > total:
            current = total

        self.completed_tests = current
        self.total_tests = total
        self._render_total_progress()

        # Update ETA
        if total > 0 and self.start_time and current > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            avg_time = elapsed / current
            remaining = avg_time * (total - current)
            eta_str = str(timedelta(seconds=int(remaining)))
            self.eta_label.config(text="{}: {}".format(self.sm.get_text('eta'), eta_str))
        elif total <= 0:
            self.eta_label.config(text="")

        if test_name:
            self.current_test_label.config(text=test_name)

    def _start_test(self):
        """开始单个测试"""
        if self.is_running:
            return

        # Get selected scale - map display name back to key
        scale_display = self.scale_var.get()
        scale = self.scale_name_to_key.get(scale_display, 'tiny')

        # Log the test parameters
        self._log("=" * 60)
        self._log("Test Configuration:")
        self._log("  Scale: {} ({})".format(scale, scale_display))
        self._log("  Data Scale Config: {}".format(self.sm.get_scale_config(scale)))
        self._log("  Multiprocess: {}".format(self.mp_var.get()))
        self._log("  Open Source: {}".format(self.os_var.get() and self.os_available))
        self._log("  Python 2.7: {}".format(self.py27_var.get() if hasattr(self, 'py27_var') else self.sm.get('python_paths.python27', 'Not set')))
        self._log("  Python 3.x: {}".format(self.py3_var.get() if hasattr(self, 'py3_var') else self.sm.get('python_paths.python3', 'Not set')))
        self._log("=" * 60)

        self.test_queue = [scale]
        self._run_tests()

    def _run_tests(self):
        """运行测试队列"""
        if not self.test_queue:
            self._on_test_complete()
            return

        self.is_running = True
        self.should_stop = False
        self.start_time = datetime.now()
        self.completed_tests = 0
        self._refresh_opensource_support()

        # Generate output directory
        base_dir = self.data_dir_var.get().strip() if hasattr(self, 'data_dir_var') else ''
        if not base_dir:
            base_dir = r'C:\temp\arcgis_benchmark_data'
        if hasattr(self, 'timestamp_var') and self.timestamp_var.get():
            self.current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.current_output_dir = os.path.join(base_dir, self.current_timestamp)
        else:
            self.current_timestamp = ''
            self.current_output_dir = base_dir
        self.root.after(0, lambda: self._log("Output directory: {}".format(self.current_output_dir)))
        total_units = self._estimate_total_progress_units()
        self.completed_tests = 0
        self.total_tests = total_units
        self.root.after(0, lambda t=total_units: self._update_progress(0, t))

        # Update UI state
        self.run_btn.config(state='disabled')
        self.stop_btn.config(state='normal')

        # Start test thread
        threading.Thread(target=self._test_worker).start()

    def _test_worker(self):
        """测试工作线程"""
        try:
            total_scales = len(self.test_queue)
            for idx, scale in enumerate(self.test_queue):
                if self.should_stop:
                    break

                self.root.after(0, lambda s=scale, i=idx, t=total_scales:
                    self._log("Starting scale: {} ({}/{})".format(s, i+1, t)))

                self._run_single_scale(scale)

        except Exception as e:
            self.root.after(0, lambda: self._log("Error: {}".format(str(e)), "ERROR"))

        finally:
            self.root.after(0, self._on_test_complete)

    def _run_single_scale(self, scale):
        """运行单个规模的测试"""
        py27_path = self.py27_var.get() if hasattr(self, 'py27_var') else self.sm.get('python_paths.python27', '')
        py3_path = self.py3_var.get() if hasattr(self, 'py3_var') else self.sm.get('python_paths.python3', '')

        if not py27_path or not os.path.exists(py27_path):
            self.root.after(0, lambda: self._log("Python 2.7 not found, skipping", "WARNING"))
        else:
            self._run_python_benchmark(py27_path, scale, 'py2', self.current_output_dir)

        if not py3_path or not os.path.exists(py3_path):
            self.root.after(0, lambda: self._log("Python 3.x not found, skipping", "WARNING"))
        else:
            self._run_python_benchmark(py3_path, scale, 'py3', self.current_output_dir)

            # Open source tests (Python 3 only)
            if self.os_var.get() and self.os_available:
                self._run_python_benchmark(py3_path, scale, 'os', self.current_output_dir)

    def _run_python_benchmark(self, python_path, scale, test_type, output_dir=None):
        """运行Python基准测试"""
        if self.should_stop:
            return

        # Get script directory for absolute paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        run_benchmarks_path = os.path.join(script_dir, 'run_benchmarks.py')

        cmd = [
            python_path,
            '-u',
            run_benchmarks_path,
            '--scale', scale,
            '--runs', str(self.runs_var.get() if hasattr(self, 'runs_var') else self.sm.get('test_settings.runs', 3)),
            '--warmup', str(self.warmup_var.get() if hasattr(self, 'warmup_var') else self.sm.get('test_settings.warmup', 1)),
            '--generate-data'
        ]

        if output_dir:
            cmd.extend(['--output-dir', output_dir])

        if test_type == 'os':
            cmd.append('--opensource')

        if self.mp_var.get():
            cmd.append('--multiprocess')
            cmd.extend(['--mp-workers', str(self.workers_var.get() if hasattr(self, 'workers_var') else self.sm.get('test_settings.mp_workers', 4))])

        test_name = "{} ({})".format(test_type.upper(), scale)
        self.root.after(0, lambda: self.current_test_label.config(text=test_name))
        self.root.after(0, lambda: self._log("Running: {}".format(' '.join(cmd)), "CMD"))
        self.root.after(0, lambda: self._advance_progress(1))

        try:
            # Set working directory to script location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                cwd=script_dir
            )

            self.current_process = process

            for line in process.stdout:
                if self.should_stop:
                    process.terminate()
                    break
                decoded_line = line.strip()
                if decoded_line:
                    if ('正在执行:' in decoded_line or
                            'Running multiprocess comparison:' in decoded_line):
                        self.root.after(0, lambda: self._advance_progress(1))
                    self.root.after(0, lambda l=decoded_line: self._log(l))

            process.wait()

            if process.returncode == 0:
                self.root.after(0, lambda: self._log("Completed: {}".format(test_name), "SUCCESS"))
            else:
                self.root.after(0, lambda: self._log("Failed: {} (code: {})".format(test_name, process.returncode), "ERROR"))

        except Exception as e:
            self.root.after(0, lambda: self._log("Error running {}: {}".format(test_name, str(e)), "ERROR"))

        finally:
            self.current_process = None

    def _stop_test(self):
        """停止测试"""
        if not self.is_running:
            return

        self.should_stop = True
        self._log("Stopping...", "WARNING")

        if self.current_process:
            try:
                self.current_process.terminate()
            except:
                pass

    def _on_test_complete(self):
        """测试完成回调"""
        self.is_running = False
        self.current_process = None
        self.test_queue = []

        # Reset UI
        self.run_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.completed_tests = 0
        self.total_tests = 0
        self._render_total_progress()
        self.current_test_label.config(text=self.sm.get_text('status_ready'))
        self.eta_label.config(text="")

        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        self._log("=" * 70, "SUCCESS")
        self._log("All tests completed in {:.1f}s".format(elapsed), "SUCCESS")
        self._log("", "INFO")

        # 生成对比报告
        self._generate_comparison_report()

    def _generate_comparison_report(self):
        """生成对比报告"""
        self._log("Generating comparison report...", "INFO")
        try:
            py3_path = self.py3_var.get() if hasattr(self, 'py3_var') else self.sm.get('python_paths.python3', 'python')

            results_dir = getattr(self, 'current_output_dir', None)
            if not results_dir:
                results_dir = os.path.join('results')
            results_dir = os.path.abspath(results_dir)
            output_dir = results_dir

            raw_root = os.path.join(results_dir, 'data')
            search_root = raw_root if os.path.isdir(raw_root) else results_dir

            py2_files = self._find_result_files(search_root, 'benchmark_results_py2')
            py3_files = self._find_result_files(search_root, 'benchmark_results_py3')
            os_files = self._find_result_files(search_root, 'benchmark_results_os')
            if not os_files:
                os_files = self._find_result_files(search_root, 'opensource')

            if not py2_files or not py3_files:
                self._log("Skip comparison report: missing benchmark result files.", "ERROR")
                if not py2_files:
                    self._log("  Missing: benchmark_results_py2.json", "ERROR")
                if not py3_files:
                    self._log("  Missing: benchmark_results_py3.json", "ERROR")
                if self.os_var.get() and not os_files:
                    self._log("  Missing: benchmark_results_os.json", "ERROR")
                return

            script_dir = os.path.dirname(os.path.abspath(__file__))
            analyze_results_path = os.path.join(script_dir, 'analyze_results.py')
            cmd = [
                py3_path,
                '-u',
                analyze_results_path,
                '--results-dir', results_dir,
                '--output-dir', output_dir
            ]

            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                cwd=script_dir
            )

            for line in process.stdout:
                decoded_line = line.strip()
                if decoded_line:
                    self._log(decoded_line)

            process.wait()

            if process.returncode == 0:
                self._log("Comparison report generated successfully!", "SUCCESS")
            else:
                self._log("Failed to generate comparison report (code: {})".format(process.returncode), "ERROR")

        except Exception as e:
            self._log("Error generating report: {}".format(str(e)), "ERROR")

        output_base = os.path.abspath(getattr(self, 'current_output_dir', os.path.join('results')))
        comparison_path = os.path.join(output_base, 'comparison_report.md')
        comparison_csv = os.path.join(output_base, 'comparison_data.csv')
        comparison_json = os.path.join(output_base, 'comparison_data.json')
        comparison_tex = os.path.join(output_base, 'comparison_table.tex')
        raw_root = os.path.join(output_base, 'data')
        log_root = raw_root if os.path.isdir(raw_root) else output_base
        py2_files = self._find_result_files(log_root, 'benchmark_results_py2')
        py3_files = self._find_result_files(log_root, 'benchmark_results_py3')
        os_files = self._find_result_files(log_root, 'benchmark_results_os')
        if not os_files:
            os_files = self._find_result_files(log_root, 'opensource')

        self._log("", "INFO")
        self._log("Results saved to:", "SUCCESS")
        if py2_files:
            self._log("  Py2 JSON: {}".format(py2_files[0]), "INFO")
        if py3_files:
            self._log("  Py3 JSON: {}".format(py3_files[0]), "INFO")
        if self.os_var.get() and os_files:
            self._log("  OS JSON: {}".format(os_files[0]), "INFO")
        self._log("  Comparison: {}".format(comparison_path), "INFO")
        self._log("  CSV: {}".format(comparison_csv), "INFO")
        self._log("  JSON: {}".format(comparison_json), "INFO")
        self._log("  TEX: {}".format(comparison_tex), "INFO")
        self._log("=" * 70, "SUCCESS")

    def _toggle_language(self):
        current_lang = self.sm.get('language', 'zh')
        new_lang = 'en' if current_lang == 'zh' else 'zh'
        self.sm.set('language', new_lang)
        self.sm.save_config()
        self._update_language()

    def _on_settings_changed(self):
        """设置变更后的回调"""
        self._update_language()
        if hasattr(self, 'py27_var'):
            self.py27_var.set(self.sm.get('python_paths.python27', ''))
        if hasattr(self, 'py3_var'):
            self.py3_var.set(self.sm.get('python_paths.python3', ''))
        if hasattr(self, 'runs_var'):
            self.runs_var.set(self.sm.get('test_settings.runs', 3))
        if hasattr(self, 'warmup_var'):
            self.warmup_var.set(self.sm.get('test_settings.warmup', 1))
        if hasattr(self, 'workers_var'):
            self.workers_var.set(self.sm.get('test_settings.mp_workers', 4))
        if hasattr(self, 'data_dir_var'):
            self.data_dir_var.set(self.sm.get('paths.data_dir', r'C:\temp\arcgis_benchmark_data'))
        if hasattr(self, 'timestamp_var'):
            self.timestamp_var.set(self.sm.get('result_settings.use_timestamp_folder', True))
        if hasattr(self, 'scale_var') and hasattr(self, 'scale_names'):
            scale_key = self.sm.get('test_settings.data_scale', 'tiny')
            self.scale_var.set(self.scale_names.get(scale_key, scale_key))
        self.mp_var.set(self.sm.get('test_settings.enable_multiprocess', False))
        self.os_var.set(self.sm.get('test_settings.enable_opensource', False))
        self._refresh_opensource_support()

    def _update_language(self):
        self.title_label.config(text=self.sm.get_text('app_title'))
        self.lang_btn.config(text=self.sm.get_text('btn_language'))
        if hasattr(self, 'open_temp_btn'):
            self.open_temp_btn.config(text=self.sm.get_text('btn_open_temp'))
        if hasattr(self, 'settings_card') and hasattr(self.settings_card, 'title_label'):
            self.settings_card.title_label.config(text=' ' + self.sm.get_text('settings_title'))

        # Update button texts
        self.run_btn.config(text=self.sm.get_text('btn_run'))
        self.stop_btn.config(text=self.sm.get_text('btn_stop'))
        if hasattr(self, 'settings_btn'):
            self.settings_btn.config(text=self.sm.get_text('btn_advanced_settings'))
        self._apply_opensource_state()

    def _on_closing(self):
        """窗口关闭处理"""
        if self.is_running:
            if not messagebox.askyesno("Confirm", "Tests are running. Exit anyway?"):
                return
            self._stop_test()

        # Check if remember last settings
        if self.sm.get('ui_settings.remember_last_settings', True):
            # Save current settings - get scale key from display name
            scale_display = self.scale_var.get()
            scale_key = self.scale_name_to_key.get(scale_display, 'tiny')
            self.sm.set('test_settings.data_scale', scale_key)
            if hasattr(self, 'py27_var'):
                self.sm.set('python_paths.python27', self.py27_var.get())
            if hasattr(self, 'py3_var'):
                self.sm.set('python_paths.python3', self.py3_var.get())
            if hasattr(self, 'runs_var'):
                self.sm.set('test_settings.runs', self.runs_var.get())
            if hasattr(self, 'warmup_var'):
                self.sm.set('test_settings.warmup', self.warmup_var.get())
            if hasattr(self, 'workers_var'):
                self.sm.set('test_settings.mp_workers', self.workers_var.get())
            if hasattr(self, 'data_dir_var'):
                self.sm.set('paths.data_dir', self.data_dir_var.get())
            if hasattr(self, 'timestamp_var'):
                self.sm.set('result_settings.use_timestamp_folder', self.timestamp_var.get())
            self.sm.set('test_settings.enable_multiprocess', self.mp_var.get())
            self.sm.set('test_settings.enable_opensource', self.os_var.get() and self.os_available)
            self.sm.save_config()

        self.root.destroy()


def main():
    root = tk.Tk()
    app = ModernBenchmarkGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
