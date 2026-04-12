#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Main script to run ArcGIS Performance Benchmarks
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import argparse
import atexit
import io
import os
import sys

# Add project directory to path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from config import settings
from runner.engine import RunnerEngine

_RUN_LOG_HANDLE = None
_RUN_ORIGINAL_STDOUT = None
_RUN_ORIGINAL_STDERR = None


def _stop_run_logging():
    global _RUN_LOG_HANDLE, _RUN_ORIGINAL_STDOUT, _RUN_ORIGINAL_STDERR
    if _RUN_LOG_HANDLE is not None:
        try:
            _RUN_LOG_HANDLE.flush()
        except Exception:
            pass
        try:
            _RUN_LOG_HANDLE.close()
        except Exception:
            pass
        _RUN_LOG_HANDLE = None
    if _RUN_ORIGINAL_STDOUT is not None:
        sys.stdout = _RUN_ORIGINAL_STDOUT
        _RUN_ORIGINAL_STDOUT = None
    if _RUN_ORIGINAL_STDERR is not None:
        sys.stderr = _RUN_ORIGINAL_STDERR
        _RUN_ORIGINAL_STDERR = None


atexit.register(_stop_run_logging)


class _TeeStream(object):
    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary

    def write(self, data):
        if data is None:
            return
        try:
            self.primary.write(data)
        except Exception:
            pass
        try:
            self.secondary.write(data)
        except Exception:
            pass

    def flush(self):
        try:
            self.primary.flush()
        except Exception:
            pass
        try:
            self.secondary.flush()
        except Exception:
            pass


def _start_run_logging(log_path):
    global _RUN_LOG_HANDLE, _RUN_ORIGINAL_STDOUT, _RUN_ORIGINAL_STDERR
    if _RUN_LOG_HANDLE is not None:
        return
    log_dir = os.path.dirname(log_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    _RUN_ORIGINAL_STDOUT = sys.stdout
    _RUN_ORIGINAL_STDERR = sys.stderr
    _RUN_LOG_HANDLE = io.open(log_path, 'w', encoding='utf-8')
    sys.stdout = _TeeStream(sys.stdout, _RUN_LOG_HANDLE)
    sys.stderr = _TeeStream(sys.stderr, _RUN_LOG_HANDLE)


def _detect_stack(args):
    """Auto-detect stack from Python version and --opensource flag."""
    if getattr(args, 'stack', None):
        return args.stack
    if args.opensource and sys.version_info[0] >= 3:
        return "oss"
    if sys.version_info[0] == 2:
        return "arcpy_desktop"
    return "arcpy_pro"


def parse_args():
    parser = argparse.ArgumentParser(
        description='ArcGIS Python Performance Benchmark',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Legacy args (kept for backward compatibility with scheduler/GUI)
    parser.add_argument(
        '--category',
        choices=['vector', 'raster', 'mixed', 'all'],
        default='all',
        help='Benchmark category (legacy; ignored in core-6 mode)'
    )
    parser.add_argument('--scale', default=None, help='Data scale')
    parser.add_argument('--runs', type=int, default=None, help='Number of runs')
    parser.add_argument('--warmup', type=int, default=None, help='Warmup runs')
    parser.add_argument('--output-dir', type=str, default=None, help='Output directory')
    parser.add_argument('--generate-data', action='store_true', help='Generate test data')
    parser.add_argument('--multiprocess', action='store_true', help='Run multiprocess benchmarks (legacy)')
    parser.add_argument('--mp-workers', type=int, default=4, help='Multiprocess workers (legacy)')
    parser.add_argument('--opensource', action='store_true', help='Run open-source benchmarks')
    parser.add_argument('--tests', type=str, default=None, help='Comma-separated test names (legacy)')
    parser.add_argument('--scale-config-json', type=str, default=None, help='Custom scale overrides JSON')

    # New matrix-oriented args
    parser.add_argument('--stack', type=str, default=None,
                        choices=['arcpy_desktop', 'arcpy_pro', 'oss'],
                        help='Execution stack')
    parser.add_argument('--format', type=str, default='SHP',
                        choices=['SHP', 'GPKG', 'GDB'],
                        help='Output format for I/O comparison')
    parser.add_argument('--complexity', type=str, default='simple',
                        choices=['simple', 'medium', 'complex'],
                        help='Geometry complexity tier')
    parser.add_argument('--matrix', type=str, default=None,
                        help='Path to matrix JSON config')

    if len(sys.argv) == 1:
        return parser.parse_args([])
    return parser.parse_args()


def main():
    args = parse_args()

    # Apply legacy scale overrides if provided
    if args.scale_config_json:
        try:
            import json
            scale_overrides = json.loads(args.scale_config_json)
            if isinstance(scale_overrides, dict):
                settings.set_scale(args.scale or settings.DATA_SCALE, scale_overrides)
        except Exception as e:
            print("ERROR: Failed to parse --scale-config-json: {}".format(e))
            return 1

    stack = _detect_stack(args)

    # Set up output directory for logging
    output_dir = args.output_dir
    if output_dir:
        settings.set_output_root(os.path.abspath(output_dir))
    else:
        settings.set_timestamped_dirs()
        output_dir = settings.DATA_DIR

    run_log_path = os.path.join(
        getattr(settings, 'TIMESTAMPED_RESULTS_DIR', None) or output_dir,
        getattr(settings, 'BENCHMARK_RUN_LOG_NAME', 'benchmark_run.log')
    )
    _start_run_logging(run_log_path)

    # Warn if arcpy not available and OSS not requested
    if stack != 'oss':
        try:
            import arcpy  # noqa: F401
        except ImportError:
            print("[Warning] arcpy not available. Only open-source stack can run.")
            if not args.opensource:
                return 1

    engine = RunnerEngine(
        stack_name=stack,
        matrix_path=args.matrix,
        scale=args.scale or settings.DATA_SCALE,
        output_format=args.format,
        complexity=args.complexity,
        num_runs=args.runs,
        warmup_runs=args.warmup,
        output_dir=output_dir,
        generate_data=args.generate_data,
        run_log_path=run_log_path,
    )

    try:
        results = engine.run()
    except RuntimeError as e:
        print("\nERROR: {}".format(str(e)))
        return 1

    print("\n[Info] Results saved to: {}".format(output_dir))
    print("[Info] Benchmark run log: {}".format(run_log_path))
    return 0


if __name__ == '__main__':
    sys.exit(main())
