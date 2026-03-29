# -*- coding: utf-8 -*-
"""
ArcGIS Environment Detection and Configuration
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import sys
import os
import subprocess

class ArcGISEnvironment(object):
    """
    Detect and configure ArcGIS environment
    """
    def __init__(self):
        self.python_version = sys.version_info
        self.is_python2 = self.python_version[0] == 2
        self.is_python3 = self.python_version[0] == 3
        self.arcpy_available = False
        self.arcgis_product = None
        self.arcgis_version = None
        self.license_level = None
        self.spatial_reference = None
        self._check_arcpy()
    
    def _check_arcpy(self):
        """Check if arcpy is available and get version info"""
        try:
            import arcpy
            self.arcpy_available = True
            
            # Get ArcGIS product info
            try:
                self.arcgis_product = arcpy.GetInstallInfo()['ProductName']
                self.arcgis_version = arcpy.GetInstallInfo()['Version']
            except Exception:
                pass
            
            # Check license level
            try:
                self.license_level = arcpy.CheckProduct("ArcInfo")
            except Exception:
                try:
                    self.license_level = arcpy.ProductInfo()
                except Exception:
                    pass
            
            # Set spatial reference
            try:
                self.spatial_reference = arcpy.SpatialReference(4326)
            except Exception:
                pass
                
        except ImportError:
            self.arcpy_available = False
    
    def get_info(self):
        """Get environment information dictionary"""
        return {
            'python_version': "{}.{}.{}".format(
                self.python_version[0],
                self.python_version[1],
                self.python_version[2]
            ),
            'python_executable': sys.executable,
            'is_python2': self.is_python2,
            'is_python3': self.is_python3,
            'arcpy_available': self.arcpy_available,
            'arcgis_product': self.arcgis_product,
            'arcgis_version': self.arcgis_version,
            'license_level': self.license_level,
            'platform': sys.platform,
        }
    
    def print_info(self):
        """Print environment information"""
        print("=" * 60)
        print("ArcGIS Environment Information")
        print("=" * 60)
        info = self.get_info()
        for key, value in sorted(info.items()):
            print("  {}: {}".format(key, value))
        print("=" * 60)
    
    def setup_workspace(self, workspace_path):
        """Setup ArcGIS workspace"""
        if not self.arcpy_available:
            raise RuntimeError("arcpy is not available")
        
        import arcpy
        
        # Set workspace
        arcpy.env.workspace = workspace_path
        arcpy.env.scratchWorkspace = workspace_path
        
        # Set overwrite output
        arcpy.env.overwriteOutput = True
        
        # Set parallel processing
        try:
            arcpy.env.parallelProcessingFactor = "100%"
        except Exception:
            pass
        
        return True
    
    def check_license(self, product='ArcInfo'):
        """Check if license is available"""
        if not self.arcpy_available:
            return False
        
        import arcpy
        
        try:
            result = arcpy.CheckProduct(product)
            return result in ['AlreadyInitialized', 'Available']
        except Exception:
            return False
    
    @staticmethod
    def create_file_gdb(path, name):
        """Create a file geodatabase"""
        import arcpy
        
        gdb_path = os.path.join(path, name)
        
        # Delete if exists
        if arcpy.Exists(gdb_path):
            try:
                arcpy.Delete_management(gdb_path)
            except Exception:
                pass
        
        # Create new
        try:
            arcpy.CreateFileGDB_management(path, name)
            return gdb_path
        except Exception as e:
            raise RuntimeError("Failed to create FileGDB: {}".format(str(e)))
    
    def get_spatial_reference(self, wkid=4326):
        """Get spatial reference object"""
        if not self.arcpy_available:
            return None
        
        import arcpy
        return arcpy.SpatialReference(wkid)


def detect_arcgis_installations():
    """
    Detect ArcGIS installations on the system
    Returns list of detected Python interpreters
    """
    installations = []
    
    # Common ArcGIS Python paths
    possible_paths = [
        # ArcGIS Desktop (Python 2.7)
        r"C:\Python27\ArcGIS10.8\python.exe",
        r"C:\Python27\ArcGIS10.7\python.exe",
        r"C:\Python27\ArcGIS10.6\python.exe",
        r"C:\Python27\ArcGIS10.5\python.exe",
        r"C:\Python27\ArcGIS10.4\python.exe",
        r"C:\Python27\ArcGIS10.3\python.exe",
        r"C:\Python27\ArcGIS10.2\python.exe",
        
        # ArcGIS Pro (Python 3)
        r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe",
        r"C:\Program Files\ArcGIS\Pro\bin\Python\python.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                # Run python to get version
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version = result.stdout.strip() if result.returncode == 0 else "Unknown"
                
                installations.append({
                    'path': path,
                    'version': version,
                    'type': 'ArcGIS Pro' if 'Pro' in path else 'ArcGIS Desktop'
                })
            except Exception:
                pass
    
    return installations


if __name__ == '__main__':
    # Test environment detection
    env = ArcGISEnvironment()
    env.print_info()
    
    print("\nDetected Installations:")
    for inst in detect_arcgis_installations():
        print("  {}: {} ({})".format(inst['type'], inst['path'], inst['version']))
