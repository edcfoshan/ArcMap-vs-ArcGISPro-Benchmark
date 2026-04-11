# -*- coding: utf-8 -*-
"""Download and cache small OSM sample extracts for benchmark inputs.

The project uses a local cached Geofabrik extract as a real-world input source
so the generated benchmark layers can be richer than the fully synthetic data
used previously.
"""
from __future__ import print_function, division, absolute_import

import hashlib
import io
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime

from config import settings


PRIMARY_SOURCE = {
    'slug': 'hong-kong',
    'label': 'Hong Kong',
    'url': 'https://download.geofabrik.de/asia/china/hong-kong-latest-free.shp.zip',
}

FALLBACK_SOURCE = {
    'slug': 'berlin',
    'label': 'Berlin',
    'url': 'https://download.geofabrik.de/europe/germany/berlin-latest-free.shp.zip',
}

LAYER_PATTERNS = {
    'roads': ['roads', '_free'],
    'buildings': ['buildings', '_free'],
    'landuse': ['landuse', '_free'],
    'pois': ['pois', '_free'],
    'places': ['places', '_free'],
    'natural': ['natural', '_free'],
    'water': ['water', '_free'],
    'traffic': ['traffic', '_free'],
    'transport': ['transport', '_free'],
}


def _ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path)
    return path


def _command_output(command):
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
    )
    stdout, stderr = proc.communicate()
    if sys.version_info[0] >= 3:
        if isinstance(stdout, bytes):
            stdout = stdout.decode('utf-8', 'replace')
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', 'replace')
    return proc.returncode, stdout or '', stderr or ''


def _powershell_download(url, dest_path):
    url = str(url).replace("'", "''")
    dest_path = os.path.abspath(dest_path).replace("'", "''")
    ps_command = "Invoke-WebRequest -UseBasicParsing -Uri '{}' -OutFile '{}'".format(url, dest_path)
    cmd = [
        'powershell',
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-Command',
        ps_command,
    ]
    return _command_output(cmd)


def _urllib_download(url, dest_path):
    try:
        try:
            from urllib.request import urlopen  # Python 3
        except ImportError:
            from urllib2 import urlopen  # Python 2
        response = urlopen(url)
        try:
            with io.open(dest_path, 'wb') as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
        finally:
            try:
                response.close()
            except Exception:
                pass
        return 0, '', ''
    except Exception as exc:
        return 1, '', str(exc)


def download_file(url, dest_path):
    """Download a file using PowerShell first, then stdlib fallback."""
    _ensure_dir(os.path.dirname(dest_path))
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        return dest_path

    if os.name == 'nt':
        return_code, stdout, stderr = _powershell_download(url, dest_path)
        if return_code == 0 and os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            return dest_path
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
        except Exception:
            pass

    return_code, stdout, stderr = _urllib_download(url, dest_path)
    if return_code != 0 or not os.path.exists(dest_path) or os.path.getsize(dest_path) <= 0:
        raise RuntimeError("Failed to download {}: {} {}".format(url, stdout, stderr))
    return dest_path


def extract_zip(zip_path, extract_dir):
    """Extract a zip file into a directory."""
    _ensure_dir(extract_dir)
    marker = os.path.join(extract_dir, '.extracted_ok')
    if os.path.exists(marker):
        return extract_dir

    with zipfile.ZipFile(zip_path, 'r') as archive:
        archive.extractall(extract_dir)

    with io.open(marker, 'w', encoding='utf-8') as handle:
        handle.write(u"{}\n".format(datetime.utcnow().isoformat()))

    return extract_dir


def _find_first_layer(extract_dir, keywords):
    keywords = [str(keyword).lower() for keyword in (keywords or [])]
    for dirpath, _, filenames in os.walk(extract_dir):
        for filename in filenames:
            if not filename.lower().endswith('.shp'):
                continue
            lowered = filename.lower()
            if all(keyword in lowered for keyword in keywords):
                return os.path.join(dirpath, filename)
    return None


def discover_layers(extract_dir):
    """Return a mapping of logical layer names to shapefile paths."""
    layers = {}
    for name, keywords in LAYER_PATTERNS.items():
        path = _find_first_layer(extract_dir, keywords)
        if path:
            layers[name] = path
    return layers


def _cache_signature(zip_path):
    size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
    mtime = int(os.path.getmtime(zip_path)) if os.path.exists(zip_path) else 0
    digest = hashlib.sha1(u"{}:{}".format(size, mtime).encode('utf-8')).hexdigest()[:12]
    return u"{}-{}".format(size, digest)


def ensure_osm_sample_cache(cache_root=None, preferred_source=None):
    """Ensure a cached OSM sample exists and return its metadata."""
    cache_root = cache_root or getattr(settings, 'OSM_CACHE_DIR', os.path.join(r'C:\temp\arcgis_benchmark_data', '_osm_cache'))
    _ensure_dir(cache_root)

    preferred = preferred_source or PRIMARY_SOURCE['slug']
    sources = [PRIMARY_SOURCE, FALLBACK_SOURCE]
    if preferred == FALLBACK_SOURCE['slug']:
        sources = [FALLBACK_SOURCE, PRIMARY_SOURCE]

    last_error = None
    for source in sources:
        try:
            region_dir = _ensure_dir(os.path.join(cache_root, source['slug']))
            zip_name = os.path.basename(source['url'])
            zip_path = os.path.join(region_dir, zip_name)
            extract_dir = os.path.join(region_dir, 'extracted')
            download_file(source['url'], zip_path)
            extract_zip(zip_path, extract_dir)
            layers = discover_layers(extract_dir)
            if not layers:
                raise RuntimeError("No shapefile layers were found in {}".format(extract_dir))

            return {
                'label': source['label'],
                'slug': source['slug'],
                'url': source['url'],
                'zip_path': zip_path,
                'extract_dir': extract_dir,
                'layers': layers,
                'cache_version': _cache_signature(zip_path),
                'cached_at': datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            last_error = exc

    raise RuntimeError("Unable to prepare any OSM sample cache: {}".format(last_error))


def list_cached_regions(cache_root=None):
    """Return cached region directories when present."""
    cache_root = cache_root or getattr(settings, 'OSM_CACHE_DIR', os.path.join(r'C:\temp\arcgis_benchmark_data', '_osm_cache'))
    if not os.path.isdir(cache_root):
        return []
    return sorted([name for name in os.listdir(cache_root) if os.path.isdir(os.path.join(cache_root, name))])

