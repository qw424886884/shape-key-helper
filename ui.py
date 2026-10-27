# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from .i18n import _tr, _ui_label
from .shape_key_core import (
    _basis_shape_key,
    _is_basis_shape_key_name,
    _shape_key_blocks,
    infer_opposite_shape_key_name,
)
from .vrm_tools import _vrm0_proxy_context_ready


class DATA_PT_shape_key_mirror_master(bpy.types.Panel):
    bl_label = "Shape Key Helper"
    bl_idname = "DATA_PT_shape_key_mirror_master"
    bl_description = "Mirror and repair shape keys, fix mesh symmetry, and preserve shape keys when applying modifiers."
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_parent_id = "DATA_PT_shape_keys"

    @classmethod
    def poll(cls, context):
        obj = context.object
        return obj is not None and obj.type == "MESH"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.object
        mode = scene.shape_key_mirror_mode
        source_name = None
        target_name = None

        shape_keys = obj.data.shape_keys
        has_shape_keys = shape_keys is not None and len(shape_keys.key_blocks) > 0

        layout.label(text=_ui_label("Model Preparation"), icon="MESH_DATA")
        layout.prop(scene, "shape_key_mirror_tolerance")
        op = layout.operator(
            "shape_key_mirror.repair_mesh_symmetry",
            text=_ui_label("Repair Model Symmetry"),
            icon="MOD_MIRROR",
        )
        op.tolerance = scene.shape_key_mirror_tolerance

        if has_shape_keys:
            base_row = layout.row(align=True)
            base_row.prop(
                scene,
                "shape_key_mirror_show_base_settings",
                text=_tr("Base Shape Settings"),
                icon="TRIA_DOWN" if scene.shape_key_mirror_show_base_settings else "TRIA_RIGHT",
                emboss=False,
            )
            if scene.shape_key_mirror_show_base_settings:
                base_col = layout.column(align=True)
                base_col.prop_search(
                    scene,
                    "shape_key_mirror_base",
                    shape_keys,
                    "key_blocks",
                    text=_tr("Base Shape"),
                )
                if scene.shape_key_mirror_base:
                    base_col.label(text=_tr("Base: {name}", name=scene.shape_key_mirror_base))
                else:
                    auto_base = _basis_shape_key(_shape_key_blocks(obj))
                    if auto_base is not None:
                        base_col.label(text=_tr("Base: Auto ({name})", name=auto_base.name))

        layout.separator()

        mirror_col = layout.column(align=True)
        row = mirror_col.row()
        row.prop(
            scene,
            "shape_key_mirror_show_mirror_tools",
            text=_ui_label("Shape Key Operations"),
            icon="TRIA_DOWN" if scene.shape_key_mirror_show_mirror_tools else "TRIA_RIGHT",
            emboss=False,
        )
        if scene.shape_key_mirror_show_mirror_tools:
            if has_shape_keys:
                mirror_col.prop(scene, "shape_key_mirror_mode", expand=True)
                if mode == "MANUAL":
                    mirror_col.prop_search(
                        scene,
                        "shape_key_mirror_source",
                        shape_keys,
                        "key_blocks",
                        text=_tr("Source"),
                    )
                    mirror_col.prop_search(
                        scene,
                        "shape_key_mirror_target",
                        shape_keys,
                        "key_blocks",
                        text=_tr("Target"),
                    )
                    source_name = scene.shape_key_mirror_source
                    target_name = scene.shape_key_mirror_target
                    if source_name and target_name:
                        mirror_col.label(text=f"{source_name} -> {target_name}")
                    else:
                        mirror_col.label(text=_tr("Choose source and target shape keys."))
                elif obj and obj.active_shape_key:
                    key_blocks = _shape_key_blocks(obj)
                    source_name = obj.active_shape_key.name
                    target_name = infer_opposite_shape_key_name(source_name)
                    if source_name and not _is_basis_shape_key_name(key_blocks, source_name):
                        mirror_col.label(text=f"{source_name} -> {target_name or _tr('Opposite side not recognized')}")
                    else:
                        mirror_col.label(text=_tr("Select a source shape key."))
                else:
                    mirror_col.label(text=_tr("Select a source shape key."))

                row = mirror_col.row(align=True)
                op_text = _ui_label("Auto Mirror") if mode == "AUTO" else _ui_label("Manual Mirror")
                op = row.operator("shape_key_mirror.active", text=op_text, icon="MOD_MIRROR")
                op.tolerance = scene.shape_key_mirror_tolerance

                op = row.operator(
                    "shape_key_mirror.batch_keys",
                    text=_ui_label("Batch Mirror"),
                    icon="MOD_MIRROR",
                )
                op.tolerance = scene.shape_key_mirror_tolerance

            else:
                mirror_col.label(text=_tr("No shape keys found on the selected object."), icon="INFO")

            if has_shape_keys:
                row = mirror_col.row(align=True)
                row.operator(
                    "shape_key_mirror.reset_active",
                    text=_ui_label("Reset Active Shape Key"),
                    icon="FILE_REFRESH",
                )
                op = row.operator(
                    "shape_key_mirror.repair_active_self_symmetry",
                    text=_ui_label("Repair Active Key Symmetry"),
                    icon="SHAPEKEY_DATA",
                )
                op.tolerance = scene.shape_key_mirror_tolerance

        layout.separator()
        utility_col = layout.column(align=True)
        row = utility_col.row()
        row.prop(
            scene,
            "shape_key_mirror_show_utility_tools",
            text=_ui_label("Other Tools"),
            icon="TRIA_DOWN" if scene.shape_key_mirror_show_utility_tools else "TRIA_RIGHT",
            emboss=False,
        )
        if scene.shape_key_mirror_show_utility_tools:
            if len(obj.modifiers) > 0:
                utility_col.prop_search(
                    scene,
                    "shape_key_mirror_modifier",
                    obj,
                    "modifiers",
                    text=_tr("Selected Modifier"),
                )
                row = utility_col.row(align=True)
                row.enabled = bool(scene.shape_key_mirror_modifier and obj.modifiers.get(scene.shape_key_mirror_modifier))
                row.operator(
                    "shape_key_mirror.apply_modifier_keep_shape_keys",
                    text=_ui_label("Apply Modifier Keep Shape Keys"),
                    icon="MODIFIER",
                )
            else:
                utility_col.label(text=_ui_label("No modifiers found on the selected object."), icon="INFO")

        layout.separator()
        vrm_col = layout.column(align=True)
        row = vrm_col.row()
        row.prop(
            scene,
            "shape_key_mirror_show_vrm_tools",
            text=_ui_label("VRM Tools"),
            icon="TRIA_DOWN" if scene.shape_key_mirror_show_vrm_tools else "TRIA_RIGHT",
            emboss=False,
        )
        if scene.shape_key_mirror_show_vrm_tools:
            proxy_ready = _vrm0_proxy_context_ready(context)
            row = vrm_col.row(align=True)
            row.enabled = proxy_ready
            row.operator(
                "shape_key_mirror.adapt_default_vrm_expressions",
                text=_ui_label("Adapt Default Expressions"),
                icon="SHAPEKEY_DATA",
            )
            row.operator(
                "shape_key_mirror.cancel_default_vrm_adaptation",
                text=_ui_label("Cancel Default Adaptation"),
                icon="X",
            )
            row = vrm_col.row(align=True)
            row.enabled = proxy_ready
            op = row.operator(
                "shape_key_mirror.import_arkit_to_vrm_proxy",
                text=_tr("Title Case"),
                icon="OUTLINER_OB_ARMATURE",
            )
            op.key_case = "UPPER"
            op = row.operator(
                "shape_key_mirror.import_arkit_to_vrm_proxy",
                text=_tr("Lower Camel Case"),
                icon="OUTLINER_OB_ARMATURE",
            )
            op.key_case = "LOWER"
            if not proxy_ready:
                vrm_col.label(text=_ui_label("VRM Proxy needs VRM Add-on and a VRM0 armature."), icon="ERROR")

        layout.separator()
        arkit_col = layout.column(align=True)
        row = arkit_col.row()
        row.prop(
            scene,
            "shape_key_mirror_show_arkit_tools",
            text=_ui_label("ARKit Tools"),
            icon="TRIA_DOWN" if scene.shape_key_mirror_show_arkit_tools else "TRIA_RIGHT",
            emboss=False,
        )
        if scene.shape_key_mirror_show_arkit_tools:
            row = arkit_col.row(align=True)
            row.operator("shape_key_mirror.add_arkit_keys", text=_ui_label("Add ARKit Keys"), icon="SHAPEKEY_DATA")
            row.operator("shape_key_mirror.convert_arkit_names", text=_ui_label("Convert Naming"), icon="SORTALPHA")
            row = arkit_col.row(align=True)
            op = row.operator(
                "shape_key_mirror.repair_arkit_symmetry",
                text=_ui_label("Repair 52 Symmetry"),
                icon="MOD_MIRROR",
            )
            op.tolerance = scene.shape_key_mirror_tolerance
