# -*- coding: utf-8 -*-
"""
ArcGIS cleanup helpers for workspace cache and file-based dataset artifacts.
Compatible with Python 2.7 and 3.x
"""
from __future__ import print_function, division, absolute_import
import os
import shutil
import time

try:
    import arcpy
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False
    arcpy = None


def clear_workspace_cache(workspace=None):
    """Release ArcPy workspace locks and optionally reset the active workspace."""
    if not HAS_ARCPY:
        return

    try:
        arcpy.ClearWorkspaceCache_management()
    except Exception:
        pass

    if workspace is not None:
        try:
            arcpy.env.workspace = workspace
        except Exception:
            pass
        try:
            arcpy.env.scratchWorkspace = workspace
        except Exception:
            pass
    else:
        try:
            arcpy.env.workspace = None
        except Exception:
            pass
        try:
            arcpy.env.scratchWorkspace = None
        except Exception:
            pass


def _delete_file(path):
    """Delete a single file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def remove_dataset_artifacts(path, retries=3, sleep_seconds=0.5):
    """Remove a dataset and common file-based sidecar artifacts."""
    if not path:
        return

    candidates = [path]
    base, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext == '.shp':
        candidates.extend([
            base + '.shx',
            base + '.dbf',
            base + '.prj',
            base + '.cpg',
            base + '.sbn',
            base + '.sbx',
            base + '.xml',
            base + '.fix',
            path + '.xml',
        ])
    elif ext in ('.tif', '.tiff', '.img', '.jpg', '.jpeg'):
        candidates.extend([
            path + '.aux.xml',
            base + '.aux.xml',
            path + '.ovr',
            base + '.ovr',
            path + '.xml',
            base + '.xml',
            path + '.tfw',
            base + '.tfw',
            path + '.cpg',
            base + '.cpg',
        ])
    elif ext == '.gdb' and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
        return

    for attempt in range(max(1, int(retries))):
        clear_workspace_cache()

        if HAS_ARCPY:
            try:
                if arcpy.Exists(path):
                    arcpy.Delete_management(path)
            except Exception:
                pass

        for candidate in candidates:
            if candidate == path and os.path.isdir(candidate):
                shutil.rmtree(candidate, ignore_errors=True)
                continue
            _delete_file(candidate)

        if not os.path.exists(path) and not (HAS_ARCPY and arcpy.Exists(path)):
            break

        if attempt < int(retries) - 1:
            time.sleep(float(sleep_seconds))
