# -*- coding: utf-8 -*-
"""
Result export utilities for multiple formats
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import json
import os
import sys
import csv
import tempfile
from datetime import datetime

# Python 2/3 compatibility for file open
import io

if sys.version_info[0] >= 3:
    text_type = str
    binary_types = (bytes, bytearray)
    integer_types = (int,)
else:
    text_type = unicode  # noqa: F821 - Python 2 compatibility
    binary_types = (str,)
    integer_types = (int, long)  # noqa: F821 - Python 2 compatibility

def open_text_file(filepath, mode):
    """Open file with UTF-8 encoding for both Python 2 and 3"""
    if sys.version_info[0] >= 3:
        return io.open(filepath, mode, encoding='utf-8', newline='', errors='replace')
    else:
        return io.open(filepath, mode, encoding='utf-8', errors='replace')

def open_csv_file(filepath, mode):
    """Open CSV file with proper encoding"""
    # CSV module needs different handling in Python 2
    if sys.version_info[0] >= 3:
        return io.open(filepath, mode, encoding='utf-8', newline='', errors='replace')
    else:
        # Python 2: use binary mode for csv module
        import codecs
        return codecs.open(filepath, mode, encoding='utf-8', errors='replace')

class ResultExporter(object):
    """
    Export benchmark results to various formats
    """
    def __init__(self, output_dir):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def _decode_bytes(self, value):
        """Decode byte strings using a small fallback chain."""
        if not isinstance(value, binary_types):
            return value

        encodings = ['utf-8', 'gbk', 'gb2312', 'cp936', 'latin-1']
        for encoding in encodings:
            try:
                return value.decode(encoding)
            except Exception:
                pass

        return value.decode('utf-8', 'replace')

    def _safe_text(self, value):
        """Convert any scalar value into a safe text string."""
        if value is None:
            return ''

        if isinstance(value, text_type):
            return value

        if isinstance(value, binary_types):
            return self._decode_bytes(value)

        try:
            return text_type(value)
        except Exception:
            try:
                return text_type(repr(value))
            except Exception:
                return text_type('<unprintable>')

    def _normalize_json_value(self, value):
        """Recursively normalize values so json.dump can always serialize them."""
        if value is None:
            return None

        if isinstance(value, bool):
            return value

        if isinstance(value, integer_types):
            return value

        if isinstance(value, float):
            return value

        if isinstance(value, text_type):
            return value

        if isinstance(value, binary_types):
            return self._decode_bytes(value)

        if isinstance(value, dict):
            normalized = {}
            for key, item in value.items():
                if isinstance(key, (bool,) + integer_types):
                    json_key = key
                elif isinstance(key, float):
                    json_key = self._safe_text(key)
                else:
                    json_key = self._safe_text(key)
                normalized[json_key] = self._normalize_json_value(item)
            return normalized

        if isinstance(value, (list, tuple, set)):
            return [self._normalize_json_value(item) for item in value]

        if isinstance(value, datetime):
            return value.isoformat()

        if hasattr(value, 'isoformat'):
            try:
                return value.isoformat()
            except Exception:
                pass

        return self._safe_text(value)

    def _normalize_json_payload(self, payload):
        """Normalize the full export payload before serialization."""
        return self._normalize_json_value(payload)

    def _write_text_atomic(self, filepath, content):
        """Write text content to a temporary file and replace the target atomically."""
        directory = os.path.dirname(filepath) or '.'
        fd, temp_path = tempfile.mkstemp(
            prefix=os.path.basename(filepath) + '.',
            suffix='.tmp',
            dir=directory
        )
        os.close(fd)

        try:
            with open_text_file(temp_path, 'w') as f:
                f.write(content)

            if sys.version_info[0] >= 3:
                os.replace(temp_path, filepath)
            else:
                if os.path.exists(filepath):
                    os.remove(filepath)
                os.rename(temp_path, filepath)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
    
    def export_json(self, results, filename, metadata=None):
        """Export results to JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        
        # Add metadata
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'python_version': "{}.{}.{}".format(
                sys.version_info[0],
                sys.version_info[1],
                sys.version_info[2]
            ),
            'metadata': metadata or {},
            'results': results
        }

        normalized_data = self._normalize_json_payload(export_data)
        json_content = json.dumps(normalized_data, indent=2, ensure_ascii=False)
        self._write_text_atomic(filepath, json_content)
        
        return filepath
    
    def export_csv(self, results, filename):
        """Export results to CSV file"""
        filepath = os.path.join(self.output_dir, filename)
        
        if not results:
            return filepath
        
        # Flatten results for CSV
        flat_results = self._flatten_results(results)
        
        if not flat_results:
            return filepath
        
        # Get all possible fieldnames from all results (not just first)
        all_fields = set()
        normalized_rows = []
        for row in flat_results:
            normalized_row = {}
            for key, value in row.items():
                safe_key = self._safe_text(key)
                normalized_row[safe_key] = self._safe_text(value)
                all_fields.add(safe_key)
            normalized_rows.append(normalized_row)
        fieldnames = sorted(list(all_fields))
        
        # Use compatible file open
        if sys.version_info[0] >= 3:
            with open_csv_file(filepath, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(normalized_rows)
        else:
            # Python 2: encode to UTF-8 manually
            import codecs
            with codecs.open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(','.join(fieldnames) + '\n')
                # Write rows
                for row in normalized_rows:
                    values = []
                    for key in fieldnames:
                        val = row.get(key, '')
                        # Escape quotes and wrap in quotes if needed
                        if ',' in val or '"' in val or '\n' in val:
                            val = '"' + val.replace('"', '""') + '"'
                        values.append(val)
                    f.write(','.join(values) + '\n')
        
        return filepath
    
    def export_markdown(self, results, filename, title="Benchmark Results"):
        """Export results to Markdown table"""
        filepath = os.path.join(self.output_dir, filename)
        
        lines = []
        lines.append("# {}\n".format(title))
        lines.append("*Generated on {}*\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        # Summary table
        lines.append("## Summary\n")
        lines.append(self._create_markdown_table(results))
        lines.append("")
        
        # Detailed results
        lines.append("## Detailed Results\n")
        for result in results:
            lines.append("### {}\n".format(self._safe_text(result.get('test_name', 'Unknown'))))
            for key, value in sorted(result.items()):
                lines.append("- **{}**: {}".format(self._safe_text(key), self._safe_text(value)))
            lines.append("")
        
        content = '\n'.join(lines)
        if sys.version_info[0] < 3 and isinstance(content, str):
            content = content.decode('utf-8')
        with open_text_file(filepath, 'w') as f:
            f.write(content)
        
        return filepath
    
    def export_latex(self, results, filename, caption="Benchmark Results"):
        """Export results to LaTeX table"""
        filepath = os.path.join(self.output_dir, filename)
        
        lines = []
        lines.append("% Benchmark Results")
        lines.append("% Generated on {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append("")
        
        # Create LaTeX table
        if results:
            # Get columns
            columns = ['test_name', 'python_version', 'mean_time', 'std_time', 'speedup']
            available_cols = [c for c in columns if c in results[0]]
            
            lines.append("\\begin{table}[htbp]")
            lines.append("\\centering")
            lines.append("\\caption{{{}}}".format(caption))
            lines.append("\\begin{tabular}{" + "l" * len(available_cols) + "}")
            lines.append("\\hline")
            
            # Header
            header = " & ".join([c.replace('_', ' ').title() for c in available_cols]) + " \\\\"
            lines.append(header)
            lines.append("\\hline")
            
            # Data rows
            for result in results:
                row_values = []
                for col in available_cols:
                    val = result.get(col, '')
                    # Format numbers
                    if isinstance(val, float):
                        if col in ['mean_time', 'std_time']:
                            val = "{:.4f}".format(val)
                        elif col == 'speedup':
                            val = "{:.2f}x".format(val)
                    row_values.append(self._safe_text(val))
                lines.append(" & ".join(row_values) + " \\\\")
            
            lines.append("\\hline")
            lines.append("\\end{tabular}")
            lines.append("\\label{tab:benchmark_results}")
            lines.append("\\end{table}")
        
        with open_text_file(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        return filepath
    
    def export_comparison_table(self, results_py2, results_py3, filename):
        """Export side-by-side comparison table"""
        filepath = os.path.join(self.output_dir, filename)
        
        # Combine results
        comparison = self._create_comparison(results_py2, results_py3)
        
        # Export as Markdown
        md_content = self._format_comparison_markdown(comparison)
        
        with open_text_file(filepath, 'w') as f:
            f.write(md_content)
        
        return filepath
    
    def _flatten_results(self, results):
        """Flatten nested result dictionaries"""
        flat = []
        for result in results:
            flat_result = {}
            for key, value in result.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        flat_result["{}_{}".format(key, subkey)] = subvalue
                else:
                    flat_result[key] = value
            flat.append(flat_result)
        return flat
    
    def _create_markdown_table(self, results):
        """Create a Markdown table from results"""
        if not results:
            return ""

        # Select key columns - check all results, not just first one
        key_cols = ['test_name', 'mean_time', 'std_time', 'min_time', 'max_time']
        # Find columns that exist in ANY result
        available_cols = []
        for col in key_cols:
            for result in results:
                if col in result and result[col] != '':
                    available_cols.append(col)
                    break

        lines = []

        # Header
        header = "| " + " | ".join([c.replace('_', ' ').title() for c in available_cols]) + " |"
        lines.append(header)

        # Separator
        separator = "|" + "|".join(["---" for _ in available_cols]) + "|"
        lines.append(separator)

        # Data rows
        for result in results:
            row_values = []
            for col in available_cols:
                val = result.get(col, '')
                if val == '' or val is None:
                    # For failed tests, show N/A
                    if not result.get('success', True):
                        row_values.append('N/A')
                    else:
                        row_values.append('')
                else:
                    row_values.append(self._format_cell(val))
            row = "| " + " | ".join(row_values) + " |"
            lines.append(row)

        return '\n'.join(lines)
    
    def _format_cell(self, value):
        """Format a cell value for display"""
        if isinstance(value, float):
            return "{:.4f}".format(value)
        return self._safe_text(value)
    
    def _create_comparison(self, results_py2, results_py3):
        """Create comparison between Python 2 and 3 results"""
        comparison = []
        
        # Create lookup by test name
        py2_lookup = {r['test_name']: r for r in results_py2}
        py3_lookup = {r['test_name']: r for r in results_py3}
        
        all_tests = set(py2_lookup.keys()) | set(py3_lookup.keys())
        
        for test in sorted(all_tests):
            py2_result = py2_lookup.get(test, {})
            py3_result = py3_lookup.get(test, {})
            
            py2_time = py2_result.get('mean_time', 0)
            py3_time = py3_result.get('mean_time', 0)
            
            speedup = py2_time / py3_time if py3_time > 0 else 0
            
            faster_val = 'Python 3.x' if speedup > 1.05 else ('Python 2.7' if speedup < 0.95 else '相当')
            comparison.append({
                'test_name': test,
                'py2_time': py2_time,
                'py2_std': py2_result.get('std_time', 0),
                'py3_time': py3_time,
                'py3_std': py3_result.get('std_time', 0),
                'speedup': speedup,
                'faster': faster_val
            })
        
        return comparison
    
    def _format_comparison_markdown(self, comparison):
        """Format comparison as Markdown (Chinese)"""
        from config import settings
        
        lines = []
        lines.append("# ArcGIS Python 2.7 vs Python 3.x 性能对比报告\n")
        lines.append("*生成时间：{}*\n".format(datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')))
        
        # 数据规模信息
        lines.append("## 测试数据规模\n")
        lines.append("| 配置项 | 数值 |")
        lines.append("|--------|------|")
        lines.append("| 数据规模 | **{}** |".format(settings.DATA_SCALE.upper()))
        lines.append("| 渔网多边形 | {:,} ({:,}×{:,}) |".format(
            settings.VECTOR_CONFIG['fishnet_rows'] * settings.VECTOR_CONFIG['fishnet_cols'],
            settings.VECTOR_CONFIG['fishnet_rows'],
            settings.VECTOR_CONFIG['fishnet_cols']
        ))
        lines.append("| 随机点数量 | {:,} |".format(settings.VECTOR_CONFIG['random_points']))
        lines.append("| 缓冲区测试点 | {:,} |".format(settings.VECTOR_CONFIG['buffer_points']))
        lines.append("| 叠加分析要素 | {:,} × {:,} |".format(
            settings.VECTOR_CONFIG['intersect_features_a'],
            settings.VECTOR_CONFIG['intersect_features_b']
        ))
        lines.append("| 空间连接 | {:,}点 + {:,}多边形 |".format(
            settings.VECTOR_CONFIG['spatial_join_points'],
            settings.VECTOR_CONFIG['spatial_join_polygons']
        ))
        lines.append("| 字段计算记录 | {:,} |".format(settings.VECTOR_CONFIG['calculate_field_records']))
        lines.append("| 栅格大小 | {:,}×{:,} ({:,}像素) |".format(
            settings.RASTER_CONFIG['constant_raster_size'],
            settings.RASTER_CONFIG['constant_raster_size'],
            settings.RASTER_CONFIG['constant_raster_size'] ** 2
        ))
        lines.append("")
        
        # 规模说明
        scale_desc = {
            'tiny': '超小规模 - 快速验证/调试（约1-2分钟）',
            'small': '小型规模 - 功能测试（约5-10分钟）',
            'standard': '标准规模 - 常规测试（约15-30分钟）',
            'medium': '中型规模 - 性能对比（约30-60分钟）',
            'large': '大型规模 - 学术研究（约2-4小时）'
        }
        lines.append("**规模说明**: {}\n".format(scale_desc.get(settings.DATA_SCALE, '未知')))
        
        # Calculate summary statistics
        total_tests = len(comparison)
        py3_faster = sum(1 for item in comparison if item['speedup'] > 1.05)
        py2_faster = sum(1 for item in comparison if item['speedup'] < 0.95)
        equal = total_tests - py3_faster - py2_faster
        
        lines.append("## 统计摘要\n")
        lines.append("- **测试项目总数**: {}".format(total_tests))
        lines.append("- **Python 3.x 更快**: {} 项 ({:.1f}%)".format(py3_faster, py3_faster*100.0/total_tests if total_tests else 0))
        lines.append("- **Python 2.7 更快**: {} 项 ({:.1f}%)".format(py2_faster, py2_faster*100.0/total_tests if total_tests else 0))
        lines.append("- **性能相当**: {} 项 ({:.1f}%)".format(equal, equal*100.0/total_tests if total_tests else 0))
        lines.append("")
        
        # Average speedup
        if comparison:
            avg_speedup = sum(item['speedup'] for item in comparison) / len(comparison)
            lines.append("- **平均加速比**: {:.2f}x".format(avg_speedup))
            if avg_speedup > 1:
                lines.append("  - 总体趋势：Python 3.x 比 Python 2.7 快 {:.1f}%".format((avg_speedup-1)*100))
            elif avg_speedup < 1:
                lines.append("  - 总体趋势：Python 2.7 比 Python 3.x 快 {:.1f}%".format((1-avg_speedup)*100))
            else:
                lines.append("  - 总体趋势：两者性能相当")
        lines.append("")
        
        lines.append("## 详细对比表\n")
        lines.append("| 测试项目 | Python 2.7 (秒) | Python 3.x (秒) | 加速比 | 更快 |")
        lines.append("|---------|----------------|----------------|--------|------|")
        
        for item in comparison:
            faster_text = "Py3" if item['speedup'] > 1.05 else ("Py2" if item['speedup'] < 0.95 else "相当")
            lines.append("| {} | {:.4f} ± {:.4f} | {:.4f} ± {:.4f} | {:.2f}x | {} |".format(
                item['test_name'],
                item['py2_time'], item['py2_std'],
                item['py3_time'], item['py3_std'],
                item['speedup'],
                faster_text
            ))
        
        lines.append("")
        lines.append("## 说明")
        lines.append("- **时间格式**: 平均值 ± 标准差（秒）")
        lines.append("- **加速比**: Python 2.7 时间 / Python 3.x 时间")
        lines.append("- **加速比 > 1**: Python 3.x 更快")
        lines.append("- **加速比 < 1**: Python 2.7 更快")
        lines.append("- **加速比 ≈ 1**: 两者性能相当（差异 < 5%）")
        lines.append("")
        lines.append("## 测试项目说明")
        lines.append("### 矢量数据测试 (V1-V6)")
        lines.append("- **V1_CreateFishnet**: 创建渔网多边形")
        lines.append("- **V2_CreateRandomPoints**: 生成随机点")
        lines.append("- **V3_Buffer**: 缓冲区分析")
        lines.append("- **V4_Intersect**: 叠加分析")
        lines.append("- **V5_SpatialJoin**: 空间连接")
        lines.append("- **V6_CalculateField**: 字段计算")
        lines.append("")
        lines.append("### 栅格数据测试 (R1-R4)")
        lines.append("- **R1_CreateConstantRaster**: 创建常量栅格")
        lines.append("- **R2_Resample**: 栅格重采样")
        lines.append("- **R3_Clip**: 栅格裁剪")
        lines.append("- **R4_RasterCalculator**: 栅格计算")
        lines.append("")
        lines.append("### 混合测试 (M1-M2)")
        lines.append("- **M1_PolygonToRaster**: 矢转栅")
        lines.append("- **M2_RasterToPoint**: 栅转矢")
        lines.append("")
        lines.append("---")
        lines.append("*报告由 ArcGIS Python2、3 与开源库性能对比测试工具自动生成*")
        
        return '\n'.join(lines)


if __name__ == '__main__':
    # Test exporter
    test_results = [
        {
            'test_name': 'V1_CreateFishnet',
            'mean_time': 12.3456,
            'std_time': 0.5678,
            'min_time': 11.2345,
            'max_time': 13.4567
        },
        {
            'test_name': 'V2_RandomPoints',
            'mean_time': 8.9012,
            'std_time': 0.3456,
            'min_time': 8.1234,
            'max_time': 9.5678
        }
    ]
    
    exporter = ResultExporter('./test_output')
    print("Exporting to JSON...")
    print(exporter.export_json(test_results, 'test.json'))
    print("Exporting to Markdown...")
    print(exporter.export_markdown(test_results, 'test.md'))
