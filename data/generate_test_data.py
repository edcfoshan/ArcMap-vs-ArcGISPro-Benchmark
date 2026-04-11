# -*- coding: utf-8 -*-
"""
Generate benchmark input data for ArcGIS performance tests.

The generator now prefers a cached OSM sample extract, converts the selected
layers into a file geodatabase, and then derives the benchmark-ready feature
classes and rasters from that local cache. If OSM preparation fails, it falls
back to deterministic synthetic data so the benchmark can still run.
"""
from __future__ import print_function, division, absolute_import

import copy
import os
import random
import sys
from datetime import datetime

from config import settings
from utils.benchmark_manifest import load_manifest, save_manifest
from utils.benchmark_shapes import factor_grid_dimensions, derive_block_size, build_block_pattern_array
from utils.gis_cleanup import clear_workspace_cache, remove_dataset_artifacts
from utils.osm_samples import ensure_osm_sample_cache
from utils.raster_utils import create_constant_raster, create_block_pattern_raster

try:
    import arcpy
    HAS_ARCPY = True
except ImportError:
    HAS_ARCPY = False
    arcpy = None


MANIFEST_VERSION = 2
PROJECTED_WKID = 3857
COMMON_ID_FIELDS = [
    ('poly_id', 'LONG'),
    ('group_id', 'LONG'),
    ('class_id', 'LONG'),
    ('priority', 'LONG'),
    ('weight', 'DOUBLE'),
    ('source_tag', 'TEXT', 64),
    ('osm_source', 'TEXT', 64),
]

OSM_LAYER_TARGETS = [
    ('roads', 'osm_roads'),
    ('buildings', 'osm_buildings'),
    ('landuse', 'osm_landuse'),
    ('pois', 'osm_pois'),
    ('places', 'osm_places'),
]


def _ensure_dir(path):
    if path and not os.path.exists(path):
        os.makedirs(path)
    return path


def _safe_text(value):
    if value is None:
        return u""
    try:
        if isinstance(value, bytes):
            return value.decode('utf-8', 'replace')
    except Exception:
        pass
    return unicode(value) if hasattr(__builtins__, 'unicode') else str(value)


def _delete_path(path):
    if not path:
        return
    try:
        remove_dataset_artifacts(path)
    except Exception:
        pass
    try:
        if os.path.isdir(path):
            import shutil
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _extent_values(extent):
    if extent is None:
        return None
    try:
        return (
            float(extent.XMin),
            float(extent.YMin),
            float(extent.XMax),
            float(extent.YMax),
        )
    except Exception:
        pass
    if isinstance(extent, (list, tuple)) and len(extent) >= 4:
        return float(extent[0]), float(extent[1]), float(extent[2]), float(extent[3])
    return None


def _extent_dict(extent):
    values = _extent_values(extent)
    if not values:
        return {}
    xmin, ymin, xmax, ymax = values
    return {
        'xmin': xmin,
        'ymin': ymin,
        'xmax': xmax,
        'ymax': ymax,
    }


def _square_extent_from_extents(extents, margin_ratio=0.05, default_side=1000000.0):
    """Return a square extent that covers the supplied extents."""
    x_mins = []
    y_mins = []
    x_maxs = []
    y_maxs = []
    for extent in extents or []:
        values = _extent_values(extent)
        if not values:
            continue
        xmin, ymin, xmax, ymax = values
        x_mins.append(xmin)
        y_mins.append(ymin)
        x_maxs.append(xmax)
        y_maxs.append(ymax)

    if not x_mins:
        half = float(default_side) / 2.0
        return -half, -half, half, half

    xmin = min(x_mins)
    ymin = min(y_mins)
    xmax = max(x_maxs)
    ymax = max(y_maxs)
    width = xmax - xmin
    height = ymax - ymin
    side = max(width, height)
    side = side * (1.0 + float(margin_ratio) * 2.0)
    if side <= 0:
        side = float(default_side)

    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    half = side / 2.0
    return cx - half, cy - half, cx + half, cy + half


def _feature_count(path):
    if not HAS_ARCPY or not path or not arcpy.Exists(path):
        return 0
    try:
        return int(arcpy.GetCount_management(path)[0])
    except Exception:
        return 0


def _raster_size(path):
    if not HAS_ARCPY or not path:
        return None
    if not arcpy.Exists(path) and not os.path.exists(path):
        return None
    try:
        desc = arcpy.Describe(path)
        return int(getattr(desc, 'width', 0) or 0), int(getattr(desc, 'height', 0) or 0)
    except Exception:
        if os.path.exists(path):
            try:
                desc = arcpy.Describe(path)
                return int(getattr(desc, 'width', 0) or 0), int(getattr(desc, 'height', 0) or 0)
            except Exception:
                pass
        return None


def _projected_spatial_reference():
    try:
        return arcpy.SpatialReference(PROJECTED_WKID)
    except Exception:
        return arcpy.SpatialReference(getattr(settings, 'SPATIAL_REFERENCE', 4326))


def _create_feature_class(output_fc, geometry_type, spatial_reference):
    _delete_path(output_fc)
    arcpy.CreateFeatureclass_management(
        out_path=os.path.dirname(output_fc),
        out_name=os.path.basename(output_fc),
        geometry_type=geometry_type,
        spatial_reference=spatial_reference
    )
    return output_fc


def _add_common_fields(feature_class):
    existing = {field.name.lower() for field in arcpy.ListFields(feature_class)}
    for field_spec in COMMON_ID_FIELDS:
        name = field_spec[0]
        if name.lower() in existing:
            continue
        field_type = field_spec[1]
        length = field_spec[2] if len(field_spec) > 2 else None
        if field_type == 'TEXT':
            arcpy.AddField_management(feature_class, name, field_type, field_length=length or 64)
        else:
            arcpy.AddField_management(feature_class, name, field_type)


def _populate_common_fields(feature_class, source_tag, osm_source, field_name='poly_id'):
    fields = [field_name, 'group_id', 'class_id', 'priority', 'weight', 'source_tag', 'osm_source']
    with arcpy.da.UpdateCursor(feature_class, fields) as cursor:
        for index, row in enumerate(cursor, start=1):
            row[0] = index
            row[1] = ((index - 1) % 64) + 1
            row[2] = ((index - 1) % 11) + 1
            row[3] = ((index - 1) % 7) + 1
            row[4] = round((((index - 1) % 100) + 1) / 100.0, 4)
            row[5] = source_tag
            row[6] = osm_source
            cursor.updateRow(row)


def _project_source_layer(source_path, output_fc, spatial_reference):
    if not source_path or not os.path.exists(source_path):
        raise RuntimeError("Missing source shapefile: {}".format(source_path))
    _delete_path(output_fc)
    arcpy.Project_management(source_path, output_fc, spatial_reference)
    return output_fc


def _collect_extents(feature_classes):
    extents = []
    for fc in feature_classes or []:
        if not fc or not arcpy.Exists(fc):
            continue
        try:
            desc = arcpy.Describe(fc)
            extents.append(desc.extent)
        except Exception:
            pass
    return extents


def _create_boundary(feature_class, extent, source_mode, source_label):
    _create_feature_class(feature_class, 'POLYGON', _projected_spatial_reference())
    _add_common_fields(feature_class)
    array = arcpy.Array([
        arcpy.Point(extent[0], extent[1]),
        arcpy.Point(extent[0], extent[3]),
        arcpy.Point(extent[2], extent[3]),
        arcpy.Point(extent[2], extent[1]),
        arcpy.Point(extent[0], extent[1]),
    ])
    polygon = arcpy.Polygon(array, _projected_spatial_reference())
    with arcpy.da.InsertCursor(feature_class, ['SHAPE@', 'poly_id', 'group_id', 'class_id', 'priority', 'weight', 'source_tag', 'osm_source']) as cursor:
        cursor.insertRow([polygon, 1, 1, 1, 1, 1.0, source_mode, source_label])
    return feature_class


def _create_fishnet(feature_class, extent, rows, cols, source_mode, source_label, offset=False):
    _delete_path(feature_class)
    spatial_reference = _projected_spatial_reference()
    xmin, ymin, xmax, ymax = extent
    width = float(xmax - xmin)
    height = float(ymax - ymin)
    cell_width = width / float(cols)
    cell_height = height / float(rows)
    if offset:
        xmin = xmin + (cell_width / 2.0)
        ymin = ymin + (cell_height / 2.0)
        xmax = xmax + (cell_width / 2.0)
        ymax = ymax + (cell_height / 2.0)
    arcpy.CreateFishnet_management(
        out_feature_class=feature_class,
        origin_coord="{} {}".format(xmin, ymin),
        y_axis_coord="{} {}".format(xmin, ymin + 10.0),
        cell_width=cell_width,
        cell_height=cell_height,
        number_rows=rows,
        number_columns=cols,
        corner_coord="{} {}".format(xmax, ymax),
        labels="NO_LABELS",
        template="",
        geometry_type="POLYGON"
    )
    try:
        arcpy.DefineProjection_management(feature_class, spatial_reference)
    except Exception:
        pass
    _add_common_fields(feature_class)
    _populate_common_fields(feature_class, source_mode, source_label)
    return feature_class


def _point_geometry_from_source(geometry):
    if geometry is None:
        return None
    try:
        if geometry.type.lower() == 'point':
            first_point = geometry.firstPoint
            if first_point is not None:
                return arcpy.Point(first_point.X, first_point.Y)
            centroid = geometry.centroid
            return arcpy.Point(centroid.X, centroid.Y) if centroid else None
        centroid = geometry.centroid
        return arcpy.Point(centroid.X, centroid.Y) if centroid else None
    except Exception:
        try:
            point = geometry.labelPoint
            return arcpy.Point(point.X, point.Y) if point else None
        except Exception:
            return None


def _jitter_point(point, index, extent, magnitude):
    if point is None:
        return None
    xmin, ymin, xmax, ymax = extent
    dx = ((index % 13) - 6) * magnitude
    dy = (((index // 13) % 13) - 6) * magnitude
    x = min(max(point.X + dx, xmin + 1.0), xmax - 1.0)
    y = min(max(point.Y + dy, ymin + 1.0), ymax - 1.0)
    return arcpy.Point(x, y)


def _create_point_sample(feature_class, source_geometries, target_count, extent, source_mode, source_label, jitter_meters=50.0):
    _delete_path(feature_class)
    spatial_reference = _projected_spatial_reference()
    _create_feature_class(feature_class, 'POINT', spatial_reference)
    _add_common_fields(feature_class)

    geometries = []
    for geom in source_geometries or []:
        point = _point_geometry_from_source(geom)
        if point is not None:
            geometries.append(point)

    if not geometries:
        geometries = [None]

    xmin, ymin, xmax, ymax = extent
    rng = random.Random(42 + int(target_count))

    with arcpy.da.InsertCursor(feature_class, ['SHAPE@', 'poly_id', 'group_id', 'class_id', 'priority', 'weight', 'source_tag', 'osm_source']) as cursor:
        for index in range(1, int(target_count) + 1):
            source_point = geometries[(index - 1) % len(geometries)]
            if source_point is None:
                x = rng.uniform(xmin + 1.0, xmax - 1.0)
                y = rng.uniform(ymin + 1.0, ymax - 1.0)
                point = arcpy.Point(x, y)
            else:
                point = _jitter_point(source_point, index, extent, jitter_meters) or source_point
            cursor.insertRow([
                arcpy.PointGeometry(point, spatial_reference),
                index,
                ((index - 1) % 64) + 1,
                ((index - 1) % 11) + 1,
                ((index - 1) % 7) + 1,
                round((((index - 1) % 100) + 1) / 100.0, 4),
                source_mode,
                source_label
            ])
    return feature_class


def _create_polygon_sample(feature_class, source_geometries, target_count, extent, source_mode, source_label):
    _delete_path(feature_class)
    spatial_reference = _projected_spatial_reference()
    _create_feature_class(feature_class, 'POLYGON', spatial_reference)
    _add_common_fields(feature_class)

    geometries = []
    for geom in source_geometries or []:
        if geom is not None:
            geometries.append(geom)

    if not geometries:
        geometries = [None]

    xmin, ymin, xmax, ymax = extent
    size = max(25.0, min(xmax - xmin, ymax - ymin) / 250.0)
    rng = random.Random(1729 + int(target_count))

    with arcpy.da.InsertCursor(feature_class, ['SHAPE@', 'poly_id', 'group_id', 'class_id', 'priority', 'weight', 'source_tag', 'osm_source']) as cursor:
        for index in range(1, int(target_count) + 1):
            source_geom = geometries[(index - 1) % len(geometries)]
            if source_geom is None:
                x = rng.uniform(xmin + size, xmax - size)
                y = rng.uniform(ymin + size, ymax - size)
                array = arcpy.Array([
                    arcpy.Point(x - size, y - size),
                    arcpy.Point(x - size, y + size),
                    arcpy.Point(x + size, y + size),
                    arcpy.Point(x + size, y - size),
                    arcpy.Point(x - size, y - size),
                ])
                geometry = arcpy.Polygon(array, spatial_reference)
            else:
                geometry = source_geom
            cursor.insertRow([
                geometry,
                index,
                ((index - 1) % 64) + 1,
                ((index - 1) % 11) + 1,
                ((index - 1) % 7) + 1,
                round((((index - 1) % 100) + 1) / 100.0, 4),
                source_mode,
                source_label
            ])
    return feature_class


def _create_random_points(feature_class, target_count, extent, source_mode, source_label):
    _delete_path(feature_class)
    spatial_reference = _projected_spatial_reference()
    _create_feature_class(feature_class, 'POINT', spatial_reference)
    _add_common_fields(feature_class)

    xmin, ymin, xmax, ymax = extent
    rng = random.Random(31415 + int(target_count))
    with arcpy.da.InsertCursor(feature_class, ['SHAPE@', 'poly_id', 'group_id', 'class_id', 'priority', 'weight', 'source_tag', 'osm_source']) as cursor:
        for index in range(1, int(target_count) + 1):
            x = rng.uniform(xmin + 1.0, xmax - 1.0)
            y = rng.uniform(ymin + 1.0, ymax - 1.0)
            cursor.insertRow([
                arcpy.PointGeometry(arcpy.Point(x, y), spatial_reference),
                index,
                ((index - 1) % 64) + 1,
                ((index - 1) % 11) + 1,
                ((index - 1) % 7) + 1,
                round((((index - 1) % 100) + 1) / 100.0, 4),
                source_mode,
                source_label
            ])
    return feature_class


def _create_rasters(root_dir, extent, source_mode, source_label, raster_config):
    """Create the baseline and analysis rasters."""
    side_extent = extent
    sr = _projected_spatial_reference()
    constant_size = int(raster_config['constant_raster_size'])
    analysis_size = int(raster_config['analysis_raster_size'])
    constant_path = os.path.join(root_dir, "constant_raster.tif")
    analysis_path = os.path.join(root_dir, "analysis_raster.tif")

    if not side_extent:
        half = float(max(constant_size, analysis_size) * 1000.0) / 2.0
        side_extent = (-half, -half, half, half)

    create_constant_raster(
        constant_path,
        cell_size=max(1.0, float(side_extent[2] - side_extent[0]) / float(constant_size)),
        extent=side_extent,
        value=1,
        spatial_reference=sr,
        use_spatial_analyst=False
    )

    block_size = derive_block_size(analysis_size, target_blocks_per_side=60, min_block_size=8)
    create_block_pattern_raster(
        analysis_path,
        cell_size=max(1.0, float(side_extent[2] - side_extent[0]) / float(analysis_size)),
        extent=side_extent,
        block_size=block_size,
        levels=8,
        spatial_reference=sr
    )

    return constant_path, analysis_path, block_size


def _load_geometry_samples(feature_class, limit=None):
    geometries = []
    if not feature_class or not arcpy.Exists(feature_class):
        return geometries
    fields = ['SHAPE@']
    with arcpy.da.SearchCursor(feature_class, fields) as cursor:
        for index, row in enumerate(cursor):
            if limit is not None and index >= int(limit):
                break
            if row and row[0] is not None:
                geometries.append(row[0])
    return geometries


class TestDataGenerator(object):
    """Generate benchmark input data and cache metadata."""

    def __init__(self):
        self.scale = settings.DATA_SCALE
        self.vector_config = copy.deepcopy(settings.VECTOR_CONFIG)
        self.raster_config = copy.deepcopy(settings.RASTER_CONFIG)
        if str(self.scale).lower() == 'standard':
            # standard 允许按测试项覆盖输入规模，这里把覆盖后的关键字段映射回
            # 实际生成的输入图层，以便生成/复用校验保持一致。
            v3 = settings.get_vector_config_for_test('V3')
            v4 = settings.get_vector_config_for_test('V4')
            v5 = settings.get_vector_config_for_test('V5')
            v6 = settings.get_vector_config_for_test('V6')
            self.vector_config['buffer_points'] = int(v3.get('buffer_points', self.vector_config.get('buffer_points', 0)))
            self.vector_config['intersect_features_a'] = int(v4.get('intersect_features_a', self.vector_config.get('intersect_features_a', 0)))
            self.vector_config['intersect_features_b'] = int(v4.get('intersect_features_b', self.vector_config.get('intersect_features_b', 0)))
            self.vector_config['spatial_join_points'] = int(v5.get('spatial_join_points', self.vector_config.get('spatial_join_points', 0)))
            self.vector_config['spatial_join_polygons'] = int(v5.get('spatial_join_polygons', self.vector_config.get('spatial_join_polygons', 0)))
            self.vector_config['calculate_field_records'] = int(v6.get('calculate_field_records', self.vector_config.get('calculate_field_records', 0)))

            # analysis_raster.tif 主要供混合项与回退逻辑使用，按 M2 口径对齐。
            m2 = settings.get_raster_config_for_test('M2')
            if isinstance(m2, dict) and m2:
                self.raster_config['analysis_raster_size'] = int(m2.get('analysis_raster_size', self.raster_config.get('analysis_raster_size', 0)))
        self.root_dir = os.path.abspath(settings.DATA_DIR)
        self.gdb_name = getattr(settings, 'DEFAULT_GDB_NAME', 'benchmark_data.gdb')
        self.gdb_path = os.path.join(self.root_dir, self.gdb_name)
        self.manifest_path = os.path.join(self.root_dir, getattr(settings, 'BENCHMARK_MANIFEST_NAME', 'benchmark_manifest.json'))

    def _required_paths(self):
        return [
            self.gdb_path,
            os.path.join(self.gdb_path, 'analysis_boundary'),
            os.path.join(self.root_dir, 'constant_raster.tif'),
            os.path.join(self.root_dir, 'analysis_raster.tif'),
        ]

    def _generated_dataset_paths(self):
        names = [
            'analysis_boundary',
            'buffer_points',
            'spatial_join_points',
            'spatial_join_polygons',
            'calculate_field_fc',
            'test_polygons_a',
            'test_polygons_b',
            'osm_roads',
            'osm_buildings',
            'osm_landuse',
            'osm_pois',
            'osm_places',
        ]
        return [os.path.join(self.gdb_path, name) for name in names]

    def _validate_existing_assets(self, manifest):
        if not manifest or not isinstance(manifest, dict):
            return False
        if str(manifest.get('schema_version')) != str(MANIFEST_VERSION):
            return False
        if str(manifest.get('scale', '')).lower() != str(self.scale).lower():
            return False
        if not os.path.isdir(self.gdb_path):
            return False
        if not os.path.exists(os.path.join(self.gdb_path, 'analysis_boundary')):
            return False

        constant_size = _raster_size(os.path.join(self.root_dir, 'constant_raster.tif'))
        analysis_size = _raster_size(os.path.join(self.root_dir, 'analysis_raster.tif'))
        if constant_size is None or analysis_size is None:
            return False
        if constant_size != (int(self.raster_config['constant_raster_size']), int(self.raster_config['constant_raster_size'])):
            return False
        if analysis_size != (int(self.raster_config['analysis_raster_size']), int(self.raster_config['analysis_raster_size'])):
            return False

        dataset_counts = manifest.get('dataset_counts') or {}
        expected_counts = {
            'buffer_points': int(self.vector_config['buffer_points']),
            'spatial_join_points': int(self.vector_config['spatial_join_points']),
            'spatial_join_polygons': int(self.vector_config['spatial_join_polygons']),
            'calculate_field_fc': int(self.vector_config['calculate_field_records']),
            'test_polygons_a': int(self.vector_config['intersect_features_a']),
            'test_polygons_b': int(self.vector_config['intersect_features_b']),
            'analysis_boundary': 1,
        }
        for name, expected_count in expected_counts.items():
            if int(dataset_counts.get(name, -1)) != int(expected_count):
                return False
            path = os.path.join(self.gdb_path, name)
            if _feature_count(path) != int(expected_count):
                return False

        return True

    def _build_manifest(self, source_mode, source_info, analysis_extent, block_size, dataset_counts):
        manifest = {
            'schema_version': MANIFEST_VERSION,
            'scale': self.scale,
            'generated_at': datetime.utcnow().isoformat(),
            'root_dir': self.root_dir,
            'gdb_path': self.gdb_path,
            'analysis_crs': PROJECTED_WKID,
            'source_mode': source_mode,
            'source_region': source_info.get('label') if source_info else 'Synthetic',
            'osm_source': source_info or {},
            'analysis_boundary_path': os.path.join(self.gdb_path, 'analysis_boundary'),
            'analysis_boundary_extent': _extent_dict(analysis_extent),
            'analysis_raster_path': os.path.join(self.root_dir, 'analysis_raster.tif'),
            'constant_raster_path': os.path.join(self.root_dir, 'constant_raster.tif'),
            'analysis_raster_block_size': int(block_size),
            'vector_config': copy.deepcopy(self.vector_config),
            'raster_config': copy.deepcopy(self.raster_config),
            'dataset_counts': dataset_counts,
        }
        return manifest

    def _build_from_source_layers(self, source_info):
        print("  [OSM] Using cached source: {} ({})".format(source_info.get('label'), source_info.get('slug')))
        projected_sr = _projected_spatial_reference()
        source_layers = source_info.get('layers') or {}
        imported_layers = {}
        for source_key, target_name in OSM_LAYER_TARGETS:
            source_path = source_layers.get(source_key)
            if not source_path:
                continue
            output_fc = os.path.join(self.gdb_path, target_name)
            try:
                _project_source_layer(source_path, output_fc, projected_sr)
                imported_layers[target_name] = output_fc
                print("    imported {} -> {}".format(source_key, target_name))
            except Exception as exc:
                print("    warning: failed to import {}: {}".format(source_key, exc))

        extents = _collect_extents(imported_layers.values())
        analysis_extent = _square_extent_from_extents(extents, margin_ratio=0.08, default_side=1000000.0)
        boundary_fc = os.path.join(self.gdb_path, 'analysis_boundary')
        _create_boundary(boundary_fc, analysis_extent, 'osm', source_info.get('label', 'OSM'))

        roads_fc = imported_layers.get('osm_roads')
        buildings_fc = imported_layers.get('osm_buildings')
        landuse_fc = imported_layers.get('osm_landuse')
        pois_fc = imported_layers.get('osm_pois')
        places_fc = imported_layers.get('osm_places')

        buffer_points_fc = os.path.join(self.gdb_path, 'buffer_points')
        spatial_join_points_fc = os.path.join(self.gdb_path, 'spatial_join_points')
        spatial_join_polygons_fc = os.path.join(self.gdb_path, 'spatial_join_polygons')
        calculate_field_fc = os.path.join(self.gdb_path, 'calculate_field_fc')
        test_polygons_a_fc = os.path.join(self.gdb_path, 'test_polygons_a')
        test_polygons_b_fc = os.path.join(self.gdb_path, 'test_polygons_b')

        poi_geoms = _load_geometry_samples(pois_fc, limit=max(self.vector_config['buffer_points'], self.vector_config['spatial_join_points']))
        place_geoms = _load_geometry_samples(places_fc, limit=max(self.vector_config['buffer_points'], self.vector_config['spatial_join_points']))
        building_geoms = _load_geometry_samples(buildings_fc, limit=self.vector_config['calculate_field_records'])
        landuse_geoms = _load_geometry_samples(landuse_fc, limit=self.vector_config['spatial_join_polygons'])

        _create_point_sample(buffer_points_fc, poi_geoms or place_geoms, int(self.vector_config['buffer_points']), analysis_extent, 'osm_buffer_points', source_info.get('label', 'OSM'))
        _create_point_sample(spatial_join_points_fc, place_geoms or poi_geoms, int(self.vector_config['spatial_join_points']), analysis_extent, 'osm_spatial_join_points', source_info.get('label', 'OSM'))
        if landuse_geoms:
            _create_polygon_sample(spatial_join_polygons_fc, landuse_geoms, int(self.vector_config['spatial_join_polygons']), analysis_extent, 'osm_join_zones', source_info.get('label', 'OSM'))
        else:
            rows, cols = factor_grid_dimensions(int(self.vector_config['spatial_join_polygons']))
            _create_fishnet(spatial_join_polygons_fc, analysis_extent, rows, cols, 'osm_join_zones', source_info.get('label', 'OSM'))
        _create_polygon_sample(calculate_field_fc, building_geoms or landuse_geoms, int(self.vector_config['calculate_field_records']), analysis_extent, 'osm_calculate_field', source_info.get('label', 'OSM'))

        rows_a, cols_a = factor_grid_dimensions(int(self.vector_config['intersect_features_a']))
        rows_b, cols_b = factor_grid_dimensions(int(self.vector_config['intersect_features_b']))
        _create_fishnet(test_polygons_a_fc, analysis_extent, rows_a, cols_a, 'osm_intersect_a', source_info.get('label', 'OSM'), offset=False)
        _create_fishnet(test_polygons_b_fc, analysis_extent, rows_b, cols_b, 'osm_intersect_b', source_info.get('label', 'OSM'), offset=True)

        constant_raster_path, analysis_raster_path, block_size = _create_rasters(
            self.root_dir,
            analysis_extent,
            'osm',
            source_info.get('label', 'OSM'),
            self.raster_config
        )

        dataset_counts = {
            'analysis_boundary': _feature_count(boundary_fc),
            'buffer_points': _feature_count(buffer_points_fc),
            'spatial_join_points': _feature_count(spatial_join_points_fc),
            'spatial_join_polygons': _feature_count(spatial_join_polygons_fc),
            'calculate_field_fc': _feature_count(calculate_field_fc),
            'test_polygons_a': _feature_count(test_polygons_a_fc),
            'test_polygons_b': _feature_count(test_polygons_b_fc),
            'osm_roads': _feature_count(roads_fc),
            'osm_buildings': _feature_count(buildings_fc),
            'osm_landuse': _feature_count(landuse_fc),
            'osm_pois': _feature_count(pois_fc),
            'osm_places': _feature_count(places_fc),
        }

        manifest = self._build_manifest('osm', source_info, analysis_extent, block_size, dataset_counts)
        manifest['constant_raster_path'] = constant_raster_path
        manifest['analysis_raster_path'] = analysis_raster_path
        return manifest

    def _build_synthetic(self):
        print("  [Fallback] Building synthetic benchmark inputs")
        projected_sr = _projected_spatial_reference()
        side = 1000000.0
        analysis_extent = (-side / 2.0, -side / 2.0, side / 2.0, side / 2.0)
        boundary_fc = os.path.join(self.gdb_path, 'analysis_boundary')
        _create_boundary(boundary_fc, analysis_extent, 'synthetic', 'Synthetic')

        buffer_points_fc = os.path.join(self.gdb_path, 'buffer_points')
        spatial_join_points_fc = os.path.join(self.gdb_path, 'spatial_join_points')
        spatial_join_polygons_fc = os.path.join(self.gdb_path, 'spatial_join_polygons')
        calculate_field_fc = os.path.join(self.gdb_path, 'calculate_field_fc')
        test_polygons_a_fc = os.path.join(self.gdb_path, 'test_polygons_a')
        test_polygons_b_fc = os.path.join(self.gdb_path, 'test_polygons_b')

        _create_random_points(buffer_points_fc, int(self.vector_config['buffer_points']), analysis_extent, 'synthetic_buffer_points', 'Synthetic')
        _create_random_points(spatial_join_points_fc, int(self.vector_config['spatial_join_points']), analysis_extent, 'synthetic_spatial_join_points', 'Synthetic')

        rows_z, cols_z = factor_grid_dimensions(int(self.vector_config['spatial_join_polygons']))
        _create_fishnet(spatial_join_polygons_fc, analysis_extent, rows_z, cols_z, 'synthetic_join_zones', 'Synthetic')

        _create_fishnet(calculate_field_fc, analysis_extent, rows_z, cols_z, 'synthetic_calculate_field', 'Synthetic')
        rows_a, cols_a = factor_grid_dimensions(int(self.vector_config['intersect_features_a']))
        rows_b, cols_b = factor_grid_dimensions(int(self.vector_config['intersect_features_b']))
        _create_fishnet(test_polygons_a_fc, analysis_extent, rows_a, cols_a, 'synthetic_intersect_a', 'Synthetic', offset=False)
        _create_fishnet(test_polygons_b_fc, analysis_extent, rows_b, cols_b, 'synthetic_intersect_b', 'Synthetic', offset=True)

        constant_raster_path, analysis_raster_path, block_size = _create_rasters(
            self.root_dir,
            analysis_extent,
            'synthetic',
            'Synthetic',
            self.raster_config
        )

        dataset_counts = {
            'analysis_boundary': _feature_count(boundary_fc),
            'buffer_points': _feature_count(buffer_points_fc),
            'spatial_join_points': _feature_count(spatial_join_points_fc),
            'spatial_join_polygons': _feature_count(spatial_join_polygons_fc),
            'calculate_field_fc': _feature_count(calculate_field_fc),
            'test_polygons_a': _feature_count(test_polygons_a_fc),
            'test_polygons_b': _feature_count(test_polygons_b_fc),
            'osm_roads': 0,
            'osm_buildings': 0,
            'osm_landuse': 0,
            'osm_pois': 0,
            'osm_places': 0,
        }

        manifest = self._build_manifest('synthetic', {}, analysis_extent, block_size, dataset_counts)
        manifest['constant_raster_path'] = constant_raster_path
        manifest['analysis_raster_path'] = analysis_raster_path
        manifest['analysis_crs'] = 3857
        return manifest

    def generate_all(self, force=False):
        """Generate all inputs and return the manifest payload."""
        if not HAS_ARCPY:
            raise RuntimeError("ArcPy is required to generate benchmark input data")

        _ensure_dir(self.root_dir)
        clear_workspace_cache(self.root_dir)

        if not force:
            existing_manifest = load_manifest(self.root_dir, default={})
            if self._validate_existing_assets(existing_manifest):
                print("  Reusing existing benchmark inputs from {}".format(self.gdb_path))
                return existing_manifest

        print("  Preparing benchmark inputs for scale: {}".format(self.scale))
        _delete_path(self.gdb_path)

        try:
            arcpy.CreateFileGDB_management(self.root_dir, self.gdb_name)
        except Exception as exc:
            raise RuntimeError("Failed to create benchmark geodatabase: {}".format(exc))

        manifest = None
        source_info = None
        try:
            try:
                source_info = ensure_osm_sample_cache(getattr(settings, 'OSM_CACHE_DIR', None), preferred_source='hong-kong')
                manifest = self._build_from_source_layers(source_info)
            except Exception as osm_exc:
                print("  [OSM] {}. Falling back to synthetic data.".format(osm_exc))
                manifest = self._build_synthetic()

            save_manifest(self.root_dir, manifest)
            print("  Wrote manifest: {}".format(self.manifest_path))
            print("  Source mode: {}".format(manifest.get('source_mode')))
            print("  Boundary extent: {}".format(manifest.get('analysis_boundary_extent')))
            print("  Constant raster: {}".format(manifest.get('constant_raster_path')))
            print("  Analysis raster: {}".format(manifest.get('analysis_raster_path')))
            return manifest
        except Exception:
            clear_workspace_cache(self.root_dir)
            raise
        finally:
            clear_workspace_cache(self.root_dir)


def generate_all(force=False):
    """Convenience wrapper used by external scripts."""
    return TestDataGenerator().generate_all(force=force)


if __name__ == '__main__':
    print("Generating benchmark input data...")
    payload = generate_all(force='--force' in sys.argv)
    print("Done. Mode: {}".format(payload.get('source_mode')))
