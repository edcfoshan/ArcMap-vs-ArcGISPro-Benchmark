# -*- coding: utf-8 -*-
"""
High-precision timing and memory monitoring utilities
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import time
import sys
import os
import threading

# Python 2/3 compatibility
if sys.version_info[0] >= 3:
    import _thread as thread
else:
    import thread

class Timer(object):
    """
    High-precision timer with context manager support
    """
    def __init__(self, name="Timer"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.elapsed = None
        self._perf_counter = time.perf_counter if hasattr(time, 'perf_counter') else time.clock
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def start(self):
        """Start the timer"""
        self.start_time = self._perf_counter()
        self.end_time = None
        self.elapsed = None
    
    def stop(self):
        """Stop the timer and return elapsed time"""
        self.end_time = self._perf_counter()
        self.elapsed = self.end_time - self.start_time
        return self.elapsed
    
    def get_elapsed(self):
        """Get elapsed time without stopping"""
        if self.start_time is None:
            return 0
        if self.end_time is not None:
            return self.elapsed
        return self._perf_counter() - self.start_time
    
    def __str__(self):
        if self.elapsed is not None:
            return "{}: {:.4f}s".format(self.name, self.elapsed)
        return "{}: running...".format(self.name)
    
    def __repr__(self):
        return self.__str__()


class MemoryMonitor(object):
    """
    Memory usage monitor for Windows
    Uses Windows API via ctypes to get process memory info
    """
    def __init__(self, interval=0.5):
        self.interval = interval
        self.peak_memory_mb = 0
        self.samples = []
        self._monitoring = False
        self._thread = None
        self._pid = os.getpid()
    
    def _get_memory_usage(self):
        """Get current memory usage in MB (Windows only)"""
        try:
            import ctypes
            from ctypes import wintypes
            
            class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
                _fields_ = [
                    ('cb', wintypes.DWORD),
                    ('PageFaultCount', wintypes.DWORD),
                    ('PeakWorkingSetSize', ctypes.c_size_t),
                    ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t),
                    ('PeakPagefileUsage', ctypes.c_size_t),
                    ('PrivateUsage', ctypes.c_size_t),
                ]
            
            GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
            GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
            
            counters = PROCESS_MEMORY_COUNTERS_EX()
            counters.cb = ctypes.sizeof(counters)
            
            process = GetCurrentProcess()
            if GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
                # WorkingSetSize is in bytes, convert to MB
                return counters.WorkingSetSize / (1024 * 1024)
        except Exception:
            pass
        return 0
    
    def _monitor(self):
        """Monitor memory in background thread"""
        while self._monitoring:
            try:
                mem = self._get_memory_usage()
                if mem > 0:
                    self.samples.append(mem)
                    if mem > self.peak_memory_mb:
                        self.peak_memory_mb = mem
            except Exception:
                pass
            time.sleep(self.interval)
    
    def start(self):
        """Start memory monitoring"""
        self._monitoring = True
        self.samples = []
        self.peak_memory_mb = self._get_memory_usage()
        self.samples.append(self.peak_memory_mb)
        try:
            self._thread = threading.Thread(target=self._monitor)
            self._thread.daemon = True
            self._thread.start()
        except Exception:
            pass
    
    def stop(self):
        """Stop memory monitoring"""
        self._monitoring = False
        if self._thread:
            try:
                self._thread.join(timeout=1.0)
            except Exception:
                pass
    
    def get_average(self):
        """Get average memory usage"""
        if not self.samples:
            return 0
        return sum(self.samples) / len(self.samples)
    
    def get_stats(self):
        """Get memory statistics"""
        if not self.samples:
            return {
                'peak_mb': 0,
                'average_mb': 0,
                'min_mb': 0,
                'max_mb': 0,
                'samples': 0
            }
        return {
            'peak_mb': self.peak_memory_mb,
            'average_mb': self.get_average(),
            'min_mb': min(self.samples),
            'max_mb': max(self.samples),
            'samples': len(self.samples)
        }


class BenchmarkTimer(object):
    """
    Combined timer and memory monitor for benchmarks
    """
    def __init__(self, name="Benchmark", monitor_memory=True):
        self.name = name
        self.timer = Timer(name)
        self.memory_monitor = MemoryMonitor() if monitor_memory else None
        self.results = {}
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
    
    def start(self):
        """Start timing and memory monitoring"""
        if self.memory_monitor:
            self.memory_monitor.start()
        self.timer.start()
    
    def stop(self):
        """Stop and collect results"""
        elapsed = self.timer.stop()
        if self.memory_monitor:
            self.memory_monitor.stop()
        
        self.results = {
            'name': self.name,
            'elapsed_seconds': elapsed,
            'elapsed_formatted': self._format_time(elapsed),
        }
        
        if self.memory_monitor:
            mem_stats = self.memory_monitor.get_stats()
            self.results['memory_mb'] = mem_stats
        
        return self.results
    
    def _format_time(self, seconds):
        """Format time in human-readable format"""
        if seconds < 0.001:
            return "{:.4f} ms".format(seconds * 1000)
        elif seconds < 1:
            return "{:.4f} s".format(seconds)
        elif seconds < 60:
            return "{:.2f} s".format(seconds)
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return "{} min {:.2f} s".format(minutes, secs)
    
    def get_results(self):
        """Get benchmark results"""
        if not self.results:
            self.stop()
        return self.results


def benchmark(func, *args, **kwargs):
    """
    Decorator/function to benchmark a function call
    Usage:
        @benchmark
        def my_function():
            pass
        
        # Or
        result = benchmark(my_function, arg1, arg2)
    """
    name = func.__name__ if hasattr(func, '__name__') else str(func)
    with BenchmarkTimer(name=name) as bt:
        result = func(*args, **kwargs)
    return result, bt.get_results()


if __name__ == '__main__':
    # Test the timer
    print("Testing Timer...")
    with Timer("Test Timer") as t:
        time.sleep(0.1)
    print(t)
    
    # Test memory monitor
    print("\nTesting Memory Monitor...")
    mm = MemoryMonitor(interval=0.1)
    mm.start()
    time.sleep(0.5)
    mm.stop()
    print("Peak Memory: {:.2f} MB".format(mm.peak_memory_mb))
    print("Average Memory: {:.2f} MB".format(mm.get_average()))
