# -*- coding: utf-8 -*-
"""Helpers for benchmark manifest files.

The manifest stores the generated input profile for a given benchmark run so
the execution layer, analyzer, and verification console can all read the same
OSM/source metadata without duplicating file-name assumptions.
"""
from __future__ import print_function, division, absolute_import

import io
import json
import os

from config import settings

try:
    text_type = unicode  # noqa: F821  # Python 2
except NameError:
    text_type = str


def get_manifest_path(root_dir):
    """Return the manifest path inside a root directory."""
    if not root_dir:
        raise ValueError("root_dir is required")
    if os.path.isdir(root_dir):
        return os.path.join(root_dir, getattr(settings, 'BENCHMARK_MANIFEST_NAME', 'benchmark_manifest.json'))
    return root_dir


def load_manifest(root_dir, default=None):
    """Load a manifest JSON file if it exists."""
    path = get_manifest_path(root_dir)
    if not os.path.exists(path):
        return default if default is not None else {}

    try:
        with io.open(path, 'r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except Exception:
        return default if default is not None else {}

    if isinstance(payload, dict):
        return payload
    return default if default is not None else {}


def save_manifest(root_dir, payload):
    """Write a manifest JSON file."""
    path = get_manifest_path(root_dir)
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent)

    json_text = json.dumps(payload or {}, ensure_ascii=False, indent=2, sort_keys=True)
    if not isinstance(json_text, text_type):
        if isinstance(json_text, bytes):
            json_text = json_text.decode('utf-8')
        else:
            json_text = text_type(json_text)

    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(json_text)

    return path


def manifest_summary(manifest):
    """Return a short human-readable manifest summary."""
    manifest = manifest or {}
    source = manifest.get('osm_source') or {}
    parts = []
    if source.get('label'):
        parts.append(source['label'])
    if manifest.get('source_mode'):
        parts.append(str(manifest['source_mode']))
    if manifest.get('cache_version'):
        parts.append(str(manifest['cache_version']))
    if manifest.get('generated_at'):
        parts.append(str(manifest['generated_at']))
    return ' | '.join(parts)
