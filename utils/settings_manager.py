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
DATA_SCALE_PROFILE_VERSION = 2

# Default configuration
DEFAULT_CONFIG = {
    'data_scale_profile_version': DATA_SCALE_PROFILE_VERSION,
    'language': 'zh',  # 'zh' or 'en'
    'python_paths': {
        'python27': '',
        'python3': ''
    },
    'test_settings': {
        'runs': 3,
        'warmup': 1,
        'data_scale': 'tiny',
        'data_scales': ['tiny'],
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
            'intersect_features_a': 10000,
            'intersect_features_b': 10000,
            'spatial_join_points': 5000,
            'spatial_join_polygons': 500,
            'calculate_field_records': 10000,
            'constant_raster_size': 500,
            'resample_source_size': 500,
            'resample_target_size': 250,
            'clip_ratio': 0.5,
        },
        'small': {
            'fishnet_rows': 125,
            'fishnet_cols': 125,
            'random_points': 12500,
            'buffer_points': 12500,
            'intersect_features_a': 125000,
            'intersect_features_b': 125000,
            'spatial_join_points': 62500,
            'spatial_join_polygons': 1250,
            'calculate_field_records': 125000,
            'constant_raster_size': 1250,
            'resample_source_size': 1250,
            'resample_target_size': 625,
            'clip_ratio': 0.5,
        },
        'standard': {
            'fishnet_rows': 250,
            'fishnet_cols': 250,
            'random_points': 25000,
            'buffer_points': 25000,
            'intersect_features_a': 250000,
            'intersect_features_b': 250000,
            'spatial_join_points': 125000,
            'spatial_join_polygons': 2500,
            'calculate_field_records': 250000,
            'constant_raster_size': 2500,
            'resample_source_size': 2500,
            'resample_target_size': 1250,
            'clip_ratio': 0.5,
        },
        'medium': {
            'fishnet_rows': 375,
            'fishnet_cols': 375,
            'random_points': 37500,
            'buffer_points': 37500,
            'intersect_features_a': 375000,
            'intersect_features_b': 375000,
            'spatial_join_points': 187500,
            'spatial_join_polygons': 3750,
            'calculate_field_records': 375000,
            'constant_raster_size': 3750,
            'resample_source_size': 3750,
            'resample_target_size': 1875,
            'clip_ratio': 0.5,
        },
        'large': {
            'fishnet_rows': 500,
            'fishnet_cols': 500,
            'random_points': 50000,
            'buffer_points': 50000,
            'intersect_features_a': 500000,
            'intersect_features_b': 500000,
            'spatial_join_points': 250000,
            'spatial_join_polygons': 5000,
            'calculate_field_records': 500000,
            'constant_raster_size': 5000,
            'resample_source_size': 5000,
            'resample_target_size': 2500,
            'clip_ratio': 0.5,
        },
    },
    'paths': {
        'data_dir': r'C:\temp\arcgis_benchmark_data',
        'custom_output_dir': '',  # empty = use default
    },
}

AVAILABLE_SCALES = ['tiny', 'small', 'standard', 'medium', 'large']

try:
    STRING_TYPES = (basestring,)
except NameError:
    STRING_TYPES = (str,)

# Translations
TRANSLATIONS = {
    'zh': {
        # Window titles
        'app_title': 'ArcGIS Python2、3 与开源库性能对比测试工具',
        'app_subtitle': 'ArcPy 与开源库性能基准对比',
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
        'label_vector_params': '向量参数:',
        'label_raster_params': '栅格参数:',

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
        'tooltip_runs': '正式计时的重复测试次数',
        'tooltip_warmup': '正式计时前的预热次数，消除文件缓存偏差',
        'tooltip_workers': '多进程分块时的并行 worker 数',

        'label_data_dir': '涓存椂鏁版嵁鐩綍:',
        'label_os_status': '寮€婧愬簱鐘舵€?:',

        'label_data_dir': '\u4e34\u65f6\u6570\u636e\u76ee\u5f55:',
        'label_os_status': '\u5f00\u6e90\u5e93\u72b6\u6001:',

        # Checkboxes
        'chk_multiprocess': '启用多进程测试',
        'chk_opensource': '启用开源库测试',
        'chk_py2': '保存 Python 2.7 结果',
        'chk_py3': '保存 Python 3.x 结果',
        'chk_os': '保存开源库结果',
        'chk_timestamp_folder': '使用带时间戳的文件夹',

        # Buttons
        'btn_run': '开始测试',
        'btn_stop': '停止测试',
        'btn_open_temp': '打开生成结果文件夹',
        'btn_save_settings': '保存设置',
        'btn_reset': '恢复默认',

        'btn_advanced_settings': '楂樼骇璁剧疆',
        'btn_recheck': '閲嶆柊妫€娴?',

        'btn_advanced_settings': '\u9ad8\u7ea7\u8bbe\u7f6e',
        'btn_recheck': '\u91cd\u65b0\u68c0\u6d4b',
        'btn_install_os': '\u5b89\u88c5\u5f00\u6e90\u5e93',

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
        'param_fishnet_rows': '渔网行数:',
        'param_fishnet_cols': '渔网列数:',
        'param_random_points': '随机点数量:',
        'param_buffer': '缓冲点数量:',
        'param_intersect': '叠加要素数量:',
        'param_intersect_a': '叠加图层A要素数:',
        'param_intersect_b': '叠加图层B要素数:',
        'param_spatial_join': '空间连接点数/面数:',
        'param_spatial_join_points': '空间连接点数:',
        'param_spatial_join_polygons': '空间连接面数:',
        'param_calculate': '字段计算记录数:',
        'param_raster': '栅格大小:',
        'param_constant_raster': '常量栅格大小:',
        'param_resample_source': '重采样源栅格大小:',
        'param_resample_target': '重采样目标栅格大小:',
        'param_clip_ratio': '裁剪比例:',

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
        'label_scale_select': '数据规模（可多选）:',
        'label_scale_params': '数据规模参数:',
        'label_edit_scale': '当前编辑规模:',
        'btn_apply_scale': '应用当前参数',
        'btn_reset_scale': '恢复默认值',

        # First-run dialog
        'first_run_title': '欢迎使用 ArcGIS 基准测试工具',
        'first_run_message': '首次启动，请确认 Python 路径配置。如路径为空，可点击“自动检测”。',
        'first_run_py27': 'Python 2.7 路径：',
        'first_run_py3': 'Python 3.x 路径：',
        'btn_auto_detect': '自动检测',
        'btn_confirm': '确认',
    },
    'en': {
        # Window titles
        'app_title': 'ArcGIS Python2、3 & Open-Source Performance Comparison Tool',
        'app_subtitle': 'ArcPy vs Open-Source Benchmark',
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
        'label_vector_params': 'Vector Parameters:',
        'label_raster_params': 'Raster Parameters:',

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
        'tooltip_runs': 'Number of timed test repetitions',
        'tooltip_warmup': 'Warm-up runs before timing to eliminate file-cache bias',
        'tooltip_workers': 'Number of parallel workers for chunked multiprocess tests',

        'label_data_dir': 'Temp Data Dir:',
        'label_os_status': 'Open-source status:',

        # Checkboxes
        'chk_multiprocess': 'Enable Multiprocess Tests',
        'chk_opensource': 'Enable Open-Source Tests',
        'chk_py2': 'Save Python 2.7 Results',
        'chk_py3': 'Save Python 3.x Results',
        'chk_os': 'Save Open-Source Results',
        'chk_timestamp_folder': 'Use Timestamped Folders',

        # Buttons
        'btn_run': 'Run Tests',
        'btn_stop': 'Stop',
        'btn_open_temp': 'Open Generated Results Folder',
        'btn_save_settings': 'Save Settings',
        'btn_reset': 'Reset Default',

        'btn_advanced_settings': 'Advanced Settings',
        'btn_recheck': 'Re-check',
        'btn_install_os': 'Install Open-Source Packages',

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
        'param_fishnet_rows': 'Fishnet Rows:',
        'param_fishnet_cols': 'Fishnet Cols:',
        'param_random_points': 'Random Points:',
        'param_buffer': 'Buffer Points:',
        'param_intersect': 'Intersect Features:',
        'param_intersect_a': 'Intersect Layer A Features:',
        'param_intersect_b': 'Intersect Layer B Features:',
        'param_spatial_join': 'Spatial Join Points/Polygons:',
        'param_spatial_join_points': 'Spatial Join Points:',
        'param_spatial_join_polygons': 'Spatial Join Polygons:',
        'param_calculate': 'Calculate Field Records:',
        'param_raster': 'Raster Size:',
        'param_constant_raster': 'Constant Raster Size:',
        'param_resample_source': 'Resample Source Size:',
        'param_resample_target': 'Resample Target Size:',
        'param_clip_ratio': 'Clip Ratio:',

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
        'label_scale_select': 'Data Scales (multi-select):',
        'label_scale_params': 'Data Scale Parameters:',
        'label_edit_scale': 'Edit Scale:',
        'btn_apply_scale': 'Apply Current',
        'btn_reset_scale': 'Reset Defaults',

        # First-run dialog
        'first_run_title': 'Welcome to ArcGIS Benchmark Tool',
        'first_run_message': 'First launch. Please confirm Python paths. Click "Auto-detect" if empty.',
        'first_run_py27': 'Python 2.7 path:',
        'first_run_py3': 'Python 3.x path:',
        'btn_auto_detect': 'Auto-detect',
        'btn_confirm': 'Confirm',
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
        self.is_first_run = not os.path.exists(CONFIG_FILE)

    def _load_config(self):
        """从文件加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    saved_profile_version = saved_config.get('data_scale_profile_version', 1)
                    # Merge with defaults to ensure all keys exist
                    config = copy.deepcopy(DEFAULT_CONFIG)
                    self._deep_update(config, saved_config)
                    config['data_scale_profile_version'] = saved_profile_version
                    self._migrate_scale_profile(config)
                    self._normalize_test_scales(config)
                    self._normalize_scale_configs(config)
                    return config
            except Exception as e:
                print("Error loading config: {}".format(e))
        config = copy.deepcopy(DEFAULT_CONFIG)
        self._migrate_scale_profile(config)
        self._normalize_test_scales(config)
        self._normalize_scale_configs(config)
        return config

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

    def _normalize_test_scales(self, config=None):
        """Normalize the saved multi-scale selection and keep backward compatibility."""
        target = config if config is not None else self.config
        test_settings = target.setdefault('test_settings', {})

        raw_scales = test_settings.get('data_scales', [])
        if isinstance(raw_scales, STRING_TYPES):
            raw_scales = [raw_scales]
        elif not isinstance(raw_scales, (list, tuple)):
            raw_scales = []

        normalized = []
        for scale in raw_scales:
            if scale in AVAILABLE_SCALES and scale not in normalized:
                normalized.append(scale)

        primary = test_settings.get('data_scale', 'tiny')
        if primary not in AVAILABLE_SCALES:
            primary = 'tiny'

        if not normalized:
            normalized = [primary]

        test_settings['data_scales'] = normalized
        test_settings['data_scale'] = primary if primary in normalized else normalized[0]
        return normalized

    def _migrate_scale_profile(self, config=None):
        """Reset cached scale presets when the repository profile is redefined."""
        target = config if config is not None else self.config
        current_version = target.get('data_scale_profile_version', 1)
        if current_version >= DATA_SCALE_PROFILE_VERSION:
            return False

        target['data_scale_custom'] = copy.deepcopy(DEFAULT_CONFIG['data_scale_custom'])
        target['data_scale_profile_version'] = DATA_SCALE_PROFILE_VERSION
        return True

    def _normalize_scale_configs(self, config=None):
        """Ensure saved scale configs keep the latest parameter schema."""
        target = config if config is not None else self.config
        scale_configs = target.setdefault('data_scale_custom', {})

        for scale, scale_config in list(scale_configs.items()):
            if not isinstance(scale_config, dict):
                scale_config = {}

            if 'intersect_features' in scale_config:
                legacy_value = scale_config.pop('intersect_features')
                scale_config.setdefault('intersect_features_a', legacy_value)
                scale_config.setdefault('intersect_features_b', legacy_value)

            merged = copy.deepcopy(DEFAULT_CONFIG['data_scale_custom'].get(scale, {}))
            self._deep_update(merged, scale_config)
            scale_configs[scale] = merged

        return scale_configs

    def get_text(self, key):
        """获取当前语言的文本"""
        lang = self.config.get('language', 'zh')
        return TRANSLATIONS.get(lang, TRANSLATIONS['zh']).get(key, key)

    def get_scale_config(self, scale=None):
        """获取指定规模的配置"""
        if scale is None:
            scale = self.config['test_settings']['data_scale']
        return self._merge_scale_config(scale)

    def get_scale_runtime_config(self, scale=None):
        """获取适合直接传递给运行器的规模配置。"""
        return copy.deepcopy(self.get_scale_config(scale))

    def _merge_scale_config(self, scale):
        """Merge defaults with saved values for a given scale."""
        if scale not in AVAILABLE_SCALES:
            scale = self.config.get('test_settings', {}).get('data_scale', 'tiny')
        if scale not in AVAILABLE_SCALES:
            scale = 'tiny'

        merged = copy.deepcopy(DEFAULT_CONFIG['data_scale_custom'].get(scale, {}))
        saved = copy.deepcopy(self.config.get('data_scale_custom', {}).get(scale, {}))

        if 'intersect_features' in saved:
            legacy_value = saved.pop('intersect_features')
            saved.setdefault('intersect_features_a', legacy_value)
            saved.setdefault('intersect_features_b', legacy_value)

        self._deep_update(merged, saved)
        return merged

    def get_selected_scales(self, default=None):
        """Get the selected benchmark scales as an ordered list."""
        scales = self.config.get('test_settings', {}).get('data_scales', [])
        if isinstance(scales, STRING_TYPES):
            scales = [scales]
        elif not isinstance(scales, (list, tuple)):
            scales = []

        ordered = [scale for scale in AVAILABLE_SCALES if scale in scales]
        if ordered:
            return ordered

        if default is not None:
            if isinstance(default, STRING_TYPES):
                default = [default]
            elif not isinstance(default, (list, tuple)):
                default = []
            ordered = [scale for scale in AVAILABLE_SCALES if scale in default]
            if ordered:
                return ordered

        fallback = self.config.get('test_settings', {}).get('data_scale', 'tiny')
        return [fallback if fallback in AVAILABLE_SCALES else 'tiny']

    def set_selected_scales(self, scales):
        """Persist the selected benchmark scales."""
        if isinstance(scales, STRING_TYPES):
            scales = [scales]
        elif not isinstance(scales, (list, tuple)):
            scales = []

        normalized = []
        for scale in scales:
            if scale in AVAILABLE_SCALES and scale not in normalized:
                normalized.append(scale)

        if not normalized:
            normalized = ['tiny']

        self.config['test_settings']['data_scales'] = normalized
        self.config['test_settings']['data_scale'] = normalized[0]
        return normalized

    def set_scale_config(self, scale, param, value):
        """设置指定规模的配置参数"""
        if scale not in self.config['data_scale_custom']:
            self.config['data_scale_custom'][scale] = {}
        if param == 'intersect_features':
            self.config['data_scale_custom'][scale]['intersect_features_a'] = value
            self.config['data_scale_custom'][scale]['intersect_features_b'] = value
        else:
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
