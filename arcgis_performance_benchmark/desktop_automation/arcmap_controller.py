# -*- coding: utf-8 -*-
"""
ArcMap Automation Controller
尝试自动化控制 ArcMap 执行 Python 脚本
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import time
import subprocess
import tempfile

# Configuration
ARCGIS_PATH = r"C:\Program Files (x86)\ArcGIS\Desktop10.8\bin\ArcMap.exe"
PYTHON_SCRIPT_TEMPLATE = '''
import arcpy
import time
import json
import sys

# Add project path
sys.path.insert(0, r"{project_path}")

from benchmarks.vector_benchmarks import VectorBenchmarks
from benchmarks.raster_benchmarks import RasterBenchmarks
from benchmarks.mixed_benchmarks import MixedBenchmarks
from config import settings

results = []

# Run vector benchmarks
print("=" * 60)
print("Running benchmarks in ArcMap Python Window")
print("=" * 60)

benchmarks = VectorBenchmarks.get_all_benchmarks()
for bm in benchmarks:
    print("\\nRunning: {}".format(bm.name))
    try:
        bm.setup()
        start = time.time()
        bm.run_single()
        elapsed = time.time() - start
        bm.teardown()
        
        results.append({{
            'test_name': bm.name,
            'elapsed': elapsed,
            'success': True
        }})
        print("  Success: {:.4f}s".format(elapsed))
    except Exception as e:
        results.append({{
            'test_name': bm.name,
            'error': str(e),
            'success': False
        }})
        print("  Failed: {}".format(e))

# Save results
output_file = r"{output_file}"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print("\\nResults saved to: {}".format(output_file))
print("You can close ArcMap now.")
'''


class ArcMapController(object):
    """Control ArcMap to run Python scripts"""
    
    def __init__(self):
        self.arcmap_process = None
        self.script_file = None
        
    def is_arcmap_installed(self):
        """Check if ArcMap is installed"""
        return os.path.exists(ARCGIS_PATH)
    
    def create_script_file(self, output_path):
        """Create temporary Python script"""
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        script_content = PYTHON_SCRIPT_TEMPLATE.format(
            project_path=project_path,
            output_file=output_path
        )
        
        # Create temp file
        fd, script_path = tempfile.mkstemp(suffix='.py', prefix='arcmap_test_')
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        
        self.script_file = script_path
        return script_path
    
    def launch_arcmap(self):
        """Launch ArcMap"""
        print("Launching ArcMap...")
        try:
            self.arcmap_process = subprocess.Popen(
                [ARCGIS_PATH],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("ArcMap launched, waiting for startup...")
            time.sleep(10)  # Wait for ArcMap to start
            return True
        except Exception as e:
            print("Failed to launch ArcMap: {}".format(e))
            return False
    
    def execute_in_arcmap(self, script_path):
        """
        Execute script in ArcMap
        
        Note: This is the challenging part. ArcMap doesn't provide
        a direct API to execute Python scripts in its Python window.
        
        Possible approaches:
        1. Use pywinauto to simulate UI interactions
        2. Use a Toolbox script
        3. Use Add-in
        4. Manual execution (most reliable)
        """
        print("=" * 70)
        print("IMPORTANT: Automatic execution in ArcMap is limited")
        print("=" * 70)
        print("")
        print("Due to ArcMap's architecture, fully automated Python execution")
        print("in the Python window is not reliably possible.")
        print("")
        print("Please follow these manual steps:")
        print("")
        print("1. Wait for ArcMap to fully start")
        print("2. Open the Python window (Geoprocessing > Python)")
        print("3. Open this script file: {}".format(script_path))
        print("4. Copy the code and paste into ArcMap Python window")
        print("5. Press Enter to execute")
        print("6. Wait for completion message")
        print("")
        print("Script file location: {}".format(script_path))
        print("")
        
        # Keep the script file for manual use
        return False
    
    def run_benchmarks(self, output_path):
        """Main method to run benchmarks in ArcMap"""
        print("=" * 70)
        print("ArcMap Benchmark Automation")
        print("=" * 70)
        
        if not self.is_arcmap_installed():
            print("Error: ArcMap not found at {}".format(ARCGIS_PATH))
            return False
        
        # Create script file
        script_path = self.create_script_file(output_path)
        print("Created script: {}".format(script_path))
        
        # Launch ArcMap
        if not self.launch_arcmap():
            return False
        
        # Try to execute
        result = self.execute_in_arcmap(script_path)
        
        return result
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.script_file and os.path.exists(self.script_file):
            try:
                os.remove(self.script_file)
            except:
                pass


def main():
    """Main function"""
    controller = ArcMapController()
    
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "results", "raw", "benchmark_results_arcmap.json"
    )
    
    try:
        controller.run_benchmarks(output_path)
        print("\\nYou can now execute the script manually in ArcMap.")
        print("Results will be saved to: {}".format(output_path))
        input("\\nPress Enter when done...")
    finally:
        controller.cleanup()


if __name__ == '__main__':
    main()
