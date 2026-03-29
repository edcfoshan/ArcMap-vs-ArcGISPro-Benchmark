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
from datetime import datetime

# Python 2/3 compatibility for file open
import io

def open_text_file(filepath, mode):
    """Open file with UTF-8 encoding for both Python 2 and 3"""
    if sys.version_info[0] >= 3:
        return io.open(filepath, mode, encoding='utf-8', newline='')
    else:
        return io.open(filepath, mode, encoding='utf-8')

def open_csv_file(filepath, mode):
    """Open CSV file with proper encoding"""
    # CSV module needs different handling in Python 2
    if sys.version_info[0] >= 3:
        return io.open(filepath, mode, encoding='utf-8', newline='')
    else:
        # Python 2: use binary mode for csv module
        import codecs
        return codecs.open(filepath, mode, encoding='utf-8')

class ResultExporter(object):
    """
    Export benchmark results to various formats
    """
    def __init__(self, output_dir):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def export_json(self, results, filename):
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
            'results': results
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
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
        
        # Get fieldnames from first result
        fieldnames = sorted(flat_results[0].keys())
        
        # Use compatible file open
        if sys.version_info[0] >= 3:
            with open_csv_file(filepath, 'w') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flat_results)
        else:
            # Python 2: encode to UTF-8 manually
            import codecs
            with codecs.open(filepath, 'w', encoding='utf-8') as f:
                # Write header
                f.write(','.join(fieldnames) + '\n')
                # Write rows
                for row in flat_results:
                    values = []
                    for key in fieldnames:
                        val = row.get(key, '')
                        if isinstance(val, unicode):
                            val = val.encode('utf-8')
                        elif not isinstance(val, basestring):
                            val = str(val)
                        else:
                            val = val.encode('utf-8')
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
            lines.append("### {}\n".format(result.get('test_name', 'Unknown')))
            for key, value in sorted(result.items()):
                lines.append("- **{}**: {}".format(key, value))
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
                    row_values.append(str(val))
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
        
        # Select key columns
        key_cols = ['test_name', 'mean_time', 'std_time', 'min_time', 'max_time']
        available_cols = [c for c in key_cols if c in results[0]]
        
        lines = []
        
        # Header
        header = "| " + " | ".join([c.replace('_', ' ').title() for c in available_cols]) + " |"
        lines.append(header)
        
        # Separator
        separator = "|" + "|".join(["---" for _ in available_cols]) + "|"
        lines.append(separator)
        
        # Data rows
        for result in results:
            row = "| " + " | ".join([self._format_cell(result.get(c, '')) for c in available_cols]) + " |"
            lines.append(row)
        
        return '\n'.join(lines)
    
    def _format_cell(self, value):
        """Format a cell value for display"""
        if isinstance(value, float):
            return "{:.4f}".format(value)
        return str(value)
    
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
            
            comparison.append({
                'test_name': test,
                'py2_time': py2_time,
                'py2_std': py2_result.get('std_time', 0),
                'py3_time': py3_time,
                'py3_std': py3_result.get('std_time', 0),
                'speedup': speedup,
                'faster': 'Python 3' if speedup > 1 else 'Python 2' if speedup < 1 else 'Equal'
            })
        
        return comparison
    
    def _format_comparison_markdown(self, comparison):
        """Format comparison as Markdown"""
        lines = []
        lines.append("# ArcGIS Python 2.7 vs Python 3.x Performance Comparison\n")
        lines.append("*Generated on {}*\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        lines.append("## Summary Table\n")
        lines.append("| Test | Python 2.7 (s) | Python 3.x (s) | Speedup | Faster |")
        lines.append("|------|----------------|----------------|---------|--------|")
        
        for item in comparison:
            lines.append("| {} | {:.4f} ± {:.4f} | {:.4f} ± {:.4f} | {:.2f}x | {} |".format(
                item['test_name'],
                item['py2_time'], item['py2_std'],
                item['py3_time'], item['py3_std'],
                item['speedup'],
                item['faster']
            ))
        
        lines.append("")
        lines.append("## Notes")
        lines.append("- Times are shown as: mean ± standard deviation")
        lines.append("- Speedup > 1 means Python 3.x is faster")
        lines.append("- Speedup < 1 means Python 2.7 is faster")
        
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
