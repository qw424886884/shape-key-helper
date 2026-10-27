# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty

from .arkit_tools import (
    add_missing_arkit_shape_keys,
    convert_arkit_shape_key_names,
    repair_arkit_shape_key_symmetry,
)
from .constants import VRM_PROXY_CASE_ITEMS
from .i18n import _tr
from .modifier_tools import apply_modifier_keep_shape_keys
from .shape_key_core import (
    _base_key_source_target_error,
    _base_shape_key_name,
    _is_basis_shape_key_name,
    _open_base_shape_settings_on_error,
    _shape_key_blocks,
    analyze_shape_key_mirror,
    batch_mirror_shape_keys,
    plan_batch_shape_keys,
    infer_opposite_shape_key_name,
    mirror_shape_key_to_target,
    repair_active_shape_key_self_symmetry,
    repair_mesh_symmetry,
    reset_shape_key_to_basis,
)
from .vrm_tools import (
    adapt_arkit_shape_keys_to_vrm0_default_expressions,
    cancel_arkit_shape_keys_from_vrm0_default_expressions,
    import_arkit_shape_keys_to_vrm0_proxy,
)


def _scene_base_shape_key_name(context):
    return _base_shape_key_name(getattr(getattr(context, "scene", None), "shape_key_mirror_base", ""))


def _active_source_name(context):
    obj = context.object
    if obj is None or obj.type != "MESH":
        raise ValueError("Select a mesh object.")
    key_blocks = _shape_key_blocks(obj)
    if key_blocks is None or obj.active_shape_key is None:
        raise ValueError("Selected mesh has no active shape key.")
    base_shape_key_name = _scene_base_shape_key_name(context)
    source_name = obj.active_shape_key.name
    if _is_basis_shape_key_name(key_blocks, source_name, base_shape_key_name):
        raise _base_key_source_target_error(base_shape_key_name)
    return source_name


def resolve_mirror_shape_key_names(context):
    scene = context.scene
    mode = getattr(scene, "shape_key_mirror_mode", "AUTO")
    base_shape_key_name = _scene_base_shape_key_name(context)

    if mode == "MANUAL":
        source_name = getattr(scene, "shape_key_mirror_source", "").strip()
        target_name = getattr(scene, "shape_key_mirror_target", "").strip()
        if not source_name or not target_name:
            raise ValueError(_tr("Manual mode needs both source and target shape keys."))
        key_blocks = _shape_key_blocks(context.object)
        if key_blocks is not None and (
            _is_basis_shape_key_name(key_blocks, source_name, base_shape_key_name)
            or _is_basis_shape_key_name(key_blocks, target_name, base_shape_key_name)
        ):
            raise _base_key_source_target_error(base_shape_key_name)
        if source_name == target_name:
            raise ValueError(_tr("Source and target shape keys cannot be the same."))
        return source_name, target_name

    source_name = _active_source_name(context)
    target_name = infer_opposite_shape_key_name(source_name)
    if not target_name:
        raise ValueError(_tr("Cannot infer opposite shape key for: {name}", name=source_name))
    return source_name, target_name


class OBJECT_OT_shape_key_mirror_active(bpy.types.Operator):
    """Mirror the active or manually selected source key into the target key on the active mesh."""

    bl_idname = "shape_key_mirror.active"
    bl_label = "Mirror Active Shape Key"
    bl_description = "Mirror the resolved source shape key into the target shape key. Does not create, delete, or rename shape keys."
    bl_options = {"REGISTER", "UNDO"}

    tolerance: FloatProperty(
        name="Vertex Match Tolerance (%)",
        description="Larger values tolerate more asymmetry but may mismatch vertices. Smaller values are stricter.",
        default=0.5,
        min=0.0,
        max=5.0,
        soft_max=2.0,
    )

    def execute(self, context):
        try:
            obj = context.object
            source_name, target_name = resolve_mirror_shape_key_names(context)
            base_shape_key_name = _scene_base_shape_key_name(context)

            result = mirror_shape_key_to_target(
                obj,
                source_name,
                target_name,
                self.tolerance,
                base_shape_key_name,
            )
        except ValueError as exc:
            _open_base_shape_settings_on_error(context, exc)
            message = str(exc)
            self.report({"WARNING"} if message.startswith(_tr("Mesh is asymmetric; mirror cancelled.").split(".")[0]) else {"ERROR"}, message)
            return {"CANCELLED"}

        self.report(
            {"INFO"},
            f"{obj.name}: {source_name} -> {target_name}, written {result['written']}, unmatched {result['unmatched']}",
        )
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_batch_keys(bpy.types.Operator):
    """Mirror all keys from one named side on the active mesh."""
    bl_idname = "shape_key_mirror.batch_keys"
    bl_label = "Batch Mirror Shape Keys"
    bl_description = "Mirror same-side shape keys on the active mesh and create missing opposite keys. Existing targets are preserved unless overwrite is enabled."
    bl_options = {"REGISTER", "UNDO"}
    tolerance: FloatProperty(name="Vertex Match Tolerance (%)", default=0.5, min=0.0, max=5.0)
    overwrite_existing: BoolProperty(name="Overwrite Existing Opposite Keys", default=False)

    def source_name(self, context):
        if getattr(context.scene, "shape_key_mirror_mode", "AUTO") == "MANUAL":
            name = context.scene.shape_key_mirror_source.strip()
            if name:
                return name
        return _active_source_name(context)

    def invoke(self, context, event):
        try:
            plan_batch_shape_keys(context.object, self.source_name(context), _scene_base_shape_key_name(context))
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self, width=440)

    def draw(self, context):
        plan = plan_batch_shape_keys(context.object, self.source_name(context), _scene_base_shape_key_name(context))
        self.layout.label(text=_tr("Right to Left") if plan["side"] == "RIGHT" else _tr("Left to Right"))
        self.layout.label(text=_tr("Current mesh: {count} source keys", count=len(plan["pairs"])))
        self.layout.label(text=_tr("Existing opposite keys: {count}", count=len(plan["existing"])))
        self.layout.prop(self, "overwrite_existing")

    def execute(self, context):
        try:
            result = batch_mirror_shape_keys(context.object, self.source_name(context), self.tolerance,
                                            _scene_base_shape_key_name(context), self.overwrite_existing)
        except ValueError as exc:
            _open_base_shape_settings_on_error(context, exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, _tr("Mirrored {count} shape keys; created {created}; skipped {skipped}.",
                    count=len(result["mirrored"]), created=len(result["created"]), skipped=len(result["skipped"])))
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_selected_meshes(bpy.types.Operator):
    """Mirror the resolved source key name into the target key on every selected mesh."""

    bl_idname = "shape_key_mirror.selected_meshes"
    bl_label = "Mirror Pair Across Selected Meshes"
    bl_description = "Apply the current source -> target direction to selected mesh objects. Each mesh must contain matching source and target shape keys."
    bl_options = {"REGISTER", "UNDO"}

    tolerance: FloatProperty(
        name="Vertex Match Tolerance (%)",
        description="Larger values tolerate more asymmetry but may mismatch vertices. Smaller values are stricter.",
        default=0.5,
        min=0.0,
        max=5.0,
        soft_max=2.0,
    )

    def execute(self, context):
        try:
            active_obj = context.object
            source_name, target_name = resolve_mirror_shape_key_names(context)
            base_shape_key_name = _scene_base_shape_key_name(context)
        except ValueError as exc:
            _open_base_shape_settings_on_error(context, exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        selected_meshes = [
            obj
            for obj in context.selected_objects
            if obj.type == "MESH" and obj.data.shape_keys is not None
        ]
        if active_obj not in selected_meshes:
            selected_meshes.append(active_obj)

        skipped = []
        ready = []
        for obj in selected_meshes:
            key_blocks = _shape_key_blocks(obj)
            if key_blocks is None or source_name not in key_blocks or target_name not in key_blocks:
                skipped.append(obj.name)
                continue
            try:
                result = analyze_shape_key_mirror(obj, source_name, target_name, self.tolerance, base_shape_key_name)
                if result["unmatched"]:
                    raise ValueError(_tr(
                        "Mesh is asymmetric; mirror cancelled. Unmatched vertices: {count}. Try a larger tolerance or fix mesh symmetry first. Current tolerance: {percent:.2f}% ({distance:.6f}), max deviation: {max_distance:.6f}.",
                        count=result["unmatched"],
                        percent=result["tolerance_percent"],
                        distance=result["tolerance_distance"],
                        max_distance=result["max_pair_distance"],
                    )
                    )
                ready.append(obj)
            except ValueError as exc:
                _open_base_shape_settings_on_error(context, exc)
                self.report({"WARNING"}, f"{obj.name}: {exc}")
                return {"CANCELLED"}

        if not ready:
            self.report({"ERROR"}, f"No selected mesh has both {source_name} and {target_name}.")
            return {"CANCELLED"}

        finished = []
        for obj in ready:
            result = mirror_shape_key_to_target(obj, source_name, target_name, self.tolerance, base_shape_key_name)
            finished.append((obj.name, result["written"], result["unmatched"]))

        detail = ", ".join(f"{name}:{written}/{unmatched}" for name, written, unmatched in finished)
        if skipped:
            detail += "; skipped " + ", ".join(skipped)
        self.report({"INFO"}, f"{source_name} -> {target_name}: {detail}")
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_reset_active(bpy.types.Operator):
    """Reset the active shape key back to base shape coordinates."""

    bl_idname = "shape_key_mirror.reset_active"
    bl_label = "Reset Active Shape Key"
    bl_description = "Copy base shape coordinates into the active shape key. This clears the current key without changing the base shape or other shape keys."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            obj = context.object
            if obj is None or obj.type != "MESH":
                raise ValueError("Select a mesh object.")
            if obj.data.shape_keys is None or obj.active_shape_key is None:
                raise ValueError("Selected mesh has no active shape key.")
            shape_key_name = obj.active_shape_key.name
            result = reset_shape_key_to_basis(obj, shape_key_name, _scene_base_shape_key_name(context))
        except ValueError as exc:
            _open_base_shape_settings_on_error(context, exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report({"INFO"}, f"{obj.name}: reset {result['shape_key']} to base shape, vertices {result['reset']}")
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_repair_mesh_symmetry(bpy.types.Operator):
    """Center and repair the selected mesh's geometric symmetry without changing UVs."""

    bl_idname = "shape_key_mirror.repair_mesh_symmetry"
    bl_label = "Repair Model Symmetry"
    bl_description = "Center and symmetrize the mesh data without deleting vertices, changing topology, or touching UVs. Shape key deltas are preserved."
    bl_options = {"REGISTER", "UNDO"}

    tolerance: FloatProperty(
        name="Vertex Match Tolerance (%)",
        description="Larger values tolerate more asymmetry but may mismatch vertices. Smaller values are stricter.",
        default=0.5,
        min=0.0,
        max=5.0,
        soft_max=2.0,
    )

    def execute(self, context):
        try:
            obj = context.object
            result = repair_mesh_symmetry(
                obj,
                tolerance_percent=self.tolerance,
                base_shape_key_name=_scene_base_shape_key_name(context),
            )
        except ValueError as exc:
            _open_base_shape_settings_on_error(context, exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report({"INFO"}, _tr(
            "Repaired model symmetry on {name}: {changed}/{total} vertices, X shift {shift:.6f}, preserved {keys} shape keys",
            name=obj.name,
            changed=result["changed_vertices"],
            total=result["vertices"],
            shift=result["center_shift_x"],
            keys=result["shape_keys_adjusted"],
        ))
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_repair_active_self_symmetry(bpy.types.Operator):
    """Repair the active shape key against itself."""

    bl_idname = "shape_key_mirror.repair_active_self_symmetry"
    bl_label = "Repair Active Key Symmetry"
    bl_description = "Repair the active shape key against itself. If only one side was edited, the edited side is mirrored to the untouched side."
    bl_options = {"REGISTER", "UNDO"}

    tolerance: FloatProperty(
        name="Vertex Match Tolerance (%)",
        description="Larger values tolerate more asymmetry but may mismatch vertices. Smaller values are stricter.",
        default=0.5,
        min=0.0,
        max=5.0,
        soft_max=2.0,
    )

    def execute(self, context):
        try:
            obj = context.object
            if obj is None or obj.type != "MESH":
                raise ValueError(_tr("Select a mesh object."))
            if obj.data.shape_keys is None or obj.active_shape_key is None:
                raise ValueError(_tr("Selected mesh has no active shape key."))
            result = repair_active_shape_key_self_symmetry(
                obj,
                obj.active_shape_key.name,
                tolerance_percent=self.tolerance,
                base_shape_key_name=_scene_base_shape_key_name(context),
            )
        except ValueError as exc:
            _open_base_shape_settings_on_error(context, exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report({"INFO"}, _tr(
            "Repaired symmetry for {key} on {name}: {changed} relations changed, {deviated} deviations found",
            key=result["shape_key"],
            name=obj.name,
            changed=result["changed_relations"],
            deviated=result["deviated_relations"],
        ))
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_apply_modifier_keep_shape_keys(bpy.types.Operator):
    """Apply the selected modifier while rebuilding all existing shape keys."""

    bl_idname = "shape_key_mirror.apply_modifier_keep_shape_keys"
    bl_label = "Apply Modifier Keep Shape Keys"
    bl_description = "Apply the selected modifier while rebuilding all existing shape keys. Other modifiers are temporarily disabled to avoid double application."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            obj = context.object
            result = apply_modifier_keep_shape_keys(
                context,
                obj,
                context.scene.shape_key_mirror_modifier,
            )
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        if result["applied_with_shape_keys"]:
            self.report({"INFO"}, _tr(
                "Applied modifier {modifier} on {name}, preserved {keys} shape keys and {vertices} vertices",
                modifier=result["modifier"],
                name=obj.name,
                keys=result["shape_keys"],
                vertices=result["vertices"],
            ))
        else:
            self.report({"INFO"}, _tr(
                "Applied modifier {modifier} on {name}; no shape keys were present",
                modifier=result["modifier"],
                name=obj.name,
            ))
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_add_arkit_keys(bpy.types.Operator):
    """Add missing ARKit shape keys to the active mesh or curve."""

    bl_idname = "shape_key_mirror.add_arkit_keys"
    bl_label = "Add ARKit Keys"
    bl_description = "Add missing ARKit 52 shape keys to the active object. Existing keys are kept and not duplicated."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            result = add_missing_arkit_shape_keys(context.object)
        except ValueError as exc:
            _open_base_shape_settings_on_error(context, exc)
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        self.report({"INFO"}, f"ARKit keys: added {result['added']}, existing {result['skipped']}")
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_convert_arkit_names(bpy.types.Operator):
    """Toggle ARKit shape key names between Left/Right and _L/_R style."""

    bl_idname = "shape_key_mirror.convert_arkit_names"
    bl_label = "Convert Naming"
    bl_description = "Toggle ARKit names between Left/Right and _L/_R style. Directional names such as MouthLeft are kept."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        to_symmetrical = getattr(scene, "shape_key_mirror_arkit_to_symmetrical", True)
        try:
            result = convert_arkit_shape_key_names(context.object, to_symmetrical=to_symmetrical)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        scene.shape_key_mirror_arkit_to_symmetrical = not to_symmetrical
        direction = "Left/Right -> _L/_R" if to_symmetrical else "_L/_R -> Left/Right"
        self.report({"INFO"}, f"{direction}: renamed {result['renamed']}, skipped {result['skipped']}")
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_repair_arkit_symmetry(bpy.types.Operator):
    """Repair symmetry drift across the existing ARKit 52 shape keys."""

    bl_idname = "shape_key_mirror.repair_arkit_symmetry"
    bl_label = "Repair 52 Symmetry"
    bl_description = "Repair symmetry drift across the existing ARKit 52 shape keys. Does not add, delete, or rename shape keys."
    bl_options = {"REGISTER", "UNDO"}

    tolerance: FloatProperty(
        name="Vertex Match Tolerance (%)",
        description="Larger values tolerate more asymmetry but may mismatch vertices. Smaller values are stricter.",
        default=0.5,
        min=0.0,
        max=5.0,
        soft_max=2.0,
    )

    def execute(self, context):
        try:
            obj = context.object
            result = repair_arkit_shape_key_symmetry(
                obj,
                tolerance_percent=self.tolerance,
                base_shape_key_name=_scene_base_shape_key_name(context),
            )
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        missing_count = len(result["missing_keys"])
        level = {"WARNING"} if missing_count else {"INFO"}
        self.report(level, _tr(
            "Repaired ARKit symmetry on {name}: checked {checked}/52 keys, repaired {groups} groups and {relations} relations, {missing} keys missing",
            name=obj.name,
            checked=result["shape_keys_checked"],
            groups=result["shape_key_groups_repaired"],
            relations=result["changed_relations"],
            missing=missing_count,
        ))
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_adapt_default_vrm_expressions(bpy.types.Operator):
    """Bind ARKit 52 shape keys to VRM0 default proxy expressions."""

    bl_idname = "shape_key_mirror.adapt_default_vrm_expressions"
    bl_label = "Adapt Default Expressions"
    bl_description = "Bind the existing ARKit 52 shape keys to VRM0 default Blend Shape Proxy expressions."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            result = adapt_arkit_shape_keys_to_vrm0_default_expressions(context)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        missing_count = len(result["groups_without_binds"])
        level = {"WARNING"} if missing_count > 1 else {"INFO"}
        self.report(level, _tr(
            "Adapted VRM0 default expressions: {groups} groups added, {added} binds added, {existing} binds kept, {missing} groups missing",
            groups=result["groups_added"],
            added=result["binds_added"],
            existing=result["binds_existing"],
            missing=missing_count,
        ))
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_cancel_default_vrm_adaptation(bpy.types.Operator):
    """Remove ARKit 52 binds from VRM0 default proxy expressions."""

    bl_idname = "shape_key_mirror.cancel_default_vrm_adaptation"
    bl_label = "Cancel Default Adaptation"
    bl_description = "Remove ARKit 52 binds from VRM0 default Blend Shape Proxy expressions while keeping the default groups."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            result = cancel_arkit_shape_keys_from_vrm0_default_expressions(context)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        missing_count = len(result["groups_missing"])
        level = {"WARNING"} if missing_count else {"INFO"}
        self.report(level, _tr(
            "Removed VRM0 default adaptation: {removed} binds removed, {kept} other binds kept, {missing} groups missing",
            removed=result["binds_removed"],
            kept=result["binds_kept"],
            missing=missing_count,
        ))
        return {"FINISHED"}


class OBJECT_OT_shape_key_mirror_import_arkit_to_vrm_proxy(bpy.types.Operator):
    """Import ARKit 52 proxy groups into a VRM0 Blend Shape Proxy."""

    bl_idname = "shape_key_mirror.import_arkit_to_vrm_proxy"
    bl_label = "Import to VRM Proxy"
    bl_description = "Import ARKit 52 keys into the VRM0 Blend Shape Proxy. Existing ARKit proxy groups are reused or renamed without duplicate binds."
    bl_options = {"REGISTER", "UNDO"}

    key_case: EnumProperty(
        name="ARKit Proxy Name Case",
        items=VRM_PROXY_CASE_ITEMS,
        default="UPPER",
        options={"HIDDEN"},
    )

    def execute(self, context):
        try:
            result = import_arkit_shape_keys_to_vrm0_proxy(context, self.key_case)
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        case_label = _tr("Title Case") if self.key_case == "UPPER" else _tr("Lower Camel Case")
        missing_count = len(result["groups_without_binds"])
        level = {"WARNING"} if missing_count else {"INFO"}
        self.report(level, _tr(
            "Imported ARKit keys to VRM proxy ({case}): {groups} groups added, {renamed} renamed, {added} binds added, {existing} binds kept, {missing} groups without binds",
            case=case_label,
            groups=result["groups_added"],
            renamed=result["groups_renamed"],
            added=result["binds_added"],
            existing=result["binds_existing"],
            missing=missing_count,
        ))
        return {"FINISHED"}
