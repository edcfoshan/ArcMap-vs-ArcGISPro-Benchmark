# -*- coding: utf-8 -*-
"""
Settings Manager - Centralized configuration management with GUI support
支持多语言和持久化配置
"""
from __future__ import print_function, division, absolute_import
import os
import json
import sys
import copy
from datetime import datetime

# Configuration file path
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.arcgis_benchmark')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# Default configuration
DEFAULT_CONFIG = {
    'language': 'zh',  # 'zh' or 'en'
    'python_paths': {
        'python27': '',
        'python3': ''
    },
    'test_settings': {
        'runs': 3,
        'warmup': 1,
        'data_scale': 'tiny',
        'enable_multiprocess': False,
        'mp_workers': 4,
        'enable_opensource': False,
    },
    'result_settings': {
        'save_py2_results': True,
        'save_py3_results': True,
        'save_os_results': True,
        'use_timestamp_folder': True,
        'retention_days': 30,  # 0 = keep forever
    },
    'ui_settings': {
        'window_width': 1200,
        'window_height': 800,
        'show_advanced': False,
        'remember_last_settings': True,  # 保留上次设置
        'font_scale': 1.0,  # 字体缩放比例（默认正常字体）
    },
    'data_scale_custom': {
        'tiny': {
            'fishnet_rows': 50,
            'fishnet_cols': 50,
            'random_points': 1000,
            'buffer_points': 1000,
            'intersect_features': 10000,
            'spatial_join_points': 5000,
            'spatial_join_polygons': 500,
            'calculate_field_records': 10000,
            'constant_raster_size': 500,
        },
        'small': {
            'fishnet_rows': 100,
            'fishnet_cols': 100,
            'random_points': 10000,
            'buffer_points': 10000,
            'intersect_features': 100000,
            'spatial_join_points': 50000,
            'spatial_join_polygons': 1000,
            'calculate_field_records': 100000,
            'constant_raster_size': 1000,
        },
        'standard': {
            'fishnet_rows': 500,
            'fishnet_cols': 500,
            'random_points': 50000,
            'buffer_points': 50000,
            'intersect_features': 300000,
            'spatial_join_points': 200000,
            'spatial_join_polygons': 5000,
            'calculate_field_records': 300000,
            'constant_raster_size': 5000,
        },
        'medium': {
            'fishnet_rows': 1000,
            'fishnet_cols': 1000,
            'random_points': 100000,
            'buffer_points': 100000,
            'intersect_features': 1000000,
            'spatial_join_points': 500000,
            'spatial_join_polygons': 10000,
            'calculate_field_records': 1000000,
            'constant_raster_size': 10000,
        },
        'large': {
            'fishnet_rows': 5000,
            'fishnet_cols': 5000,
            'random_points': 500000,
            'buffer_points': 500000,
            'intersect_features': 5000000,
            'spatial_join_points': 2000000,
            'spatial_join_polygons': 50000,
            'calculate_field_records': 5000000,
            'constant_raster_size': 30000,
        },
    },
    'paths': {
        'data_dir': r'C:\temp\arcgis_benchmark_data',
        'custom_output_dir': '',  # empty = use default
    },
}

# Translations
TRANSLATIONS = {
    'zh': {
        # Window titles
        'app_title': 'ArcGIS Python 性能对比测试工具',
        'settings_title': '测试设置',

        # Menu
        'menu_file': '文件',
        'menu_settings': '设置',
        'menu_help': '帮助',
        'menu_exit': '退出',
        'menu_save_config': '保存配置',
        'menu_load_config': '加载配置',

        # Settings panel
        'tab_basic': '基本设置',
        'tab_advanced': '高级设置',
        'tab_data_scale': '数据规模',
        'tab_results': '结果设置',

        # Basic settings
        'label_language': '界面语言:',
        'label_python27': 'Python 2.7 路径:',
        'label_python3': 'Python 3.x 路径:',
        'btn_browse': '浏览...',
        'btn_verify': '验证环境',
        'label_runs': '测试运行次数:',
        'label_warmup': '预热运行次数:',
        'label_scale': '数据规模:',
        'label_workers': '多进程Worker数:',

        # Checkboxes
        'chk_multiprocess': '启用多进程测试',
        'chk_opensource': '启用开源库测试',
        'chk_py2': '保存 Python 2.7 结果',
        'chk_py3': '保存 Python 3.x 结果',
        'chk_os': '保存开源库结果',
        'chk_timestamp_folder': '使用带时间戳的文件夹',

        # Buttons
        'btn_run': '开始测试',
        'btn_run_all': '五级连跑',
        'btn_stop': '停止测试',
        'btn_open_temp': '打开生成结果文件夹',
        'btn_save_settings': '保存设置',
        'btn_reset': '恢复默认',

        # Status
        'status_ready': '就绪',
        'status_running': '运行中...',
        'status_completed': '测试完成',
        'status_stopped': '已停止',
        'status_error': '错误',

        # Progress
        'progress_total': '总进度',
        'progress_current': '当前测试',
        'eta': '预计剩余',

        # Scale names
        'scale_tiny': '超小 (Tiny)',
        'scale_small': '小型 (Small)',
        'scale_standard': '标准 (Standard)',
        'scale_medium': '中型 (Medium)',
        'scale_large': '大型 (Large)',

        # Messages
        'msg_config_saved': '配置已保存',
        'msg_config_loaded': '配置已加载',
        'msg_invalid_python': '无效的Python路径',
        'msg_verifying': '正在验证环境...',
        'msg_verify_ok': '环境验证通过',
        'msg_verify_fail': '环境验证失败',

        # Data scale parameters
        'param_fishnet': '渔网行列数:',
        'param_random_points': '随机点数量:',
        'param_buffer': '缓冲点数量:',
        'param_intersect': '叠加要素数量:',
        'param_spatial_join': '空间连接点数/面数:',
        'param_calculate': '字段计算记录数:',
        'param_raster': '栅格大小:',

        # Result settings
        'label_retention': '结果保留天数:',
        'retention_forever': '0 = 永久保留',

        # UI settings
        'chk_remember_settings': '保留上次设置（下次启动恢复）',
        'label_font_scale': '界面字体缩放:',
        'font_scale_small': '小 (1.0x)',
        'font_scale_normal': '正常 (1.2x)',
        'font_scale_large': '大 (1.5x)',
        'font_scale_huge': '超大 (2.0x)',

        # Quick settings
        'chk_mp': '多进程 (MP)',
        'chk_os': '开源库 (OS)',
        'tooltip_mp': '启用多进程并行测试（4 workers）',
        'tooltip_os': '启用开源库对比测试（GeoPandas/Rasterio）',
        'btn_language': 'English',
        'label_scale_select': '数据规模:',
    },
    'en': {
        # Window titles
        'app_title': 'ArcGIS Python Performance Benchmark Tool',
        'settings_title': 'Test Settings',

        # Menu
        'menu_file': 'File',
        'menu_settings': 'Settings',
        'menu_help': 'Help',
        'menu_exit': 'Exit',
        'menu_save_config': 'Save Config',
        'menu_load_config': 'Load Config',

        # Settings panel
        'tab_basic': 'Basic',
        'tab_advanced': 'Advanced',
        'tab_data_scale': 'Data Scale',
        'tab_results': 'Results',

        # Basic settings
        'label_language': 'Language:',
        'label_python27': 'Python 2.7 Path:',
        'label_python3': 'Python 3.x Path:',
        'btn_browse': 'Browse...',
        'btn_verify': 'Verify',
        'label_runs': 'Test Runs:',
        'label_warmup': 'Warmup Runs:',
        'label_scale': 'Data Scale:',
        'label_workers': 'MP Workers:',

        # Checkboxes
        'chk_multiprocess': 'Enable Multiprocess Tests',
        'chk_opensource': 'Enable Open-Source Tests',
        'chk_py2': 'Save Python 2.7 Results',
        'chk_py3': 'Save Python 3.x Results',
        'chk_os': 'Save Open-Source Results',
        'chk_timestamp_folder': 'Use Timestamped Folders',

        # Buttons
        'btn_run': 'Run Tests',
        'btn_run_all': 'Run All Scales',
        'btn_stop': 'Stop',
        'btn_open_temp': 'Open Generated Results Folder',
        'btn_save_settings': 'Save Settings',
        'btn_reset': 'Reset Default',

        # Status
        'status_ready': 'Ready',
        'status_running': 'Running...',
        'status_completed': 'Completed',
        'status_stopped': 'Stopped',
        'status_error': 'Error',

        # Progress
        'progress_total': 'Total Progress',
        'progress_current': 'Current Test',
        'eta': 'ETA',

        # Scale names
        'scale_tiny': 'Tiny',
        'scale_small': 'Small',
        'scale_standard': 'Standard',
        'scale_medium': 'Medium',
        'scale_large': 'Large',

        # Messages
        'msg_config_saved': 'Configuration saved',
        'msg_config_loaded': 'Configuration loaded',
        'msg_invalid_python': 'Invalid Python path',
        'msg_verifying': 'Verifying environment...',
        'msg_verify_ok': 'Environment verified',
        'msg_verify_fail': 'Environment verification failed',

        # Data scale parameters
        'param_fishnet': 'Fishnet Rows/Cols:',
        'param_random_points': 'Random Points:',
        'param_buffer': 'Buffer Points:',
        'param_intersect': 'Intersect Features:',
        'param_spatial_join': 'Spatial Join Points/Polygons:',
        'param_calculate': 'Calculate Field Records:',
        'param_raster': 'Raster Size:',

        # Result settings
        'label_retention': 'Retention Days:',
        'retention_forever': '0 = Keep Forever',

        # UI settings
        'chk_remember_settings': 'Remember last settings on restart',
        'label_font_scale': 'Font Scale:',
        'font_scale_small': 'Small (1.0x)',
        'font_scale_normal': 'Normal (1.2x)',
        'font_scale_large': 'Large (1.5x)',
        'font_scale_huge': 'Huge (2.0x)',

        # Quick settings
        'chk_mp': 'Multiprocess (MP)',
        'chk_os': 'Open-Source (OS)',
        'tooltip_mp': 'Enable multiprocess parallel testing (4 workers)',
        'tooltip_os': 'Enable open-source library comparison (GeoPandas/Rasterio)',
        'btn_language': '中文',
        'label_scale_select': 'Data Scale:',
    }
}


class SettingsManager(object):
    """管理应用程序设置的类"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.config = self._load_config()

    def _load_config(self):
        """从文件加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = copy.deepcopy(DEFAULT_CONFIG)
                    self._deep_update(config, saved_config)
                    return config
            except Exception as e:
                print("Error loading config: {}".format(e))
        return copy.deepcopy(DEFAULT_CONFIG)

    def _deep_update(self, d, u):
        """递归更新字典"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v

    def save_config(self):
        """保存配置到文件"""
        try:
            if not os.path.exists(CONFIG_DIR):
                os.makedirs(CONFIG_DIR)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print("Error saving config: {}".format(e))
            return False

    def get(self, key_path, default=None):
        """
        获取配置值，支持点号分隔的路径
        例如: get('test_settings.runs')
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path, value):
        """
        设置配置值，支持点号分隔的路径
        例如: set('test_settings.runs', 5)
        """
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value

    def get_text(self, key):
        """获取当前语言的文本"""
        lang = self.config.get('language', 'zh')
        return TRANSLATIONS.get(lang, TRANSLATIONS['zh']).get(key, key)

    def get_scale_config(self, scale=None):
        """获取指定规模的配置"""
        if scale is None:
            scale = self.config['test_settings']['data_scale']
        return self.config['data_scale_custom'].get(scale, {})

    def set_scale_config(self, scale, param, value):
        """设置指定规模的配置参数"""
        if scale not in self.config['data_scale_custom']:
            self.config['data_scale_custom'][scale] = {}
        self.config['data_scale_custom'][scale][param] = value

    def get_output_dir(self):
        """获取输出目录（带时间戳）"""
        base_dir = self.config['paths'].get('custom_output_dir', '')
        if not base_dir:
            base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')

        if self.config['result_settings'].get('use_timestamp_folder', True):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return os.path.join(base_dir, timestamp)
        return base_dir

    def get_temp_dir(self):
        """获取临时数据目录"""
        base_dir = self.config['paths'].get('data_dir', r'C:\temp\arcgis_benchmark_data')
        if self.config['result_settings'].get('use_timestamp_folder', True):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return os.path.join(base_dir, timestamp)
        return base_dir

    def should_save_result(self, result_type):
        """检查是否应该保存指定类型的结果"""
        settings = self.config['result_settings']
        if result_type == 'py2':
            return settings.get('save_py2_results', True)
        elif result_type == 'py3':
            return settings.get('save_py3_results', True)
        elif result_type == 'os':
            return settings.get('save_os_results', True)
        return True

    def reset_to_defaults(self):
        """重置为默认配置"""
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        self.save_config()

    def auto_detect_python_paths(self):
        """自动检测Python路径"""
        import glob
        import subprocess

        # Python 2.7 常见路径
        py27_paths = [
            r"C:\Python27\ArcGIS10.8\python.exe",
            r"C:\Python27\ArcGIS10.7\python.exe",
            r"C:\Python27\ArcGIS10.6\python.exe",
            r"C:\Python27\python.exe",
            r"C:\Program Files (x86)\ArcGIS\Python27\python.exe",
        ]

        # Python 3.x 常见路径
        py3_paths = [
            r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe",
            r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3-clone\python.exe",
            r"C:\ProgramData\Anaconda3\envs\arcgispro-py3\python.exe",
            r"C:\Python312\python.exe",
            r"C:\Python311\python.exe",
            r"C:\Python310\python.exe",
            r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe",
            r"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe",
            r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe",
        ]

        detected_py27 = None
        detected_py3 = None

        # 检测 Python 2.7
        for path in py27_paths:
            if os.path.exists(path):
                # 验证版本
                try:
                    result = subprocess.run(
                        [path, "-c", "import sys; print(sys.version_info.major)"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip() == "2":
                        detected_py27 = path
                        break
                except:
                    pass

        # 检测 Python 3.x
        for path in py3_paths:
            if os.path.exists(path):
                # 验证版本
                try:
                    result = subprocess.run(
                        [path, "-c", "import sys; print(sys.version_info.major)"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip() == "3":
                        detected_py3 = path
                        break
                except:
                    pass

        # 如果找到了，保存到配置
        if detected_py27:
            self.config['python_paths']['python27'] = detected_py27
        if detected_py3:
            self.config['python_paths']['python3'] = detected_py3

        # 返回检测结果
        return {
            'python27': detected_py27,
            'python3': detected_py3
        }


# Global settings manager instance
settings_manager = SettingsManager()


def get_text(key):
    """快捷函数获取文本"""
    return settings_manager.get_text(key)


if __name__ == '__main__':
    # Test
    sm = SettingsManager()
    print("Current language:", sm.get('language'))
    print("Test runs:", sm.get('test_settings.runs'))
    print("Tiny fishnet:", sm.get_scale_config('tiny'))
    print(sm.get_text('app_title'))
