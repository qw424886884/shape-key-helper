# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .arkit_tools import (
    _arkit_shape_key_name_candidates,
    _first_letter_case_variant,
    _resolve_arkit_shape_key_name,
    arkit_shape_key_names_for_vrm_proxy,
)
from .constants import ARKIT_SHAPE_KEYS, VRM0_DEFAULT_EXPRESSION_MAPPINGS
from .i18n import _tr
from .shape_key_core import _shape_key_blocks


def _vrm_addon_available():
    return hasattr(bpy.types.Armature, "vrm_addon_extension")


def _armature_vrm_extension(obj):
    if obj is None or obj.type != "ARMATURE":
        return None
    if not _vrm_addon_available():
        return None
    return getattr(obj.data, "vrm_addon_extension", None)


def _is_vrm0_armature(obj):
    ext = _armature_vrm_extension(obj)
    if ext is None or not hasattr(ext, "vrm0"):
        return False
    return str(getattr(ext, "spec_version", "")) == "0.0"


def _iter_unique_objects(objects):
    seen = set()
    for obj in objects:
        if obj is None:
            continue
        pointer = obj.as_pointer()
        if pointer in seen:
            continue
        seen.add(pointer)
        yield obj


def _object_armature_modifiers(obj):
    for modifier in getattr(obj, "modifiers", []):
        if getattr(modifier, "type", None) == "ARMATURE" and getattr(modifier, "object", None):
            yield modifier.object


def _find_vrm0_armature(context, raise_errors=True):
    if not _vrm_addon_available():
        if raise_errors:
            raise ValueError(_tr("VRM Add-on is not available. Enable the VRM Add-on before importing ARKit keys into Blend Shape Proxy."))
        return None

    active = getattr(context, "object", None)
    candidates = []
    if active is not None:
        candidates.append(active)
        if active.type == "MESH":
            candidates.extend(_object_armature_modifiers(active))

    for obj in getattr(context, "selected_objects", []):
        candidates.append(obj)
        if obj.type == "MESH":
            candidates.extend(_object_armature_modifiers(obj))

    scene = getattr(context, "scene", None)
    if scene is not None:
        candidates.extend(obj for obj in scene.objects if obj.type == "ARMATURE")

    has_vrm_armature = False
    for obj in _iter_unique_objects(candidates):
        if _armature_vrm_extension(obj) is None:
            continue
        has_vrm_armature = True
        if _is_vrm0_armature(obj):
            return obj

    if raise_errors:
        if has_vrm_armature:
            raise ValueError(_tr("The detected VRM armature is not VRM 0.0. Blend Shape Proxy is a VRM0 feature."))
        raise ValueError(_tr("No VRM0 armature found. Select a mesh bound to a VRM0 armature or keep the VRM0 armature in the scene."))
    return None


def _mesh_has_shape_keys(obj):
    return obj is not None and obj.type == "MESH" and obj.data.shape_keys is not None


def _mesh_uses_armature(obj, armature):
    if obj.parent == armature:
        return True
    return any(modifier_armature == armature for modifier_armature in _object_armature_modifiers(obj))


def _collect_vrm_proxy_meshes(context, armature):
    scene = getattr(context, "scene", None)
    scene_objects = list(scene.objects) if scene is not None else list(bpy.data.objects)
    related_meshes = [
        obj
        for obj in scene_objects
        if _mesh_has_shape_keys(obj) and _mesh_uses_armature(obj, armature)
    ]
    selected_meshes = [
        obj
        for obj in getattr(context, "selected_objects", [])
        if _mesh_has_shape_keys(obj)
    ]
    active = getattr(context, "object", None)
    active_meshes = [active] if _mesh_has_shape_keys(active) else []
    meshes = list(_iter_unique_objects([*related_meshes, *selected_meshes, *active_meshes]))
    if not meshes:
        raise ValueError(_tr("No mesh with shape keys was found for the VRM0 armature."))
    return meshes


def _resolve_arkit_bind_key_name(mesh_obj, proxy_group_name):
    key_blocks = _shape_key_blocks(mesh_obj)
    if key_blocks is None:
        return None
    return _resolve_arkit_shape_key_name(key_blocks, proxy_group_name)


def _find_vrm0_blend_shape_group(blend_shape_groups, group_name):
    for index, group in enumerate(blend_shape_groups):
        if group.name == group_name:
            return index, group
    return None, None


def _get_or_create_vrm0_blend_shape_group(blend_shape_master, group_name):
    groups = blend_shape_master.blend_shape_groups
    index, group = _find_vrm0_blend_shape_group(groups, group_name)
    if group is not None:
        return index, group, "existing"

    alternate_name = _first_letter_case_variant(group_name)
    index, group = _find_vrm0_blend_shape_group(groups, alternate_name)
    if group is not None:
        group.name = group_name
        blend_shape_master.active_blend_shape_group_index = index
        return index, group, "renamed"

    group = groups.add()
    group.name = group_name
    try:
        group.preset_name = "unknown"
    except Exception:
        pass
    index = len(groups) - 1
    blend_shape_master.active_blend_shape_group_index = index
    return index, group, "added"


def _has_vrm0_bind_for_key(blend_shape_group, mesh_name, shape_key_name):
    acceptable_key_names = {shape_key_name, _first_letter_case_variant(shape_key_name)}
    for bind in blend_shape_group.binds:
        if bind.mesh.mesh_object_name == mesh_name and bind.index in acceptable_key_names:
            return True
    return False


def _has_related_vrm0_bind(blend_shape_group, mesh_name, proxy_group_name):
    return _has_vrm0_bind_for_key(blend_shape_group, mesh_name, proxy_group_name)


def import_arkit_shape_keys_to_vrm0_proxy(context, key_case):
    armature = _find_vrm0_armature(context, raise_errors=True)
    ext = armature.data.vrm_addon_extension
    blend_shape_master = ext.vrm0.blend_shape_master
    meshes = _collect_vrm_proxy_meshes(context, armature)
    proxy_group_names = arkit_shape_key_names_for_vrm_proxy(key_case)

    bind_plan = {}
    for proxy_group_name in proxy_group_names:
        binds = []
        for mesh_obj in meshes:
            bind_key_name = _resolve_arkit_bind_key_name(mesh_obj, proxy_group_name)
            if bind_key_name:
                binds.append((mesh_obj, bind_key_name))
        bind_plan[proxy_group_name] = binds

    if not any(bind_plan.values()):
        raise ValueError(_tr("No ARKit 52 shape keys were found on the selected or VRM0-bound meshes."))

    result = {
        "case": key_case,
        "armature": armature.name,
        "mesh_count": len(meshes),
        "total_groups": len(proxy_group_names),
        "groups_added": 0,
        "groups_existing": 0,
        "groups_renamed": 0,
        "binds_added": 0,
        "binds_existing": 0,
        "groups_without_binds": [],
    }

    for proxy_group_name in proxy_group_names:
        _index, group, group_status = _get_or_create_vrm0_blend_shape_group(
            blend_shape_master,
            proxy_group_name,
        )
        if group_status == "added":
            result["groups_added"] += 1
        elif group_status == "renamed":
            result["groups_renamed"] += 1
        else:
            result["groups_existing"] += 1

        if not bind_plan[proxy_group_name]:
            result["groups_without_binds"].append(proxy_group_name)
            continue

        for mesh_obj, bind_key_name in bind_plan[proxy_group_name]:
            if _has_related_vrm0_bind(group, mesh_obj.name, proxy_group_name):
                result["binds_existing"] += 1
                continue
            bind = group.binds.add()
            bind.mesh.mesh_object_name = mesh_obj.name
            bind.index = bind_key_name
            bind.weight = 1.0
            group.active_bind_index = len(group.binds) - 1
            result["binds_added"] += 1

    return result


def _find_vrm0_default_blend_shape_group(blend_shape_groups, preset_name, display_name):
    for index, group in enumerate(blend_shape_groups):
        if group.preset_name == preset_name:
            return index, group
    for index, group in enumerate(blend_shape_groups):
        if group.name == display_name:
            return index, group
    return None, None


def _get_or_create_vrm0_default_blend_shape_group(blend_shape_master, mapping):
    groups = blend_shape_master.blend_shape_groups
    index, group = _find_vrm0_default_blend_shape_group(
        groups,
        mapping["preset"],
        mapping["name"],
    )
    if group is not None:
        group.name = mapping["name"]
        group.preset_name = mapping["preset"]
        blend_shape_master.active_blend_shape_group_index = index
        return index, group, "existing"

    group = groups.add()
    group.name = mapping["name"]
    group.preset_name = mapping["preset"]
    index = len(groups) - 1
    blend_shape_master.active_blend_shape_group_index = index
    return index, group, "added"


def adapt_arkit_shape_keys_to_vrm0_default_expressions(context):
    armature = _find_vrm0_armature(context, raise_errors=True)
    ext = armature.data.vrm_addon_extension
    blend_shape_master = ext.vrm0.blend_shape_master
    meshes = _collect_vrm_proxy_meshes(context, armature)

    bind_plan = {}
    for mapping in VRM0_DEFAULT_EXPRESSION_MAPPINGS:
        binds = []
        for shape_key_name in mapping["keys"]:
            for mesh_obj in meshes:
                bind_key_name = _resolve_arkit_bind_key_name(mesh_obj, shape_key_name)
                if bind_key_name:
                    binds.append((mesh_obj, bind_key_name))
        bind_plan[mapping["name"]] = binds

    if not any(bind_plan.values()):
        raise ValueError(_tr("No ARKit 52 shape keys were found on the selected or VRM0-bound meshes."))

    result = {
        "armature": armature.name,
        "mesh_count": len(meshes),
        "total_groups": len(VRM0_DEFAULT_EXPRESSION_MAPPINGS),
        "groups_added": 0,
        "groups_existing": 0,
        "binds_added": 0,
        "binds_existing": 0,
        "groups_without_binds": [],
    }

    for mapping in VRM0_DEFAULT_EXPRESSION_MAPPINGS:
        _index, group, group_status = _get_or_create_vrm0_default_blend_shape_group(
            blend_shape_master,
            mapping,
        )
        if group_status == "added":
            result["groups_added"] += 1
        else:
            result["groups_existing"] += 1

        if not bind_plan[mapping["name"]]:
            result["groups_without_binds"].append(mapping["name"])
            continue

        for mesh_obj, bind_key_name in bind_plan[mapping["name"]]:
            if _has_vrm0_bind_for_key(group, mesh_obj.name, bind_key_name):
                result["binds_existing"] += 1
                continue
            bind = group.binds.add()
            bind.mesh.mesh_object_name = mesh_obj.name
            bind.index = bind_key_name
            bind.weight = 1.0
            group.active_bind_index = len(group.binds) - 1
            result["binds_added"] += 1

    return result


def _default_expression_arkit_bind_names(mapping):
    bind_names = set()
    for shape_key_name in mapping["keys"]:
        bind_names.update(_arkit_shape_key_name_candidates(shape_key_name))
    return bind_names


def cancel_arkit_shape_keys_from_vrm0_default_expressions(context):
    armature = _find_vrm0_armature(context, raise_errors=True)
    ext = armature.data.vrm_addon_extension
    blend_shape_groups = ext.vrm0.blend_shape_master.blend_shape_groups

    result = {
        "armature": armature.name,
        "groups_checked": 0,
        "groups_missing": [],
        "binds_removed": 0,
        "binds_kept": 0,
    }

    for mapping in VRM0_DEFAULT_EXPRESSION_MAPPINGS:
        _index, group = _find_vrm0_default_blend_shape_group(
            blend_shape_groups,
            mapping["preset"],
            mapping["name"],
        )
        if group is None:
            result["groups_missing"].append(mapping["name"])
            continue

        result["groups_checked"] += 1
        arkit_bind_names = _default_expression_arkit_bind_names(mapping)
        for bind_index in reversed(range(len(group.binds))):
            bind = group.binds[bind_index]
            if bind.index in arkit_bind_names:
                group.binds.remove(bind_index)
                result["binds_removed"] += 1
            else:
                result["binds_kept"] += 1

        if len(group.binds) <= group.active_bind_index:
            group.active_bind_index = max(len(group.binds) - 1, 0)

    return result


def _vrm0_proxy_context_ready(context):
    return _find_vrm0_armature(context, raise_errors=False) is not None
