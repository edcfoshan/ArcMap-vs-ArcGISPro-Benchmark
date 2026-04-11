#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Browser-driven benchmark verification scheduler.

This module keeps the existing Tkinter GUI untouched and instead orchestrates
the benchmark scripts as subprocesses behind a local web console.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import threading
import time
import uuid
from collections import deque
from datetime import datetime

from config import settings

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_BENCHMARKS_SCRIPT = os.path.join(PROJECT_DIR, "run_benchmarks.py")
ANALYZE_RESULTS_SCRIPT = os.path.join(PROJECT_DIR, "analyze_results.py")

DEFAULT_SCALES = ["tiny", "small"]
ALL_SCALES = ["tiny", "small", "standard", "medium", "large"]
EXPECTED_BASE_TESTS = 12
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

PY27_CANDIDATES = [
    r"C:\Python27\ArcGIS10.8\python.exe",
    r"C:\Python27\ArcGIS10.7\python.exe",
    r"C:\Python27\ArcGIS10.6\python.exe",
    r"C:\Python27\ArcGIS10.5\python.exe",
    r"C:\Python27\ArcGIS10.4\python.exe",
    r"C:\Python27\ArcGIS10.3\python.exe",
    r"C:\Python27\ArcGIS10.2\python.exe",
    r"C:\Python27\python.exe",
    r"C:\Program Files (x86)\ArcGIS\Python27\python.exe",
]

PY3_CANDIDATES = [
    r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe",
    r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3-clone\python.exe",
    r"C:\Program Files\ArcGIS\Pro\bin\Python\python.exe",
    r"C:\ProgramData\Anaconda3\envs\arcgispro-py3\python.exe",
    r"C:\Python312\python.exe",
    r"C:\Python311\python.exe",
    r"C:\Python310\python.exe",
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe",
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe",
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe",
]


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_int(value, default, minimum=None, maximum=None):
    try:
        number = int(value)
    except Exception:
        number = default

    if minimum is not None:
        number = max(minimum, number)
    if maximum is not None:
        number = min(maximum, number)
    return number


def _format_command(cmd):
    try:
        return subprocess.list2cmdline(cmd)
    except Exception:
        return " ".join(cmd)


def _ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path)
    return path


def _probe_python_major(path, expected_major):
    if not path or not os.path.exists(path):
        return False

    probe = (
        "import sys\n"
        "sys.stdout.write(str(sys.version_info[0]))\n"
    )
    try:
        result = subprocess.run(
            [path, "-c", probe],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return False

    return result.returncode == 0 and result.stdout.strip() == str(expected_major)


def _detect_python_paths():
    py27 = ""
    py3 = ""

    for candidate in PY27_CANDIDATES:
        if _probe_python_major(candidate, 2):
            py27 = candidate
            break

    for candidate in PY3_CANDIDATES:
        if _probe_python_major(candidate, 3):
            py3 = candidate
            break

    return py27, py3


def _probe_opensource_support(python3_path):
    if not python3_path or not os.path.exists(python3_path):
        return False, "Python 3 interpreter not detected"

    probe = (
        "mods = ['geopandas', 'rasterio', 'shapely', 'numpy']\n"
        "missing = []\n"
        "for mod in mods:\n"
        "    try:\n"
        "        __import__(mod)\n"
        "    except Exception:\n"
        "        missing.append(mod)\n"
        "if missing:\n"
        "    print('MISSING:' + ','.join(missing))\n"
        "    raise SystemExit(1)\n"
        "print('OK')\n"
    )
    try:
        result = subprocess.run(
            [python3_path, "-u", "-c", probe],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:
        return False, str(exc)

    output = (result.stdout or "").strip()
    if result.returncode == 0 and output == "OK":
        return True, "Open-source packages are available"
    return False, output or "Open-source packages are unavailable"


def _default_output_base_dir():
    return os.path.abspath(getattr(settings, "DATA_DIR", r"C:\temp\arcgis_benchmark_data"))


def _default_config():
    py27_path, py3_path = _detect_python_paths()
    opensource_supported, opensource_reason = _probe_opensource_support(py3_path)

    return {
        "python27_path": py27_path,
        "python3_path": py3_path,
        "output_base_dir": _default_output_base_dir(),
        "selected_scales": list(DEFAULT_SCALES),
        "runs": _safe_int(getattr(settings, "TEST_RUNS", 3), 3, minimum=1),
        "warmup": _safe_int(getattr(settings, "WARMUP_RUNS", 1), 1, minimum=0),
        "generate_data": True,
        "include_opensource": opensource_supported,
        "opensource_supported": opensource_supported,
        "opensource_reason": opensource_reason,
        "multiprocess": True,
        "mp_workers": _safe_int(
            getattr(settings, "MULTIPROCESS_CONFIG", {}).get("num_workers", 4),
            4,
            minimum=1,
        ),
    }


def _make_stage(name):
    return {
        "name": name,
        "status": "pending",
        "return_code": None,
        "duration_sec": 0.0,
        "command": "",
        "output_tail": [],
        "summary": "",
        "details": {},
        "started_at": None,
        "finished_at": None,
    }


def _make_scale_state(scale, output_dir):
    return {
        "scale": scale,
        "status": "pending",
        "output_dir": output_dir,
        "stages": {
            "py2": _make_stage("py2"),
            "py3": _make_stage("py3"),
            "os": _make_stage("os"),
            "analysis": _make_stage("analysis"),
            "validation": _make_stage("validation"),
        },
        "raw_results": {},
        "artifacts": {},
        "issues": [],
        "started_at": None,
        "finished_at": None,
    }


def _list_result_files(root_dir):
    matches = []
    if not root_dir or not os.path.isdir(root_dir):
        return matches

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            lowered = filename.lower()
            if lowered.endswith(".json") and "benchmark_results" in lowered:
                matches.append(os.path.join(dirpath, filename))

    matches.sort()
    return matches


def _classify_result_file(filepath):
    lowered = os.path.basename(filepath).lower()
    if "benchmark_results_py2" in lowered:
        return "py2"
    if "benchmark_results_py3" in lowered and "benchmark_results_os" not in lowered and "opensource" not in lowered:
        return "py3"
    if "benchmark_results_os" in lowered or "opensource" in lowered or lowered.endswith("_os.json"):
        return "os"
    return None


def _load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_result_payload(filepath, expected_min_count=EXPECTED_BASE_TESTS, expected_tag=None):
    summary = {
        "path": filepath,
        "exists": os.path.exists(filepath) if filepath else False,
        "status": "failed",
        "count": 0,
        "success_count": 0,
        "failure_count": 0,
        "expected_min_count": expected_min_count,
        "expected_tag": expected_tag,
        "actual_tag": None,
        "metadata": {},
        "failed_tests": [],
        "error": None,
    }

    if not summary["exists"]:
        summary["error"] = "Missing file"
        return summary

    try:
        payload = _load_json(filepath)
    except Exception as exc:
        summary["error"] = "Failed to load JSON: {}".format(exc)
        return summary

    results = payload.get("results", [])
    metadata = payload.get("metadata", {})
    actual_tag = metadata.get("result_tag") if isinstance(metadata, dict) else None
    summary["metadata"] = metadata if isinstance(metadata, dict) else {}
    summary["actual_tag"] = actual_tag

    if expected_tag and actual_tag and str(actual_tag).lower() != str(expected_tag).lower():
        summary["error"] = "Unexpected result_tag: {}".format(actual_tag)
        return summary

    if not isinstance(results, list):
        summary["error"] = "results payload is not a list"
        return summary

    failed_tests = []
    success_count = 0
    for item in results:
        if isinstance(item, dict) and item.get("success", True):
            success_count += 1
        else:
            if isinstance(item, dict):
                failed_tests.append(item.get("test_name", "unknown"))
            else:
                failed_tests.append("unknown")

    summary["count"] = len(results)
    summary["success_count"] = success_count
    summary["failure_count"] = len(results) - success_count
    summary["failed_tests"] = failed_tests[:10]

    if summary["count"] < expected_min_count:
        summary["error"] = "Expected at least {} results, got {}".format(expected_min_count, summary["count"])
        return summary

    if summary["failure_count"] > 0:
        summary["error"] = "Result file contains {} failed test(s)".format(summary["failure_count"])
        return summary

    summary["status"] = "passed"
    return summary


class VerificationScheduler(object):
    """Manage one browser-driven verification job at a time."""

    def __init__(self):
        self._defaults = _default_config()
        self._lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._logs = deque(maxlen=400)
        self._worker = None
        self._active_process = None
        self._active_process_lock = threading.RLock()
        self._state = self._build_initial_state(self._defaults)

    def _build_initial_state(self, defaults=None):
        defaults = defaults or self._defaults
        py27_ready = bool(defaults["python27_path"] and os.path.exists(defaults["python27_path"]))
        py3_ready = bool(defaults["python3_path"] and os.path.exists(defaults["python3_path"]))
        return {
            "status": "idle",
            "job_id": None,
            "message": "Ready",
            "started_at": None,
            "finished_at": None,
            "session_root": None,
            "current_scale": None,
            "current_stage": None,
            "selected_scales": list(defaults["selected_scales"]),
            "config": defaults,
            "environment": {
                "python27_ready": py27_ready,
                "python3_ready": py3_ready,
                "opensource_supported": defaults["opensource_supported"],
                "opensource_reason": defaults["opensource_reason"],
                "project_dir": PROJECT_DIR,
                "base_output_dir": defaults["output_base_dir"],
            },
            "scales": [],
            "summary": {
                "total_scales": 0,
                "passed_scales": 0,
                "failed_scales": 0,
                "skipped_scales": 0,
            },
        }

    def snapshot(self):
        with self._state_lock:
            payload = copy.deepcopy(self._state)
            payload["logs"] = list(self._logs)
            payload["running"] = self.is_running()
            payload["has_error"] = payload.get("status") in ("failed", "stopped")
            return payload

    def is_running(self):
        worker = self._worker
        return bool(worker and worker.is_alive())

    def _set_summary_counts(self):
        with self._state_lock:
            scales = self._state.get("scales", [])
            passed = sum(1 for scale in scales if scale.get("status") == "passed")
            failed = sum(1 for scale in scales if scale.get("status") == "failed")
            skipped = sum(1 for scale in scales if scale.get("status") == "skipped")
            self._state["summary"] = {
                "total_scales": len(scales),
                "passed_scales": passed,
                "failed_scales": failed,
                "skipped_scales": skipped,
            }

    def _append_log(self, message):
        line = "[{}] {}".format(datetime.now().strftime("%H:%M:%S"), message)
        with self._state_lock:
            self._logs.append(line)

    def _select_scales(self, scales):
        if not scales:
            return list(DEFAULT_SCALES)

        ordered = []
        wanted = {str(scale).lower() for scale in scales}
        for scale in ALL_SCALES:
            if scale in wanted:
                ordered.append(scale)
        return ordered or list(DEFAULT_SCALES)

    def _unique_session_root(self, base_dir):
        base_dir = os.path.abspath(base_dir or _default_output_base_dir())
        _ensure_dir(base_dir)

        candidate = os.path.join(base_dir, _timestamp())
        suffix = 1
        while os.path.exists(candidate):
            candidate = os.path.join(base_dir, "{}_{}".format(_timestamp(), suffix))
            suffix += 1
        return candidate

    def _sanitize_config(self, payload):
        defaults = self._defaults
        config = {
            "python27_path": (payload.get("python27_path") or defaults["python27_path"] or "").strip(),
            "python3_path": (payload.get("python3_path") or defaults["python3_path"] or "").strip(),
            "output_base_dir": os.path.abspath(payload.get("output_base_dir") or defaults["output_base_dir"]),
            "selected_scales": self._select_scales(payload.get("selected_scales") or defaults["selected_scales"]),
            "runs": _safe_int(payload.get("runs"), defaults["runs"], minimum=1),
            "warmup": _safe_int(payload.get("warmup"), defaults["warmup"], minimum=0),
            "generate_data": bool(payload.get("generate_data", defaults["generate_data"])),
            "include_opensource": bool(payload.get("include_opensource", defaults["include_opensource"])),
            "multiprocess": bool(payload.get("multiprocess", defaults["multiprocess"])),
            "mp_workers": _safe_int(payload.get("mp_workers"), defaults["mp_workers"], minimum=1),
        }

        config["opensource_supported"], config["opensource_reason"] = _probe_opensource_support(config["python3_path"])
        if config["include_opensource"] and not config["opensource_supported"]:
            config["include_opensource"] = False
        return config

    def _find_latest_matching_file(self, root_dir, keyword):
        matches = []
        for path in _list_result_files(root_dir):
            if keyword in os.path.basename(path).lower():
                matches.append(path)
        if not matches:
            return None
        matches.sort(key=lambda path: os.path.getmtime(path))
        return matches[-1]

    def _build_benchmark_command(self, python_path, scale, output_dir, config, include_opensource=False):
        cmd = [
            python_path,
            "-u",
            RUN_BENCHMARKS_SCRIPT,
            "--category",
            "all",
            "--scale",
            scale,
            "--runs",
            str(config["runs"]),
            "--warmup",
            str(config["warmup"]),
            "--output-dir",
            output_dir,
            "--generate-data",
        ]

        if config["multiprocess"]:
            cmd.extend(["--multiprocess", "--mp-workers", str(config["mp_workers"])])

        if include_opensource:
            cmd.append("--opensource")

        return cmd

    def _run_process(self, scale_name, stage_name, cmd, cwd):
        started = time.time()
        output_tail = deque(maxlen=30)
        stage_result = {
            "status": "failed",
            "return_code": None,
            "duration_sec": 0.0,
            "command": _format_command(cmd),
            "output_tail": [],
            "summary": "",
            "details": {},
            "started_at": _now_iso(),
            "finished_at": None,
        }

        self._append_log("[{}:{}] {}".format(scale_name, stage_name, stage_result["command"]))
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"

        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception as exc:
            stage_result["summary"] = "Failed to start process: {}".format(exc)
            stage_result["details"]["error"] = str(exc)
            stage_result["finished_at"] = _now_iso()
            stage_result["duration_sec"] = time.time() - started
            self._append_log("[{}:{}] {}".format(scale_name, stage_name, stage_result["summary"]))
            return stage_result

        self._active_process = process
        try:
            if process.stdout is not None:
                for line in iter(process.stdout.readline, ""):
                    if line == "" and process.poll() is not None:
                        break
                    stripped = line.rstrip()
                    if stripped:
                        self._append_log(stripped)
                        output_tail.append(stripped)
                    if self._stop_event.is_set():
                        try:
                            process.terminate()
                        except Exception:
                            pass
                        break

            process.wait()
        finally:
            self._active_process = None

        stage_result["return_code"] = process.returncode
        stage_result["duration_sec"] = time.time() - started
        stage_result["output_tail"] = list(output_tail)
        stage_result["finished_at"] = _now_iso()

        if self._stop_event.is_set():
            stage_result["status"] = "stopped"
            stage_result["summary"] = "Stopped by user"
        elif process.returncode == 0:
            stage_result["status"] = "passed"
            stage_result["summary"] = "Completed successfully"
        else:
            stage_result["status"] = "failed"
            stage_result["summary"] = "Process exited with code {}".format(process.returncode)

        self._append_log("[{}:{}] {}".format(scale_name, stage_name, stage_result["summary"]))
        return stage_result

    def start(self, payload):
        with self._lock:
            if self.is_running():
                return {
                    "ok": False,
                    "error": "A verification job is already running",
                }

            config = self._sanitize_config(payload or {})
            if not config["python27_path"] or not os.path.exists(config["python27_path"]):
                return {
                    "ok": False,
                    "error": "Python 2.7 interpreter was not found",
                }
            if not config["python3_path"] or not os.path.exists(config["python3_path"]):
                return {
                    "ok": False,
                    "error": "Python 3 interpreter was not found",
                }

            if not config["selected_scales"]:
                return {
                    "ok": False,
                    "error": "No scales selected",
                }

            session_root = self._unique_session_root(config["output_base_dir"])
            _ensure_dir(session_root)

            job_id = uuid.uuid4().hex[:12]
            scales = [_make_scale_state(scale, os.path.join(session_root, scale)) for scale in config["selected_scales"]]

            with self._state_lock:
                self._logs.clear()
                self._stop_event.clear()
                self._state = self._build_initial_state(self._defaults)
                self._state.update({
                    "status": "running",
                    "job_id": job_id,
                    "message": "Verification job started",
                    "started_at": _now_iso(),
                    "finished_at": None,
                    "session_root": session_root,
                    "current_scale": None,
                    "current_stage": None,
                    "selected_scales": list(config["selected_scales"]),
                    "config": config,
                    "scales": scales,
                    "environment": {
                        "python27_ready": bool(config["python27_path"] and os.path.exists(config["python27_path"])),
                        "python3_ready": bool(config["python3_path"] and os.path.exists(config["python3_path"])),
                        "opensource_supported": config["opensource_supported"],
                        "opensource_reason": config["opensource_reason"],
                        "project_dir": PROJECT_DIR,
                        "base_output_dir": config["output_base_dir"],
                    },
                })
                self._set_summary_counts()

            self._worker = threading.Thread(
                target=self._run_job,
                args=(job_id, config, session_root),
                daemon=True,
            )
            self._worker.start()

            self._append_log("Verification job {} started".format(job_id))
            self._append_log("Session root: {}".format(session_root))
            self._append_log("Selected scales: {}".format(", ".join(config["selected_scales"])))
            self._append_log(
                "Runs: {} | Warmup: {} | Generate data: {} | Open-source: {} | Multiprocess: {}".format(
                    config["runs"],
                    config["warmup"],
                    "yes" if config["generate_data"] else "no",
                    "yes" if config["include_opensource"] else "no",
                    "yes" if config["multiprocess"] else "no",
                )
            )
            return {
                "ok": True,
                "job_id": job_id,
                "session_root": session_root,
            }

    def stop(self):
        self._stop_event.set()
        process = self._active_process
        if process is not None:
            try:
                process.terminate()
            except Exception:
                pass
        with self._state_lock:
            if self._state.get("status") == "running":
                self._state["message"] = "Stop requested"
        self._append_log("Stop requested")
        return {"ok": True}

    def _validate_scale(self, scale_name, scale_output_dir, include_opensource):
        issues = []
        expected_groups = ["py2", "py3"]
        if include_opensource:
            expected_groups.append("os")

        raw_results = {}
        for group in expected_groups:
            if group == "py2":
                file_path = self._find_latest_matching_file(scale_output_dir, "benchmark_results_py2")
            elif group == "py3":
                file_path = self._find_latest_matching_file(scale_output_dir, "benchmark_results_py3")
            else:
                file_path = self._find_latest_matching_file(scale_output_dir, "benchmark_results_os")
                if file_path is None:
                    file_path = self._find_latest_matching_file(scale_output_dir, "opensource")

            summary = _validate_result_payload(file_path, expected_min_count=EXPECTED_BASE_TESTS, expected_tag=group)
            if not summary.get("exists"):
                summary["status"] = "failed"
            raw_results[group] = summary
            if summary["status"] != "passed":
                issues.append("{}: {}".format(group, summary.get("error") or "validation failed"))

        artifacts = {
            "benchmark_run.log": os.path.join(scale_output_dir, getattr(settings, "BENCHMARK_RUN_LOG_NAME", "benchmark_run.log")),
            "comparison_report.md": os.path.join(scale_output_dir, "comparison_report.md"),
            "comparison_table.tex": os.path.join(scale_output_dir, "comparison_table.tex"),
            "comparison_data.csv": os.path.join(scale_output_dir, "comparison_data.csv"),
            "comparison_data.json": os.path.join(scale_output_dir, "comparison_data.json"),
        }
        artifact_summary = {}
        for name, path in artifacts.items():
            artifact_summary[name] = {
                "path": path,
                "exists": os.path.exists(path),
                "size": os.path.getsize(path) if os.path.exists(path) else 0,
            }
            if not artifact_summary[name]["exists"] or artifact_summary[name]["size"] <= 0:
                issues.append("Missing or empty artifact: {}".format(name))

        comparison_payload = {}
        comparison_path = artifacts["comparison_data.json"]
        if artifact_summary["comparison_data.json"]["exists"]:
            try:
                comparison_payload = _load_json(comparison_path)
            except Exception as exc:
                issues.append("Failed to load comparison_data.json: {}".format(exc))
                comparison_payload = {}

        if comparison_payload:
            comparison_rows = comparison_payload.get("comparison", [])
            statistics = comparison_payload.get("statistics", {})
            report_context = comparison_payload.get("report_context", {})
            if not comparison_rows:
                issues.append("comparison_data.json did not contain comparison rows")
            if not isinstance(statistics, dict) or statistics.get("total_tests", 0) <= 0:
                issues.append("comparison statistics are missing or empty")
            if str(report_context.get("data_scale", "")).lower() != str(scale_name).lower():
                issues.append("comparison report context scale mismatch")

        passed = not issues
        return {
            "status": "passed" if passed else "failed",
            "issues": issues,
            "raw_results": raw_results,
            "artifacts": artifact_summary,
            "comparison": {
                "path": comparison_path,
                "exists": artifact_summary["comparison_data.json"]["exists"],
                "payload": comparison_payload,
            },
        }

    def _run_scale(self, job_id, config, scale_state):
        scale = scale_state["scale"]
        scale_output_dir = scale_state["output_dir"]
        _ensure_dir(scale_output_dir)
        scale_state["started_at"] = _now_iso()

        with self._state_lock:
            self._state["current_scale"] = scale
            self._state["current_stage"] = "py2"

        self._append_log("Starting scale {}".format(scale))
        self._append_log("Output directory: {}".format(scale_output_dir))

        py2_stage = scale_state["stages"]["py2"]
        py3_stage = scale_state["stages"]["py3"]
        os_stage = scale_state["stages"]["os"]
        analysis_stage = scale_state["stages"]["analysis"]
        validation_stage = scale_state["stages"]["validation"]

        if self._stop_event.is_set():
            scale_state["status"] = "skipped"
            scale_state["issues"].append("Skipped before start")
            return scale_state

        py2_cmd = self._build_benchmark_command(
            config["python27_path"],
            scale,
            scale_output_dir,
            config,
            include_opensource=False,
        )
        py2_result = self._run_process(scale, "py2", py2_cmd, PROJECT_DIR)
        py2_stage.update(py2_result)

        with self._state_lock:
            self._state["current_stage"] = "py3"

        py3_include_os = bool(config["include_opensource"] and config["opensource_supported"])
        py3_cmd = self._build_benchmark_command(
            config["python3_path"],
            scale,
            scale_output_dir,
            config,
            include_opensource=py3_include_os,
        )
        py3_result = self._run_process(scale, "py3", py3_cmd, PROJECT_DIR)
        py3_stage.update(py3_result)

        if py3_include_os:
            os_stage.update({
                "status": "pending",
                "return_code": py3_result.get("return_code"),
                "duration_sec": 0.0,
                "command": "Included in py3 benchmark run",
                "output_tail": [],
                "summary": "Open-source results were generated inside the py3 stage",
                "details": {
                    "expected": True,
                },
                "started_at": py3_stage.get("started_at"),
                "finished_at": py3_stage.get("finished_at"),
            })
        else:
            os_stage.update({
                "status": "skipped",
                "summary": "Open-source stage was not requested or not available",
                "details": {
                    "expected": False,
                    "reason": config.get("opensource_reason", "not requested"),
                },
            })

        with self._state_lock:
            self._state["current_stage"] = "analysis"

        analysis_cmd = [
            config["python3_path"],
            "-u",
            ANALYZE_RESULTS_SCRIPT,
            "--results-dir",
            scale_output_dir,
            "--output-dir",
            scale_output_dir,
        ]
        analysis_result = self._run_process(scale, "analysis", analysis_cmd, PROJECT_DIR)
        analysis_stage.update(analysis_result)

        with self._state_lock:
            self._state["current_stage"] = "validation"

        validation = self._validate_scale(scale, scale_output_dir, py3_include_os)
        validation_stage.update({
            "status": validation["status"],
            "return_code": 0 if validation["status"] == "passed" else 1,
            "duration_sec": 0.0,
            "command": "artifact validation",
            "output_tail": [],
            "summary": "All artifacts validated" if validation["status"] == "passed" else "Validation failed",
            "details": validation,
            "started_at": _now_iso(),
            "finished_at": _now_iso(),
        })

        scale_state["raw_results"] = validation["raw_results"]
        scale_state["artifacts"] = validation["artifacts"]
        scale_state["issues"].extend(validation["issues"])

        if validation["raw_results"].get("py2"):
            py2_stage["details"] = validation["raw_results"]["py2"]
        if validation["raw_results"].get("py3"):
            py3_stage["details"] = validation["raw_results"]["py3"]
        if validation["raw_results"].get("os"):
            os_result = validation["raw_results"]["os"]
            os_stage.update({
                "status": os_result.get("status", "failed"),
                "return_code": 0 if os_result.get("status") == "passed" else 1,
                "duration_sec": 0.0,
                "command": "Included in py3 benchmark run",
                "output_tail": [],
                "summary": "Validated {} result(s)".format(os_result.get("count", 0)),
                "details": os_result,
                "started_at": py3_stage.get("started_at"),
                "finished_at": _now_iso(),
            })

        comparison_payload = validation["comparison"].get("payload") or {}
        if comparison_payload:
            comparison_rows = comparison_payload.get("comparison", [])
            statistics = comparison_payload.get("statistics", {})
            analysis_stage["details"] = {
                "count": len(comparison_rows),
                "statistics": statistics,
            }

        if (
            py2_stage["status"] == "passed"
            and py3_stage["status"] == "passed"
            and analysis_stage["status"] == "passed"
            and validation["status"] == "passed"
            and not self._stop_event.is_set()
        ):
            scale_state["status"] = "passed"
            self._append_log("Scale {} passed validation".format(scale))
        elif self._stop_event.is_set():
            scale_state["status"] = "stopped"
            self._append_log("Scale {} stopped".format(scale))
        else:
            scale_state["status"] = "failed"
            if py2_stage["status"] != "passed":
                scale_state["issues"].append("py2 stage failed")
            if py3_stage["status"] != "passed":
                scale_state["issues"].append("py3 stage failed")
            if analysis_stage["status"] != "passed":
                scale_state["issues"].append("analysis stage failed")
            self._append_log("Scale {} failed validation".format(scale))

        scale_state["finished_at"] = _now_iso()
        self._set_summary_counts()
        return scale_state

    def _run_job(self, job_id, config, session_root):
        all_scales = []
        try:
            for scale_state in list(self._state.get("scales", [])):
                if self._stop_event.is_set():
                    scale_state["status"] = "skipped"
                    scale_state["issues"].append("Skipped because the job was stopped")
                    all_scales.append(scale_state)
                    continue

                result = self._run_scale(job_id, config, scale_state)
                all_scales.append(result)

            with self._state_lock:
                self._state["scales"] = all_scales
                self._set_summary_counts()

                if self._stop_event.is_set():
                    self._state["status"] = "stopped"
                    self._state["message"] = "Verification job stopped"
                else:
                    if any(scale.get("status") == "failed" for scale in all_scales):
                        self._state["status"] = "failed"
                        self._state["message"] = "One or more scales failed validation"
                    else:
                        self._state["status"] = "completed"
                        self._state["message"] = "All selected scales passed validation"

                self._state["finished_at"] = _now_iso()
                self._state["current_scale"] = None
                self._state["current_stage"] = None

        except Exception as exc:
            with self._state_lock:
                self._state["status"] = "failed"
                self._state["message"] = "Scheduler crashed: {}".format(exc)
                self._state["finished_at"] = _now_iso()
            self._append_log("Scheduler crashed: {}".format(exc))
        finally:
            self._append_log("Verification job finished")
            self._active_process = None
            self._worker = None
