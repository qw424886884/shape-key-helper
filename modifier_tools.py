# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .i18n import _tr


def _safe_shape_key_attr(key_block, attr_name, default=None):
    return getattr(key_block, attr_name, default)


def _id_property_to_python(value):
    if hasattr(value, "to_dict"):
        return {key: _id_property_to_python(item) for key, item in value.to_dict().items()}
    if hasattr(value, "to_list"):
        return [_id_property_to_python(item) for item in value.to_list()]
    if isinstance(value, dict):
        return {key: _id_property_to_python(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_id_property_to_python(item) for item in value]
    return value


def _capture_id_properties(owner):
    try:
        return {key: _id_property_to_python(value) for key, value in owner.items()}
    except Exception:
        return {}


def _restore_id_properties(owner, properties):
    for key, value in properties.items():
        try:
            owner[key] = value
        except Exception:
            pass


def _shape_key_metadata(key_block):
    relative_key = _safe_shape_key_attr(key_block, "relative_key")
    return {
        "name": key_block.name,
        "value": _safe_shape_key_attr(key_block, "value", 0.0),
        "mute": _safe_shape_key_attr(key_block, "mute", False),
        "slider_min": _safe_shape_key_attr(key_block, "slider_min", 0.0),
        "slider_max": _safe_shape_key_attr(key_block, "slider_max", 1.0),
        "vertex_group": _safe_shape_key_attr(key_block, "vertex_group", ""),
        "interpolation": _safe_shape_key_attr(key_block, "interpolation", "KEY_LINEAR"),
        "frame": _safe_shape_key_attr(key_block, "frame", 0.0),
        "relative_key": getattr(relative_key, "name", None),
        "id_properties": _capture_id_properties(key_block),
    }


def _restore_shape_key_metadata(key_block, metadata, restore_value=True):
    for attr_name in ("slider_min", "slider_max", "mute", "vertex_group", "interpolation", "frame"):
        try:
            setattr(key_block, attr_name, metadata[attr_name])
        except Exception:
            pass
    if restore_value:
        try:
            key_block.value = metadata["value"]
        except Exception:
            pass
    _restore_id_properties(key_block, metadata.get("id_properties", {}))


def _set_shape_key_chain_active(key_blocks, active_key=None):
    for key_block in key_blocks:
        if hasattr(key_block, "value"):
            key_block.value = 0.0
        if hasattr(key_block, "mute"):
            key_block.mute = False
        if hasattr(key_block, "vertex_group"):
            key_block.vertex_group = ""

    if active_key is None:
        return

    basis_key = next(iter(key_blocks))
    visited = set()
    current_key = active_key
    while current_key is not None and current_key != basis_key and current_key.name not in visited:
        visited.add(current_key.name)
        if hasattr(current_key, "value"):
            current_key.value = 1.0
        current_key = getattr(current_key, "relative_key", None)


def _capture_rna_scalar_state(owner, skip=()):
    state = {}
    skip = set(skip)
    for prop in owner.bl_rna.properties:
        identifier = prop.identifier
        if identifier == "rna_type" or identifier in skip or prop.is_readonly:
            continue
        if prop.type not in {"BOOLEAN", "INT", "FLOAT", "STRING", "ENUM"}:
            continue
        try:
            value = getattr(owner, identifier)
            state[identifier] = tuple(value) if prop.is_array else value
        except Exception:
            pass
    return state


def _restore_rna_scalar_state(owner, state):
    for identifier, value in state.items():
        try:
            setattr(owner, identifier, value)
        except Exception:
            pass


def _capture_driver_target(target):
    return {
        "id": target.id,
        "id_type": target.id_type,
        "state": _capture_rna_scalar_state(target, skip={"id_type"}),
    }


def _restore_driver_target(target, state, old_shape_keys, new_shape_keys):
    try:
        target.id_type = state["id_type"]
    except Exception:
        pass
    target_id = state["id"]
    if target_id == old_shape_keys:
        target_id = new_shape_keys
    try:
        target.id = target_id
    except Exception:
        pass
    _restore_rna_scalar_state(target, state["state"])


def _capture_driver_fcurve(fcurve):
    return {
        "data_path": fcurve.data_path,
        "array_index": fcurve.array_index,
        "fcurve_state": _capture_rna_scalar_state(fcurve, skip={"data_path", "array_index"}),
        "driver_state": {
            "type": fcurve.driver.type,
            "expression": fcurve.driver.expression,
            "use_self": fcurve.driver.use_self,
        },
        "variables": [
            {
                "name": variable.name,
                "type": variable.type,
                "targets": [_capture_driver_target(target) for target in variable.targets],
            }
            for variable in fcurve.driver.variables
        ],
        "modifiers": [
            {
                "type": modifier.type,
                "state": _capture_rna_scalar_state(modifier, skip={"type"}),
            }
            for modifier in fcurve.modifiers
        ],
    }


def _driver_add_fcurve(owner, data_path, array_index):
    try:
        result = owner.driver_add(data_path, array_index)
    except (TypeError, ValueError):
        result = owner.driver_add(data_path)
    if isinstance(result, (list, tuple)):
        return result[array_index if array_index < len(result) else 0]
    return result


def _restore_driver_fcurves(new_shape_keys, driver_states, old_shape_keys):
    for state in driver_states:
        fcurve = _driver_add_fcurve(new_shape_keys, state["data_path"], state["array_index"])
        _restore_rna_scalar_state(fcurve, state["fcurve_state"])

        for variable in list(fcurve.driver.variables):
            fcurve.driver.variables.remove(variable)
        for variable_state in state["variables"]:
            variable = fcurve.driver.variables.new()
            variable.name = variable_state["name"]
            variable.type = variable_state["type"]
            for target, target_state in zip(variable.targets, variable_state["targets"]):
                _restore_driver_target(target, target_state, old_shape_keys, new_shape_keys)
        fcurve.driver.type = state["driver_state"]["type"]
        fcurve.driver.use_self = state["driver_state"]["use_self"]
        fcurve.driver.expression = state["driver_state"]["expression"]

        for modifier in list(fcurve.modifiers):
            fcurve.modifiers.remove(modifier)
        for modifier_state in state["modifiers"]:
            modifier = fcurve.modifiers.new(type=modifier_state["type"])
            _restore_rna_scalar_state(modifier, modifier_state["state"])


def _capture_shape_key_animation(shape_keys):
    animation_data = shape_keys.animation_data
    if animation_data is None:
        return {
            "action": None,
            "action_slot": None,
            "animation_state": {},
            "drivers": [],
            "driver_mutes": [],
        }
    if len(animation_data.nla_tracks) > 0:
        raise ValueError(_tr("Shape key NLA tracks are not supported yet. Remove or bake the NLA tracks before applying a modifier."))
    return {
        "action": animation_data.action,
        "action_slot": getattr(animation_data, "action_slot", None),
        "animation_state": _capture_rna_scalar_state(
            animation_data,
            skip={"action_slot_handle", "action_slot_handle_tweak_storage", "last_slot_identifier"},
        ),
        "drivers": [_capture_driver_fcurve(fcurve) for fcurve in animation_data.drivers],
        "driver_mutes": [fcurve.mute for fcurve in animation_data.drivers],
    }


def _suspend_shape_key_animation(shape_keys, animation_state):
    animation_data = shape_keys.animation_data
    if animation_data is None:
        return
    animation_data.action = None
    for fcurve in animation_data.drivers:
        fcurve.mute = True


def _resume_shape_key_animation(shape_keys, animation_state):
    animation_data = shape_keys.animation_data
    if animation_data is None:
        return
    animation_data.action = animation_state["action"]
    action_slot = animation_state.get("action_slot")
    if action_slot is not None:
        try:
            animation_data.action_slot = action_slot
        except Exception:
            pass
    for fcurve, mute in zip(animation_data.drivers, animation_state["driver_mutes"]):
        fcurve.mute = mute


def _restore_shape_key_animation(new_shape_keys, animation_state, old_shape_keys):
    if animation_state["action"] is None and not animation_state["drivers"]:
        return
    animation_data = new_shape_keys.animation_data_create()
    animation_data.action = animation_state["action"]
    action_slot = animation_state.get("action_slot")
    if action_slot is not None:
        try:
            animation_data.action_slot = action_slot
        except Exception:
            pass
    _restore_rna_scalar_state(animation_data, animation_state["animation_state"])
    _restore_driver_fcurves(new_shape_keys, animation_state["drivers"], old_shape_keys)


def _evaluated_mesh_from_current_shape(context, obj, mesh_name):
    context.view_layer.update()
    depsgraph = context.evaluated_depsgraph_get()
    evaluated_obj = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(
        evaluated_obj,
        depsgraph=depsgraph,
        preserve_all_data_layers=True,
    )
    mesh.name = mesh_name
    return mesh


def _make_active_object(context, obj):
    try:
        if context.object is not obj:
            context.view_layer.objects.active = obj
        obj.select_set(True)
    except Exception:
        pass


def _apply_modifier_without_shape_keys(context, obj, modifier_name):
    _make_active_object(context, obj)
    if getattr(context, "mode", "OBJECT") != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.modifier_apply(modifier=modifier_name)
    return {
        "modifier": modifier_name,
        "shape_keys": 0,
        "vertices": len(obj.data.vertices),
        "applied_with_shape_keys": False,
        "temporarily_disabled_modifiers": 0,
    }


def apply_modifier_keep_shape_keys(context, obj, modifier_name):
    """Apply one modifier while rebuilding existing shape keys on the active mesh."""
    if obj is None or obj.type != "MESH":
        raise ValueError(_tr("Select a mesh object."))

    modifier_name = str(modifier_name or "").strip()
    if not modifier_name:
        raise ValueError(_tr("Select a modifier first."))

    target_modifier = obj.modifiers.get(modifier_name)
    if target_modifier is None:
        raise ValueError(_tr("Selected modifier not found: {name}", name=modifier_name))

    if obj.data.shape_keys is None or len(obj.data.shape_keys.key_blocks) == 0:
        return _apply_modifier_without_shape_keys(context, obj, modifier_name)

    _make_active_object(context, obj)
    if getattr(context, "mode", "OBJECT") != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    key_blocks = obj.data.shape_keys.key_blocks
    shape_key_meta = [_shape_key_metadata(key_block) for key_block in key_blocks]
    old_mesh = obj.data
    old_mesh_name = old_mesh.name
    old_shape_keys = old_mesh.shape_keys
    old_shape_key_state = {
        "name": old_shape_keys.name,
        "use_relative": old_shape_keys.use_relative,
        "eval_time": old_shape_keys.eval_time,
        "id_properties": _capture_id_properties(old_shape_keys),
        "active_index": obj.active_shape_key_index,
    }
    animation_state = _capture_shape_key_animation(old_shape_keys)

    hidden_modifiers = {}
    captured_meshes = []
    target_show_viewport = target_modifier.show_viewport
    target_modifier.show_viewport = True
    operation_succeeded = False

    try:
        for modifier in obj.modifiers:
            if modifier.name != modifier_name and modifier.show_viewport:
                hidden_modifiers[modifier.name] = True
                modifier.show_viewport = False

        _suspend_shape_key_animation(old_shape_keys, animation_state)
        try:
            expected_vertex_count = None
            for index, metadata in enumerate(shape_key_meta):
                if old_shape_key_state["use_relative"]:
                    active_key = None if index == 0 else key_blocks[metadata["name"]]
                    _set_shape_key_chain_active(key_blocks, active_key)
                else:
                    _set_shape_key_chain_active(key_blocks)
                    old_shape_keys.eval_time = metadata["frame"]

                mesh = _evaluated_mesh_from_current_shape(
                    context,
                    obj,
                    f"{old_mesh_name}_{metadata['name']}_{modifier_name}",
                )
                vertex_count = len(mesh.vertices)
                if expected_vertex_count is None:
                    expected_vertex_count = vertex_count
                elif vertex_count != expected_vertex_count:
                    bpy.data.meshes.remove(mesh)
                    raise ValueError(_tr("The modifier result changes vertex count inconsistently between shape keys. Cancelled to protect shape keys."))
                captured_meshes.append(mesh)
        finally:
            for key_block, metadata in zip(key_blocks, shape_key_meta):
                if hasattr(key_block, "value"):
                    key_block.value = metadata["value"]
                if hasattr(key_block, "mute"):
                    key_block.mute = metadata["mute"]
                if hasattr(key_block, "vertex_group"):
                    key_block.vertex_group = metadata["vertex_group"]
            old_shape_keys.eval_time = old_shape_key_state["eval_time"]
            _resume_shape_key_animation(old_shape_keys, animation_state)
            context.view_layer.update()

        basis_mesh = captured_meshes[0]
        basis_mesh.name = old_mesh_name
        obj.data = basis_mesh

        new_key_blocks = []
        for index, metadata in enumerate(shape_key_meta):
            new_key = obj.shape_key_add(name=metadata["name"], from_mix=False)
            new_key_blocks.append(new_key)
            if index == 0:
                obj.data.shape_keys.use_relative = old_shape_key_state["use_relative"]
            if index > 0:
                source_mesh = captured_meshes[index]
                for vertex_index, vertex in enumerate(source_mesh.vertices):
                    new_key.data[vertex_index].co = vertex.co

        new_shape_keys = obj.data.shape_keys
        new_shape_keys.name = old_shape_key_state["name"]
        new_shape_keys.use_relative = old_shape_key_state["use_relative"]
        new_shape_keys.eval_time = old_shape_key_state["eval_time"]
        _restore_id_properties(new_shape_keys, old_shape_key_state["id_properties"])

        for index, (new_key, metadata) in enumerate(zip(new_key_blocks, shape_key_meta)):
            _restore_shape_key_metadata(new_key, metadata, restore_value=index > 0)

        new_key_lookup = {key_block.name: key_block for key_block in new_key_blocks}
        if old_shape_key_state["use_relative"]:
            for new_key, metadata in zip(new_key_blocks, shape_key_meta):
                relative_key_name = metadata.get("relative_key")
                if relative_key_name and relative_key_name in new_key_lookup:
                    new_key.relative_key = new_key_lookup[relative_key_name]

        _restore_shape_key_animation(new_shape_keys, animation_state, old_shape_keys)
        obj.active_shape_key_index = min(old_shape_key_state["active_index"], len(new_key_blocks) - 1)

        applied_modifier = obj.modifiers.get(modifier_name)
        if applied_modifier is not None:
            obj.modifiers.remove(applied_modifier)
        obj.data.update()
        operation_succeeded = True

        remaining_meshes = [basis_mesh]
        for mesh in captured_meshes[1:]:
            if mesh.users == 0:
                try:
                    bpy.data.meshes.remove(mesh)
                    continue
                except Exception:
                    pass
            remaining_meshes.append(mesh)
        captured_meshes = remaining_meshes
        if old_mesh.users == 0:
            try:
                bpy.data.meshes.remove(old_mesh)
            except Exception:
                pass

        return {
            "modifier": modifier_name,
            "shape_keys": len(shape_key_meta),
            "vertices": len(obj.data.vertices),
            "applied_with_shape_keys": True,
            "temporarily_disabled_modifiers": len(hidden_modifiers),
        }
    except Exception as exc:
        if obj.data is not old_mesh:
            obj.data = old_mesh
        target_modifier = obj.modifiers.get(modifier_name)
        if target_modifier is not None:
            target_modifier.show_viewport = target_show_viewport
        if isinstance(exc, ValueError):
            raise
        raise ValueError(_tr("Could not apply the modifier while preserving shape keys: {error}", error=exc)) from exc
    finally:
        if not operation_succeeded:
            target_modifier = obj.modifiers.get(modifier_name)
            if target_modifier is not None:
                target_modifier.show_viewport = target_show_viewport
        for modifier_name_to_restore in hidden_modifiers:
            modifier = obj.modifiers.get(modifier_name_to_restore)
            if modifier is not None:
                modifier.show_viewport = True
        for mesh in captured_meshes:
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
