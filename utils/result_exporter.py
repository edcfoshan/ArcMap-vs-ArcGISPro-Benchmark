# -*- coding: utf-8 -*-
"""
Result export utilities for benchmark outputs.

This module keeps the public interface used by the repository:
- ResultExporter
- export_json
- export_csv
- export_markdown
- export_latex
- export_comparison_table

It is compatible with Python 2.7 and Python 3.x.
"""
from __future__ import print_function, division, absolute_import

import csv
import io
import json
import os
import sys
from datetime import datetime

PY2 = sys.version_info[0] < 3

try:
    text_type = unicode
except NameError:  # Python 3
    text_type = str


def _ensure_text(value):
    """Convert values to text for writing files safely."""
    if value is None:
        return u""

    if PY2:
        if isinstance(value, unicode):
            return value
        if isinstance(value, str):
            try:
                return value.decode('utf-8')
            except Exception:
                return value.decode('utf-8', 'ignore')
    else:
        if isinstance(value, str):
            return value
        if isinstance(value, bytes):
            return value.decode('utf-8', 'replace')

    if isinstance(value, dict):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except Exception:
            return text_type(value)

    if isinstance(value, (list, tuple, set)):
        try:
            return json.dumps(list(value), ensure_ascii=False)
        except Exception:
            return text_type(value)

    return text_type(value)


def _json_ready(value):
    """Recursively prepare values for JSON serialization."""
    if isinstance(value, dict):
        return dict((k, _json_ready(v)) for k, v in value.items())
    if isinstance(value, (list, tuple, set)):
        return [_json_ready(v) for v in value]
    return value


def _escape_markdown_cell(value):
    """Escape a single Markdown table cell."""
    text = _ensure_text(value)
    text = text.replace(u"\\", u"\\\\")
    text = text.replace(u"|", u"\\|")
    text = text.replace(u"\r\n", u"<br>")
    text = text.replace(u"\n", u"<br>")
    return text


def _escape_latex(text):
    """Escape text for a LaTeX table."""
    text = _ensure_text(text)
    replacements = [
        (u"&", u"\\&"),
        (u"%", u"\\%"),
        (u"$", u"\\$"),
        (u"#", u"\\#"),
        (u"_", u"\\_"),
        (u"{", u"\\{"),
        (u"}", u"\\}"),
        (u"~", u"\\textasciitilde{}"),
        (u"^", u"\\textasciicircum{}"),
        (u"\\", u"\\textbackslash{}"),
    ]
    for src, dst in replacements:
        text = text.replace(src, dst)
    return text


def _format_number(value, digits=4):
    """Format numeric values consistently."""
    try:
        if value is None or value == "":
            return u""
        return u"{:." + text_type(digits) + u"f}".format(float(value))
    except Exception:
        return _ensure_text(value)


def _open_text_file(filepath, mode):
    """Open a UTF-8 text file in a Python 2/3 friendly way."""
    if PY2:
        return io.open(filepath, mode, encoding='utf-8')
    return io.open(filepath, mode, encoding='utf-8', newline='')


def _open_csv_file(filepath):
    """Open a CSV file in a Python 2/3 friendly way."""
    if PY2:
        return io.open(filepath, 'w', encoding='utf-8')
    return io.open(filepath, 'w', encoding='utf-8', newline='')


class ResultExporter(object):
    """Export benchmark results to JSON, CSV, Markdown, and LaTeX."""

    def __init__(self, output_dir):
        self.output_dir = output_dir
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def export_json(self, results, filename, metadata=None):
        """Export results to JSON."""
        filepath = os.path.join(self.output_dir, filename)
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'python_version': "{}.{}.{}".format(
                sys.version_info[0],
                sys.version_info[1],
                sys.version_info[2],
            ),
            'metadata': metadata or {},
            'results': _json_ready(results),
        }

        json_text = json.dumps(export_data, indent=2, ensure_ascii=False)
        if PY2 and not isinstance(json_text, unicode):
            json_text = json_text.decode('utf-8')

        with _open_text_file(filepath, 'w') as handle:
            handle.write(json_text)

        return filepath

    def _flatten_results(self, results):
        """Flatten nested dictionaries one level deep.
        Also expand list fields like all_times into discrete columns."""
        flat_results = []
        for result in results or []:
            flat_row = {}
            if not isinstance(result, dict):
                flat_row['value'] = result
                flat_results.append(flat_row)
                continue

            for key, value in result.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        flat_row["{}_{}".format(key, subkey)] = subvalue
                elif isinstance(value, (list, tuple)) and key == 'all_times':
                    for idx, item in enumerate(value, 1):
                        flat_row["time_{}".format(idx)] = item
                else:
                    flat_row[key] = value
            flat_results.append(flat_row)
        return flat_results

    def export_csv(self, results, filename):
        """Export results to CSV."""
        filepath = os.path.join(self.output_dir, filename)

        flat_results = self._flatten_results(results)
        if not flat_results:
            with _open_csv_file(filepath):
                pass
            return filepath

        fieldnames = sorted(set().union(*[set(row.keys()) for row in flat_results]))

        if PY2:
            with _open_csv_file(filepath) as handle:
                handle.write(u",".join(fieldnames) + u"\n")
                for row in flat_results:
                    values = []
                    for field in fieldnames:
                        cell = _ensure_text(row.get(field, u""))
                        if u"," in cell or u"\"" in cell or u"\n" in cell or u"\r" in cell:
                            cell = u"\"{}\"".format(cell.replace(u"\"", u"\"\""))
                        values.append(cell)
                    handle.write(u",".join(values) + u"\n")
        else:
            with _open_csv_file(filepath) as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in flat_results:
                    writer.writerow(dict((k, _ensure_text(row.get(k, u""))) for k in fieldnames))

        return filepath

    def _markdown_table(self, rows, preferred_columns=None):
        """Create a Markdown table from rows."""
        if not rows:
            return u""

        columns = []
        if preferred_columns:
            for column in preferred_columns:
                if any(column in row and row.get(column) not in (None, u"") for row in rows):
                    columns.append(column)

        if not columns:
            columns = sorted(set().union(*[set(row.keys()) for row in rows]))

        if not columns:
            return u""

        lines = []
        lines.append(u"| " + u" | ".join(_escape_markdown_cell(c) for c in columns) + u" |")
        lines.append(u"|" + u"|".join([u"---" for _ in columns]) + u"|")

        for row in rows:
            values = []
            failed = not row.get('success', True)
            for column in columns:
                value = row.get(column, u"")
                if value in (None, u"") and failed:
                    value = u"N/A"
                values.append(_escape_markdown_cell(value))
            lines.append(u"| " + u" | ".join(values) + u" |")

        return u"\n".join(lines)

    def export_markdown(self, results, filename, title="Benchmark Results"):
        """Export results to Markdown."""
        filepath = os.path.join(self.output_dir, filename)
        results = results or []

        lines = []
        lines.append(u"# {}".format(_ensure_text(title)))
        lines.append(u"")
        lines.append(u"*Generated on {}*".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append(u"")

        summary_table = self._markdown_table(
            results,
            preferred_columns=['test_name', 'mean_time', 'std_time', 'min_time', 'max_time', 'speedup']
        )
        if summary_table:
            lines.append(u"## Summary")
            lines.append(u"")
            lines.append(summary_table)
            lines.append(u"")

        if results:
            lines.append(u"## Detailed Results")
            lines.append(u"")
            for result in results:
                if not isinstance(result, dict):
                    result = {'value': result}
                lines.append(u"### {}".format(_ensure_text(result.get('test_name', 'Unknown'))))
                lines.append(u"")
                for key in sorted(result.keys()):
                    lines.append(u"- **{}**: {}".format(_ensure_text(key), _ensure_text(result.get(key))))
                lines.append(u"")
        else:
            lines.append(u"_No results available._")
            lines.append(u"")

        content = u"\n".join(lines)
        if PY2 and not isinstance(content, unicode):
            content = content.decode('utf-8')

        with _open_text_file(filepath, 'w') as handle:
            handle.write(content)

        return filepath

    def export_latex(self, results, filename, caption="Benchmark Results"):
        """Export results to a small LaTeX table."""
        filepath = os.path.join(self.output_dir, filename)
        results = results or []

        lines = []
        lines.append(u"% Benchmark Results")
        lines.append(u"% Generated on {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append(u"")

        if results:
            preferred_columns = ['test_name', 'python_version', 'mean_time', 'std_time', 'speedup']
            columns = []
            for column in preferred_columns:
                if any(column in row for row in results if isinstance(row, dict)):
                    columns.append(column)
            if not columns:
                columns = sorted(set().union(*[set(row.keys()) for row in results if isinstance(row, dict)]))

            lines.append(u"\\begin{table}[htbp]")
            lines.append(u"\\centering")
            lines.append(u"\\caption{{{}}}".format(_escape_latex(caption)))
            lines.append(u"\\begin{tabular}{" + u"l" * len(columns) + u"}")
            lines.append(u"\\hline")
            lines.append(u" & ".join(_escape_latex(col.replace('_', ' ').title()) for col in columns) + u" \\\\")
            lines.append(u"\\hline")

            for result in results:
                if not isinstance(result, dict):
                    result = {'value': result}
                row_values = []
                for column in columns:
                    value = result.get(column, u"")
                    if column in ('mean_time', 'std_time', 'min_time', 'max_time'):
                        value = _format_number(value, 4)
                    elif column == 'speedup':
                        value = u"{}x".format(_format_number(value, 2)) if value not in (None, u"") else u""
                    row_values.append(_escape_latex(value))
                lines.append(u" & ".join(row_values) + u" \\\\")

            lines.append(u"\\hline")
            lines.append(u"\\end{tabular}")
            lines.append(u"\\label{tab:benchmark_results}")
            lines.append(u"\\end{table}")
        else:
            lines.append(u"No results available.")

        content = u"\n".join(lines)
        if PY2 and not isinstance(content, unicode):
            content = content.decode('utf-8')

        with _open_text_file(filepath, 'w') as handle:
            handle.write(content)

        return filepath

    def _create_comparison(self, results_py2, results_py3):
        """Create a simple side-by-side comparison."""
        py2_lookup = {}
        py3_lookup = {}

        for result in results_py2 or []:
            if isinstance(result, dict) and result.get('test_name') and result.get('success', True):
                py2_lookup[result['test_name']] = result

        for result in results_py3 or []:
            if isinstance(result, dict) and result.get('test_name') and result.get('success', True):
                py3_lookup[result['test_name']] = result

        test_names = sorted(set(py2_lookup.keys()) | set(py3_lookup.keys()))
        comparison = []

        for test_name in test_names:
            py2_result = py2_lookup.get(test_name, {})
            py3_result = py3_lookup.get(test_name, {})
            py2_time = py2_result.get('mean_time', 0) or 0
            py3_time = py3_result.get('mean_time', 0) or 0
            speedup = (py2_time / py3_time) if (py2_time > 0 and py3_time > 0) else 0

            if py2_time <= 0 or py3_time <= 0:
                faster = 'N/A'
            elif speedup > 1.05:
                faster = 'Python 3.x'
            elif speedup < 0.95:
                faster = 'Python 2.7'
            else:
                faster = 'Tie'

            comparison.append({
                'test_name': test_name,
                'py2_time': py2_time,
                'py2_std': py2_result.get('std_time', 0) or 0,
                'py3_time': py3_time,
                'py3_std': py3_result.get('std_time', 0) or 0,
                'speedup': speedup,
                'faster': faster,
            })

        return comparison

    def _format_comparison_markdown(self, comparison):
        """Format the comparison data as Markdown."""
        lines = []
        lines.append(u"# Benchmark Comparison")
        lines.append(u"")
        lines.append(u"*Generated on {}*".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        lines.append(u"")
        lines.append(u"| Test | Python 2.7 (s) | Python 3.x (s) | Speedup | Faster |")
        lines.append(u"|---|---|---|---|---|")

        for row in comparison:
            lines.append(u"| {} | {} | {} | {} | {} |".format(
                _escape_markdown_cell(row.get('test_name', u"")),
                _escape_markdown_cell(_format_number(row.get('py2_time', 0))),
                _escape_markdown_cell(_format_number(row.get('py3_time', 0))),
                _escape_markdown_cell(u"{:.2f}x".format(row.get('speedup', 0)) if row.get('speedup', 0) else u"N/A"),
                _escape_markdown_cell(row.get('faster', u"N/A")),
            ))

        return u"\n".join(lines)

    def _format_comparison_latex(self, comparison):
        """Format the comparison data as LaTeX."""
        lines = []
        lines.append(u"\\begin{table}[htbp]")
        lines.append(u"\\centering")
        lines.append(u"\\caption{Benchmark Comparison}")
        lines.append(u"\\begin{tabular}{lllll}")
        lines.append(u"\\hline")
        lines.append(u"Test & Python 2.7 (s) & Python 3.x (s) & Speedup & Faster \\\\")
        lines.append(u"\\hline")

        for row in comparison:
            lines.append(u"{} & {} & {} & {} & {} \\\\".format(
                _escape_latex(row.get('test_name', u"")),
                _escape_latex(_format_number(row.get('py2_time', 0))),
                _escape_latex(_format_number(row.get('py3_time', 0))),
                _escape_latex(u"{:.2f}x".format(row.get('speedup', 0)) if row.get('speedup', 0) else u"N/A"),
                _escape_latex(row.get('faster', u"N/A")),
            ))

        lines.append(u"\\hline")
        lines.append(u"\\end{tabular}")
        lines.append(u"\\end{table}")
        return u"\n".join(lines)

    def export_comparison_table(self, results_py2, results_py3, filename):
        """Export a side-by-side comparison table."""
        filepath = os.path.join(self.output_dir, filename)
        comparison = self._create_comparison(results_py2, results_py3)

        if filename.lower().endswith('.tex'):
            content = self._format_comparison_latex(comparison)
        else:
            content = self._format_comparison_markdown(comparison)

        if PY2 and not isinstance(content, unicode):
            content = content.decode('utf-8')

        with _open_text_file(filepath, 'w') as handle:
            handle.write(content)

        return filepath
