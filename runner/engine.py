# -*- coding: utf-8 -*-
"""
Benchmark runner engine for the 6-core task matrix.
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import io
import json
import os
import sys
import time
import copy

# Add project directory to path
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from config import settings
from utils.timer import BenchmarkTimer, ProgressHeartbeat
from utils.gis_cleanup import clear_workspace_cache
from utils.result_exporter import ResultExporter
from utils.benchmark_manifest import load_manifest, manifest_summary, save_manifest


class RunnerEngine(object):
    """
    Execute a benchmark suite for a given stack, scale, format, and complexity.
    """

    def __init__(self, stack_name, matrix_path=None, scale=None, output_format="SHP",
                 complexity="simple", num_runs=None, warmup_runs=None,
                 output_dir=None, generate_data=False, run_log_path=None):
        self.stack_name = stack_name
        self.scale = scale or settings.DATA_SCALE
        self.output_format = output_format
        self.complexity = complexity
        self.num_runs = num_runs if num_runs is not None else settings.TEST_RUNS
        self.warmup_runs = warmup_runs if warmup_runs is not None else settings.WARMUP_RUNS
        self.output_dir = output_dir
        self.generate_data = generate_data
        self.run_log_path = run_log_path
        self.matrix = self._load_matrix(matrix_path)
        self.benchmarks = []
        self.results = []

    def _load_matrix(self, matrix_path):
        """Load matrix JSON. Fallback to minimal inline matrix."""
        if matrix_path is None:
            matrix_path = os.path.join(PROJECT_DIR, "configs", "matrix.json")
        try:
            with io.open(matrix_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "tasks": [
                    {"id": "Buffer", "category": "vector"},
                    {"id": "Intersect", "category": "vector"},
                    {"id": "SpatialJoin", "category": "vector"},
                    {"id": "Resample", "category": "raster"},
                    {"id": "Clip", "category": "raster"},
                    {"id": "PolygonToRaster", "category": "mixed"},
                ]
            }

    def _resolve_output_dir(self):
        """Set up timestamped or custom output directory."""
        if self.output_dir:
            output_dir = os.path.abspath(self.output_dir)
            settings.set_output_root(output_dir)
            self.output_dir = output_dir
        else:
            settings.set_timestamped_dirs()
            self.output_dir = settings.DATA_DIR

        # Isolate GIS datasets and per-benchmark JSON to data/ subdirectory
        data_dir = os.path.join(self.output_dir, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        settings.DATA_DIR = data_dir
        settings.SCRATCH_WORKSPACE = os.path.join(data_dir, 'scratch')
        settings.RAW_RESULTS_DIR = data_dir

    def _get_benchmarks(self):
        """Import and instantiate benchmarks for this stack and format."""
        from tasks.task_interface import get_benchmark_class

        benchmarks = []
        for task in self.matrix.get("tasks", []):
            task_id = task.get("id")
            cls = get_benchmark_class(task_id, self.stack_name)
            if cls is None:
                print("[Warning] No benchmark class for task={} stack={}".format(task_id, self.stack_name))
                continue
            try:
                instance = cls(output_format=self.output_format)
            except TypeError:
                instance = cls()
            benchmarks.append(instance)
        return benchmarks

    def _generate_data(self):
        """Generate test data if requested."""
        if not self.generate_data:
            return True
        print("\n" + "=" * 60)
        print("Generating Test Data")
        print("=" * 60)
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            from data.generate_test_data import TestDataGenerator
            generator = TestDataGenerator(output_format=self.output_format, complexity=self.complexity)
            datasets = generator.generate_all()
            if not datasets:
                clear_workspace_cache(settings.DATA_DIR)
                print("\nTest data generation failed")
                return False
            clear_workspace_cache(settings.DATA_DIR)
            print("\nTest data generated successfully")
            return True
        except Exception as e:
            print("\nError generating test data: {}".format(str(e)))
            clear_workspace_cache(settings.DATA_DIR)
            import traceback
            traceback.print_exc()
            return False

    def _get_git_commit(self):
        """Try to get current git commit hash."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def _get_dependency_versions(self):
        """Collect versions of key dependencies."""
        deps = {}
        for mod_name in ["geopandas", "rasterio", "shapely", "numpy", "arcpy"]:
            try:
                mod = __import__(mod_name)
                deps[mod_name] = getattr(mod, "__version__", "unknown")
            except Exception:
                pass
        return deps

    def _get_hardware_info(self):
        """Collect basic hardware info."""
        info = {}
        try:
            import platform
            info["cpu"] = platform.processor() or "Unknown"
            info["machine"] = platform.machine()
            info["os"] = platform.system() + " " + platform.release()
            info["cpu_count"] = os.cpu_count() if hasattr(os, "cpu_count") else "Unknown"
        except Exception:
            pass
        try:
            import psutil
            mem = psutil.virtual_memory()
            info["memory_gb"] = round(mem.total / (1024 ** 3), 1)
        except Exception:
            pass
        return info

    def _write_manifest(self):
        """Write run manifest with environment and matrix info."""
        manifest = {
            "version": "1.0",
            "stack": self.stack_name,
            "scale": self.scale,
            "output_format": self.output_format,
            "complexity": self.complexity,
            "num_runs": self.num_runs,
            "warmup_runs": self.warmup_runs,
            "matrix": self.matrix.get("version", "1.0"),
            "python_version": "{}.{}.{}".format(
                sys.version_info[0], sys.version_info[1], sys.version_info[2]
            ),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "git_commit": self._get_git_commit(),
            "dependencies": self._get_dependency_versions(),
            "hardware": self._get_hardware_info(),
            "random_seed": getattr(settings, "RANDOM_SEED", None),
        }
        try:
            import arcpy
            manifest["arcgis_version"] = getattr(arcpy, "GetInstallInfo", lambda: {})().get("Version", "unknown")
        except Exception:
            pass
        root = getattr(settings, "TIMESTAMPED_RESULTS_DIR", None) or self.output_dir
        save_manifest(root, manifest)
        return manifest

    def _write_latest_txt(self):
        """Write a latest.txt index pointing to the most recent result directory."""
        root = getattr(settings, "TIMESTAMPED_RESULTS_DIR", None) or self.output_dir
        data_root = getattr(settings, "DATA_ROOT_DIR", r"C:\temp\arcgis_benchmark_data")
        if root:
            try:
                with io.open(os.path.join(data_root, "latest.txt"), "w", encoding="utf-8") as f:
                    f.write(root)
            except Exception:
                pass

    def run(self):
        """Run all benchmarks for this engine configuration."""
        self._resolve_output_dir()

        if self.run_log_path:
            self._start_run_logging(self.run_log_path)

        settings.set_scale(self.scale)
        settings.ACTIVE_OUTPUT_FORMAT = self.output_format
        settings.ACTIVE_COMPLEXITY = self.complexity
        print("=" * 70)
        print("Benchmark Runner Engine")
        print("Stack: {} | Scale: {} | Format: {} | Complexity: {}".format(
            self.stack_name, self.scale, self.output_format, self.complexity
        ))
        print("=" * 70)

        if self.generate_data:
            if not self._generate_data():
                raise RuntimeError("Test data generation failed")

        self.benchmarks = self._get_benchmarks()
        if not self.benchmarks:
            print("\n[Warning] No benchmarks available for stack: {}".format(self.stack_name))
            return []

        print("\nTotal benchmarks: {}".format(len(self.benchmarks)))
        print("Warmup runs: {} | Test runs: {}".format(self.warmup_runs, self.num_runs))
        print("=" * 70)

        self.results = []
        for i, benchmark in enumerate(self.benchmarks, 1):
            print("\n" + "-" * 70)
            print("[{}/{}] Running: {} (category: {})".format(
                i, len(self.benchmarks), benchmark.name, benchmark.category
            ))
            print("-" * 70)
            try:
                stats = benchmark.run(num_runs=self.num_runs, warmup_runs=self.warmup_runs)
                self.results.append(stats)
                benchmark.save_results(settings.RAW_RESULTS_DIR)
                if stats.get("success"):
                    print("\n  [OK] {}: mean={:.4f}s std={:.4f}s".format(
                        benchmark.name, stats.get("mean_time", 0), stats.get("std_time", 0)
                    ))
                else:
                    print("\n  [FAILED] {}: {}".format(benchmark.name, stats.get("error", "Unknown")))
            except Exception as e:
                print("\n  [ERROR] {}: {}".format(benchmark.name, str(e)))
                import traceback
                traceback.print_exc()
                self.results.append({
                    "test_name": getattr(benchmark, "name", "unknown"),
                    "success": False,
                    "error": str(e)
                })

        self._write_manifest()
        self._write_latest_txt()
        self._save_group_results()
        self._print_summary()
        return self.results

    def _save_group_results(self):
        """Save consolidated results in the legacy schema."""
        if self.stack_name in ("arcpy_desktop", "arcpy_pro"):
            tag = "py{}".format(sys.version_info[0])
        else:
            tag = "os"

        exporter = ResultExporter(self.output_dir)
        metadata = {
            "result_tag": tag,
            "data_scale": self.scale,
            "test_runs": self.num_runs,
            "warmup_runs": self.warmup_runs,
            "stack": self.stack_name,
            "output_format": self.output_format,
            "complexity": self.complexity,
            "vector_config": copy.deepcopy(settings.VECTOR_CONFIG),
            "raster_config": copy.deepcopy(settings.RASTER_CONFIG),
            "benchmark_manifest_summary": manifest_summary(load_manifest(self.output_dir, default={})),
        }

        title = "Benchmark Results ({})".format(tag)
        if tag == "os":
            title = "Open-Source Benchmark Results"

        exporter.export_json(self.results, "benchmark_results_{}.json".format(tag), metadata=metadata)
        exporter.export_markdown(self.results, "benchmark_results_{}.md".format(tag), title=title)
        exporter.export_csv(self.results, "benchmark_results_{}.csv".format(tag))

    def _print_summary(self):
        """Print run summary."""
        print("\n" + "=" * 70)
        print("Benchmark Summary")
        print("=" * 70)
        successful = [r for r in self.results if r.get("success")]
        failed = [r for r in self.results if not r.get("success")]
        print("Total: {} | Success: {} | Failed: {}".format(len(self.results), len(successful), len(failed)))
        if successful:
            print("\nSuccessful:")
            for r in successful:
                print("  {:30s} {:.4f}s (+-{:.4f}s)".format(
                    r.get("test_name", "") + ":", r.get("mean_time", 0), r.get("std_time", 0)
                ))
        if failed:
            print("\nFailed:")
            for r in failed:
                print("  {}: {}".format(r.get("test_name", ""), r.get("error", "Unknown")))
        print("=" * 70)

    def _start_run_logging(self, log_path):
        """Mirror stdout/stderr to a log file (simplified)."""
        try:
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            self._log_handle = io.open(log_path, "w", encoding="utf-8")
            self._original_stdout = sys.stdout
            self._original_stderr = sys.stderr

            class TeeStream(object):
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

            sys.stdout = TeeStream(sys.stdout, self._log_handle)
            sys.stderr = TeeStream(sys.stderr, self._log_handle)
        except Exception:
            pass


def run_from_args(args):
    """
    Convenience wrapper to run the engine from parsed CLI arguments.
    Returns list of result dicts.
    """
    engine = RunnerEngine(
        stack_name=args.stack,
        matrix_path=args.matrix,
        scale=args.scale,
        output_format=args.format,
        complexity=args.complexity,
        num_runs=args.runs,
        warmup_runs=args.warmup,
        output_dir=args.output_dir,
        generate_data=args.generate_data,
        run_log_path=getattr(args, "run_log_path", None),
    )
    return engine.run()
