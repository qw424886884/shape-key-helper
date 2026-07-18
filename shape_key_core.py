# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

from mathutils import Vector
from mathutils.kdtree import KDTree

from .constants import NAME_PAIRS
from .i18n import _tr


MISSING_BASIS_MESSAGE = "No usable base shape key found. Shape keys need a base shape key as the first shape key, usually named Basis/基型/基础. Select a mesh with shape keys, or recreate/reimport the model so the base shape is present before using mirror, reset, or repair."


def infer_opposite_shape_key_name(shape_key_name):
    """Return the opposite side shape key name inferred from the selected key."""
    for left, right in NAME_PAIRS:
        if right in shape_key_name:
            return shape_key_name.replace(right, left, 1)
        if left in shape_key_name:
            return shape_key_name.replace(left, right, 1)
    if len(shape_key_name) > 2 and shape_key_name[0] in {"L", "R"} and shape_key_name[1].isupper():
        return ("R" if shape_key_name[0] == "L" else "L") + shape_key_name[1:]
    if len(shape_key_name) > 2 and shape_key_name[-1] in {"L", "R"} and (
        shape_key_name[-2].islower() or shape_key_name[-2].isdigit()
    ):
        return shape_key_name[:-1] + ("R" if shape_key_name[-1] == "L" else "L")
    return None


def _shape_key_blocks(obj):
    if obj is None or obj.type != "MESH" or obj.data.shape_keys is None:
        return None
    return obj.data.shape_keys.key_blocks


class BaseShapeKeyError(ValueError):
    pass


def _missing_basis_error():
    return BaseShapeKeyError(_tr(MISSING_BASIS_MESSAGE))


def _base_shape_key_name(base_shape_key_name):
    return str(base_shape_key_name or "").strip()


def _basis_shape_key(key_blocks, base_shape_key_name=None):
    if key_blocks is None:
        return None
    configured_name = _base_shape_key_name(base_shape_key_name)
    if configured_name:
        if configured_name not in key_blocks:
            raise BaseShapeKeyError(_tr(
                "Base shape key not found: {name}. Clear Base Shape to use automatic first-key detection, or choose an existing base shape key.",
                name=configured_name,
            ))
        return key_blocks[configured_name]
    for key_block in key_blocks:
        return key_block
    return None


def _is_basis_shape_key_name(key_blocks, shape_key_name, base_shape_key_name=None):
    basis_key = _basis_shape_key(key_blocks, base_shape_key_name)
    return basis_key is not None and shape_key_name == basis_key.name


def _base_key_reset_error(base_shape_key_name=None):
    if _base_shape_key_name(base_shape_key_name):
        return BaseShapeKeyError(_tr("The selected base shape key cannot be reset. Select a normal shape key; if this is wrong, clear Base Shape or choose the model's default base shape."))
    return BaseShapeKeyError(_tr("The first shape key is treated as the base shape key and cannot be reset. Select a normal shape key; if this is wrong, set the base shape as the first shape key."))


def _base_key_source_target_error(base_shape_key_name=None):
    if _base_shape_key_name(base_shape_key_name):
        return BaseShapeKeyError(_tr("The selected base shape key cannot be used as source or target. Select normal expression keys; if this is wrong, clear Base Shape or choose the model's default base shape."))
    return BaseShapeKeyError(_tr("The first shape key is treated as the base shape key and cannot be used as source or target. Select normal expression keys; if this is wrong, set the base shape as the first shape key."))


def _open_base_shape_settings_on_error(context, exc):
    if isinstance(exc, BaseShapeKeyError) and getattr(context, "scene", None) is not None:
        setattr(context.scene, "shape_key_mirror_show_base_settings", True)


def _build_mirrored_basis_lookup(basis_key, mirror_plane_x):
    tree = KDTree(len(basis_key.data))
    for index, point in enumerate(basis_key.data):
        co = point.co
        tree.insert(Vector((2.0 * mirror_plane_x - co.x, co.y, co.z)), index)
    tree.balance()
    return tree


def _mirror_pairing_for_basis(basis_key, tolerance_percent):
    if len(basis_key.data) == 0:
        return {
            "pairs": [],
            "written": 0,
            "unmatched": 0,
            "max_pair_distance": 0.0,
            "tolerance_distance": 0.0,
            "tolerance_percent": tolerance_percent,
            "mirror_plane_x": 0.0,
            "model_span": 0.0,
        }

    min_x = min(point.co.x for point in basis_key.data)
    max_x = max(point.co.x for point in basis_key.data)
    min_y = min(point.co.y for point in basis_key.data)
    max_y = max(point.co.y for point in basis_key.data)
    min_z = min(point.co.z for point in basis_key.data)
    max_z = max(point.co.z for point in basis_key.data)
    mirror_plane_x = (min_x + max_x) * 0.5
    lookup = _build_mirrored_basis_lookup(basis_key, mirror_plane_x)
    model_span = max(max_x - min_x, max_y - min_y, max_z - min_z, 1e-8)

    pairs = []
    unmatched = 0
    max_pair_distance = 0.0
    tolerance_percent = max(min(float(tolerance_percent), 5.0), 0.0)
    tolerance_distance = model_span * (tolerance_percent * 0.01)

    for target_index, target_basis_point in enumerate(basis_key.data):
        _, source_index, distance = lookup.find(target_basis_point.co)
        max_pair_distance = max(max_pair_distance, distance)
        if distance > tolerance_distance:
            pairs.append((target_index, None, distance))
            unmatched += 1
        else:
            pairs.append((target_index, source_index, distance))

    return {
        "pairs": pairs,
        "written": len(basis_key.data) - unmatched,
        "unmatched": unmatched,
        "max_pair_distance": max_pair_distance,
        "tolerance_distance": tolerance_distance,
        "tolerance_percent": tolerance_percent,
        "mirror_plane_x": mirror_plane_x,
        "model_span": model_span,
    }


class _MeshVertexCoordinateBlock:
    def __init__(self, mesh):
        self.name = "Mesh Vertices"
        self.data = mesh.vertices


def _coordinate_vector(co):
    return Vector((co.x, co.y, co.z))


def _mesh_vertex_coordinate_block(obj):
    if obj is None or obj.type != "MESH":
        raise ValueError(_tr("Select a mesh object."))
    vertices = getattr(getattr(obj, "data", None), "vertices", None)
    if vertices is None or len(vertices) == 0:
        raise ValueError(_tr("Selected mesh has no vertices."))
    return _MeshVertexCoordinateBlock(obj.data)


def _mesh_symmetry_reference_block(obj, base_shape_key_name=None):
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is not None and len(key_blocks) > 0:
        basis_key = _basis_shape_key(key_blocks, base_shape_key_name)
        if basis_key is None:
            raise _missing_basis_error()
        return basis_key, key_blocks
    return _mesh_vertex_coordinate_block(obj), None


def _mirrored_delta(delta):
    return Vector((-delta.x, delta.y, delta.z))


def _symmetrized_centered_coordinates(reference_block, mirror_pairs, mirror_plane_x):
    original_coords = [_coordinate_vector(point.co) for point in reference_block.data]
    repaired_coords = list(original_coords)

    for left_index, right_index in mirror_pairs:
        left_co = original_coords[left_index]
        if left_index == right_index:
            repaired_coords[left_index] = Vector((0.0, left_co.y, left_co.z))
            continue

        right_co = original_coords[right_index]
        left_relative = Vector((left_co.x - mirror_plane_x, left_co.y, left_co.z))
        right_relative = Vector((right_co.x - mirror_plane_x, right_co.y, right_co.z))
        repaired_left = (left_relative + _mirrored_delta(right_relative)) * 0.5
        repaired_right = _mirrored_delta(repaired_left)
        repaired_coords[left_index] = repaired_left
        repaired_coords[right_index] = repaired_right

    return original_coords, repaired_coords


def analyze_shape_key_mirror(obj, source_name, target_name, tolerance_percent, base_shape_key_name=None):
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is None:
        raise ValueError("Selected object is not a mesh with shape keys.")
    basis_key = _basis_shape_key(key_blocks, base_shape_key_name)
    if basis_key is None:
        raise _missing_basis_error()
    if source_name not in key_blocks:
        raise ValueError(f"Missing source shape key: {source_name}")
    if target_name not in key_blocks:
        raise ValueError(f"Missing target shape key: {target_name}")
    if (
        _is_basis_shape_key_name(key_blocks, source_name, base_shape_key_name)
        or _is_basis_shape_key_name(key_blocks, target_name, base_shape_key_name)
    ):
        raise _base_key_source_target_error(base_shape_key_name)
    if source_name == target_name:
        raise ValueError("Source and target shape key names are the same.")

    source_key = key_blocks[source_name]
    target_key = key_blocks[target_name]
    pairing = _mirror_pairing_for_basis(basis_key, tolerance_percent)
    source_nonzero = 0
    target_nonzero = 0
    for index, point in enumerate(basis_key.data):
        if (source_key.data[index].co - point.co).length > 1e-8:
            source_nonzero += 1
        if (target_key.data[index].co - point.co).length > 1e-8:
            target_nonzero += 1

    return {
        **pairing,
        "source_nonzero": source_nonzero,
        "target_nonzero": target_nonzero,
    }


def mirror_shape_key_to_target(obj, source_name, target_name, tolerance_percent, base_shape_key_name=None):
    """Mirror source_name into target_name on obj without creating, deleting, or renaming keys."""
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is None:
        raise ValueError("Selected object is not a mesh with shape keys.")
    basis_key = _basis_shape_key(key_blocks, base_shape_key_name)
    if basis_key is None:
        raise _missing_basis_error()
    if source_name not in key_blocks:
        raise ValueError(f"Missing source shape key: {source_name}")
    if target_name not in key_blocks:
        raise ValueError(f"Missing target shape key: {target_name}")
    if (
        _is_basis_shape_key_name(key_blocks, source_name, base_shape_key_name)
        or _is_basis_shape_key_name(key_blocks, target_name, base_shape_key_name)
    ):
        raise _base_key_source_target_error(base_shape_key_name)
    if source_name == target_name:
        raise ValueError("Source and target shape key names are the same.")

    source_key = key_blocks[source_name]
    target_key = key_blocks[target_name]

    analysis = analyze_shape_key_mirror(obj, source_name, target_name, tolerance_percent, base_shape_key_name)
    if analysis["unmatched"]:
        raise ValueError(
            _tr(
                "Mesh is asymmetric; mirror cancelled. Unmatched vertices: {count}. Try a larger tolerance or fix mesh symmetry first. Current tolerance: {percent:.2f}% ({distance:.6f}), max deviation: {max_distance:.6f}.",
                count=analysis["unmatched"],
                percent=analysis["tolerance_percent"],
                distance=analysis["tolerance_distance"],
                max_distance=analysis["max_pair_distance"],
            )
        )

    for target_index, source_index, _distance in analysis["pairs"]:
        target_basis_point = basis_key.data[target_index]
        target_basis = target_basis_point.co

        if source_index is None:
            continue

        source_basis = basis_key.data[source_index].co
        source_delta = source_key.data[source_index].co - source_basis
        mirrored_delta = Vector((-source_delta.x, source_delta.y, source_delta.z))
        target_key.data[target_index].co = target_basis + mirrored_delta

    obj.data.update()
    return analysis


def reset_shape_key_to_basis(obj, shape_key_name, base_shape_key_name=None):
    """Reset shape_key_name to the base shape coordinates without changing other shape keys."""
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is None:
        raise ValueError("Selected object is not a mesh with shape keys.")
    basis_key = _basis_shape_key(key_blocks, base_shape_key_name)
    if basis_key is None:
        raise _missing_basis_error()
    if shape_key_name not in key_blocks:
        raise ValueError(f"Missing shape key: {shape_key_name}")
    if _is_basis_shape_key_name(key_blocks, shape_key_name, base_shape_key_name):
        raise _base_key_reset_error(base_shape_key_name)

    target_key = key_blocks[shape_key_name]
    for index, basis_point in enumerate(basis_key.data):
        target_key.data[index].co = basis_point.co.copy()

    obj.data.update()
    return {"shape_key": shape_key_name, "reset": len(basis_key.data)}


def _unique_mirror_vertex_pairs(pairing):
    seen = set()
    for target_index, source_index, _distance in pairing["pairs"]:
        if source_index is None:
            continue
        pair = tuple(sorted((target_index, source_index)))
        if pair in seen:
            continue
        seen.add(pair)
        yield pair


def _repair_self_shape_key_symmetry(key_block, basis_key, mirror_pairs, tolerance_distance, prefer_nonzero_side=False):
    changed_relations = 0
    deviated_relations = 0
    max_deviation = 0.0
    write_epsilon = 1e-8

    for left_index, right_index in mirror_pairs:
        left_delta = key_block.data[left_index].co - basis_key.data[left_index].co
        right_delta = key_block.data[right_index].co - basis_key.data[right_index].co
        deviation = (left_delta - _mirrored_delta(right_delta)).length
        max_deviation = max(max_deviation, deviation)
        if deviation > tolerance_distance:
            deviated_relations += 1
        if deviation <= write_epsilon:
            continue

        left_delta_len = left_delta.length
        right_delta_len = right_delta.length
        if prefer_nonzero_side and left_delta_len <= tolerance_distance < right_delta_len:
            repaired_left_delta = _mirrored_delta(right_delta)
            repaired_right_delta = right_delta
        elif prefer_nonzero_side and right_delta_len <= tolerance_distance < left_delta_len:
            repaired_left_delta = left_delta
            repaired_right_delta = _mirrored_delta(left_delta)
        else:
            repaired_left_delta = (left_delta + _mirrored_delta(right_delta)) * 0.5
            repaired_right_delta = _mirrored_delta(repaired_left_delta)
        key_block.data[left_index].co = basis_key.data[left_index].co + repaired_left_delta
        key_block.data[right_index].co = basis_key.data[right_index].co + repaired_right_delta
        changed_relations += 1

    return {
        "changed_relations": changed_relations,
        "deviated_relations": deviated_relations,
        "max_deviation": max_deviation,
    }


def _repair_pair_shape_key_relation(key_a, key_b, basis_key, index_a, index_b, tolerance_distance):
    delta_a = key_a.data[index_a].co - basis_key.data[index_a].co
    delta_b = key_b.data[index_b].co - basis_key.data[index_b].co
    deviation = (delta_a - _mirrored_delta(delta_b)).length
    if deviation <= 1e-8:
        return {
            "changed_relations": 0,
            "deviated_relations": 1 if deviation > tolerance_distance else 0,
            "max_deviation": deviation,
        }

    repaired_delta_a = (delta_a + _mirrored_delta(delta_b)) * 0.5
    repaired_delta_b = _mirrored_delta(repaired_delta_a)
    key_a.data[index_a].co = basis_key.data[index_a].co + repaired_delta_a
    key_b.data[index_b].co = basis_key.data[index_b].co + repaired_delta_b
    return {
        "changed_relations": 1,
        "deviated_relations": 1 if deviation > tolerance_distance else 0,
        "max_deviation": deviation,
    }


def _repair_pair_shape_key_symmetry(key_a, key_b, basis_key, mirror_pairs, tolerance_distance):
    changed_relations = 0
    deviated_relations = 0
    max_deviation = 0.0

    for left_index, right_index in mirror_pairs:
        for index_a, index_b in (
            (left_index, right_index),
            (right_index, left_index),
        ):
            if left_index == right_index and index_a != left_index:
                continue
            result = _repair_pair_shape_key_relation(
                key_a,
                key_b,
                basis_key,
                index_a,
                index_b,
                tolerance_distance,
            )
            changed_relations += result["changed_relations"]
            deviated_relations += result["deviated_relations"]
            max_deviation = max(max_deviation, result["max_deviation"])

    return {
        "changed_relations": changed_relations,
        "deviated_relations": deviated_relations,
        "max_deviation": max_deviation,
    }


def repair_mesh_symmetry(obj, tolerance_percent=0.5, base_shape_key_name=None):
    """Center the mesh on X=0 and repair vertex-level symmetry without touching UVs."""
    reference_block, key_blocks = _mesh_symmetry_reference_block(obj, base_shape_key_name)
    pairing = _mirror_pairing_for_basis(reference_block, tolerance_percent)
    if pairing["unmatched"]:
        raise ValueError(
            _tr(
                "Mesh is asymmetric; mirror cancelled. Unmatched vertices: {count}. Try a larger tolerance or fix mesh symmetry first. Current tolerance: {percent:.2f}% ({distance:.6f}), max deviation: {max_distance:.6f}.",
                count=pairing["unmatched"],
                percent=pairing["tolerance_percent"],
                distance=pairing["tolerance_distance"],
                max_distance=pairing["max_pair_distance"],
            )
        )

    mirror_pairs = list(_unique_mirror_vertex_pairs(pairing))
    original_coords, repaired_coords = _symmetrized_centered_coordinates(
        reference_block,
        mirror_pairs,
        pairing["mirror_plane_x"],
    )
    corrections = [
        repaired_coord - original_coord
        for original_coord, repaired_coord in zip(original_coords, repaired_coords)
    ]
    changed_vertices = sum(1 for correction in corrections if correction.length > 1e-8)

    if key_blocks is not None:
        shape_keys_adjusted = 0
        for key_block in key_blocks:
            for index, point in enumerate(key_block.data):
                point.co = point.co + corrections[index]
            shape_keys_adjusted += 1
    else:
        for index, point in enumerate(reference_block.data):
            point.co = repaired_coords[index]
        shape_keys_adjusted = 0

    obj.data.update()
    return {
        **pairing,
        "vertices": len(reference_block.data),
        "mirror_pairs": len(mirror_pairs),
        "changed_vertices": changed_vertices,
        "center_shift_x": -pairing["mirror_plane_x"],
        "shape_keys_adjusted": shape_keys_adjusted,
    }


def repair_active_shape_key_self_symmetry(obj, shape_key_name, tolerance_percent=0.5, base_shape_key_name=None):
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is None:
        raise ValueError(_tr("No shape keys found on the selected object."))
    basis_key = _basis_shape_key(key_blocks, base_shape_key_name)
    if basis_key is None:
        raise _missing_basis_error()
    if shape_key_name not in key_blocks:
        raise ValueError(f"Missing shape key: {shape_key_name}")
    if _is_basis_shape_key_name(key_blocks, shape_key_name, base_shape_key_name):
        raise _base_key_source_target_error(base_shape_key_name)

    pairing = _mirror_pairing_for_basis(basis_key, tolerance_percent)
    if pairing["unmatched"]:
        raise ValueError(
            _tr(
                "Mesh is asymmetric; mirror cancelled. Unmatched vertices: {count}. Try a larger tolerance or fix mesh symmetry first. Current tolerance: {percent:.2f}% ({distance:.6f}), max deviation: {max_distance:.6f}.",
                count=pairing["unmatched"],
                percent=pairing["tolerance_percent"],
                distance=pairing["tolerance_distance"],
                max_distance=pairing["max_pair_distance"],
            )
        )

    mirror_pairs = list(_unique_mirror_vertex_pairs(pairing))
    repair = _repair_self_shape_key_symmetry(
        key_blocks[shape_key_name],
        basis_key,
        mirror_pairs,
        pairing["tolerance_distance"],
        prefer_nonzero_side=True,
    )
    obj.data.update()
    return {
        **pairing,
        **repair,
        "shape_key": shape_key_name,
        "mirror_pairs": len(mirror_pairs),
    }
