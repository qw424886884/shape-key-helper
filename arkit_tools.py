# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

from .constants import ARKIT_DIRECTION_EXCEPTION_KEYS, ARKIT_SHAPE_KEYS
from .i18n import _tr
from .shape_key_core import (
    _basis_shape_key,
    _mirror_pairing_for_basis,
    _missing_basis_error,
    _repair_pair_shape_key_symmetry,
    _repair_self_shape_key_symmetry,
    _shape_key_blocks,
    _unique_mirror_vertex_pairs,
    infer_opposite_shape_key_name,
)


def add_missing_arkit_shape_keys(obj):
    if obj is None or obj.type not in {"MESH", "CURVE"}:
        raise ValueError(_tr("Select a mesh or curve object."))

    if obj.data.shape_keys is None:
        obj.shape_key_add(name="Basis", from_mix=False)

    key_blocks = obj.data.shape_keys.key_blocks
    existing_names = {key_block.name for key_block in key_blocks}
    added = 0
    skipped = 0
    for shape_key_name in ARKIT_SHAPE_KEYS:
        if shape_key_name in existing_names:
            skipped += 1
            continue
        obj.shape_key_add(name=shape_key_name, from_mix=False)
        existing_names.add(shape_key_name)
        added += 1

    return {"added": added, "skipped": skipped, "total": len(ARKIT_SHAPE_KEYS)}


def convert_arkit_shape_key_names(obj, to_symmetrical=True):
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is None:
        raise ValueError(_tr("No shape keys found on the selected object."))

    renamed = 0
    skipped = 0
    for key_block in key_blocks:
        original_name = key_block.name
        if original_name in ARKIT_DIRECTION_EXCEPTION_KEYS:
            skipped += 1
            continue

        if to_symmetrical:
            new_name = original_name.replace("Left", "_L").replace("Right", "_R")
        else:
            new_name = original_name.replace("_L", "Left").replace("_R", "Right")

        if new_name != original_name:
            key_block.name = new_name
            renamed += 1

    return {"renamed": renamed, "skipped": skipped}


def _first_letter_lower(name):
    return name[:1].lower() + name[1:] if name else name


def _first_letter_upper(name):
    return name[:1].upper() + name[1:] if name else name


def _first_letter_case_variant(name):
    if not name:
        return name
    return _first_letter_lower(name) if name[0].isupper() else _first_letter_upper(name)


def _arkit_shape_key_name_candidates(canonical_name):
    candidates = []
    for name in (
        canonical_name,
        _first_letter_lower(canonical_name),
        _first_letter_upper(canonical_name),
    ):
        if name and name not in candidates:
            candidates.append(name)
        if name not in ARKIT_DIRECTION_EXCEPTION_KEYS:
            symmetrical_name = name.replace("Left", "_L").replace("Right", "_R")
            if symmetrical_name != name and symmetrical_name not in candidates:
                candidates.append(symmetrical_name)
    return candidates


def _resolve_arkit_shape_key_name(key_blocks, canonical_name):
    for candidate in _arkit_shape_key_name_candidates(canonical_name):
        if candidate in key_blocks:
            return candidate
    return None


def arkit_shape_key_names_for_vrm_proxy(key_case):
    if key_case == "UPPER":
        return list(ARKIT_SHAPE_KEYS)
    if key_case == "LOWER":
        return [_first_letter_lower(name) for name in ARKIT_SHAPE_KEYS]
    raise ValueError(f"Unknown VRM ARKit case option: {key_case}")


def _collect_arkit_symmetry_work_items(key_blocks):
    actual_names = {
        canonical_name: _resolve_arkit_shape_key_name(key_blocks, canonical_name)
        for canonical_name in ARKIT_SHAPE_KEYS
    }
    missing_keys = [
        canonical_name
        for canonical_name, actual_name in actual_names.items()
        if actual_name is None
    ]
    processed = set()
    work_items = []

    for canonical_name in ARKIT_SHAPE_KEYS:
        if canonical_name in processed or actual_names[canonical_name] is None:
            continue

        opposite_name = infer_opposite_shape_key_name(canonical_name)
        if opposite_name in ARKIT_SHAPE_KEYS:
            if opposite_name not in processed and actual_names.get(opposite_name):
                work_items.append(
                    (
                        "PAIR",
                        canonical_name,
                        actual_names[canonical_name],
                        opposite_name,
                        actual_names[opposite_name],
                    )
                )
                processed.add(canonical_name)
                processed.add(opposite_name)
            continue

        work_items.append(("SELF", canonical_name, actual_names[canonical_name]))
        processed.add(canonical_name)

    return work_items, missing_keys


def repair_arkit_shape_key_symmetry(obj, tolerance_percent=0.5, base_shape_key_name=None):
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is None:
        raise ValueError(_tr("No shape keys found on the selected object."))
    basis_key = _basis_shape_key(key_blocks, base_shape_key_name)
    if basis_key is None:
        raise _missing_basis_error()

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
    work_items, missing_keys = _collect_arkit_symmetry_work_items(key_blocks)
    result = {
        "shape_keys_checked": len(ARKIT_SHAPE_KEYS) - len(missing_keys),
        "shape_key_groups_checked": len(work_items),
        "shape_key_groups_repaired": 0,
        "changed_relations": 0,
        "deviated_relations": 0,
        "max_deviation": 0.0,
        "missing_keys": missing_keys,
        "unmatched_basis_vertices": pairing["unmatched"],
    }

    for item in work_items:
        if item[0] == "SELF":
            _kind, _canonical_name, actual_name = item
            repair = _repair_self_shape_key_symmetry(
                key_blocks[actual_name],
                basis_key,
                mirror_pairs,
                pairing["tolerance_distance"],
            )
        else:
            _kind, _left_name, actual_left_name, _right_name, actual_right_name = item
            repair = _repair_pair_shape_key_symmetry(
                key_blocks[actual_left_name],
                key_blocks[actual_right_name],
                basis_key,
                mirror_pairs,
                pairing["tolerance_distance"],
            )

        if repair["changed_relations"]:
            result["shape_key_groups_repaired"] += 1
        result["changed_relations"] += repair["changed_relations"]
        result["deviated_relations"] += repair["deviated_relations"]
        result["max_deviation"] = max(result["max_deviation"], repair["max_deviation"])

    obj.data.update()
    return result
