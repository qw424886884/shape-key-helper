# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty

from .constants import MIRROR_MODE_ITEMS
from .i18n import TRANSLATIONS
from .operators import (
    OBJECT_OT_shape_key_mirror_active,
    OBJECT_OT_shape_key_mirror_adapt_default_vrm_expressions,
    OBJECT_OT_shape_key_mirror_add_arkit_keys,
    OBJECT_OT_shape_key_mirror_apply_modifier_keep_shape_keys,
    OBJECT_OT_shape_key_mirror_cancel_default_vrm_adaptation,
    OBJECT_OT_shape_key_mirror_convert_arkit_names,
    OBJECT_OT_shape_key_mirror_import_arkit_to_vrm_proxy,
    OBJECT_OT_shape_key_mirror_repair_active_self_symmetry,
    OBJECT_OT_shape_key_mirror_repair_arkit_symmetry,
    OBJECT_OT_shape_key_mirror_repair_mesh_symmetry,
    OBJECT_OT_shape_key_mirror_reset_active,
    OBJECT_OT_shape_key_mirror_selected_meshes,
)
from .ui import DATA_PT_shape_key_mirror_master


CLASSES = (
    OBJECT_OT_shape_key_mirror_active,
    OBJECT_OT_shape_key_mirror_selected_meshes,
    OBJECT_OT_shape_key_mirror_reset_active,
    OBJECT_OT_shape_key_mirror_repair_mesh_symmetry,
    OBJECT_OT_shape_key_mirror_repair_active_self_symmetry,
    OBJECT_OT_shape_key_mirror_apply_modifier_keep_shape_keys,
    OBJECT_OT_shape_key_mirror_add_arkit_keys,
    OBJECT_OT_shape_key_mirror_convert_arkit_names,
    OBJECT_OT_shape_key_mirror_repair_arkit_symmetry,
    OBJECT_OT_shape_key_mirror_adapt_default_vrm_expressions,
    OBJECT_OT_shape_key_mirror_cancel_default_vrm_adaptation,
    OBJECT_OT_shape_key_mirror_import_arkit_to_vrm_proxy,
    DATA_PT_shape_key_mirror_master,
)

SCENE_PROPERTY_NAMES = (
    "shape_key_mirror_arkit_to_symmetrical",
    "shape_key_mirror_show_vrm_tools",
    "shape_key_mirror_show_arkit_tools",
    "shape_key_mirror_tolerance",
    "shape_key_mirror_modifier",
    "shape_key_mirror_show_base_settings",
    "shape_key_mirror_show_utility_tools",
    "shape_key_mirror_show_mirror_tools",
    "shape_key_mirror_base",
    "shape_key_mirror_target",
    "shape_key_mirror_source",
    "shape_key_mirror_mode",
)

TRANSLATION_KEY = __package__ or __name__


def register():
    try:
        bpy.app.translations.unregister(TRANSLATION_KEY)
    except Exception:
        pass
    bpy.app.translations.register(TRANSLATION_KEY, TRANSLATIONS)

    bpy.types.Scene.shape_key_mirror_mode = EnumProperty(
        name="Mode",
        description="Choose automatic opposite-side detection or manual source/target selection.",
        items=MIRROR_MODE_ITEMS,
        default="AUTO",
    )
    bpy.types.Scene.shape_key_mirror_source = StringProperty(
        name="Source",
        description="Manual source shape key name.",
        default="",
    )
    bpy.types.Scene.shape_key_mirror_target = StringProperty(
        name="Target",
        description="Manual target shape key name.",
        default="",
    )
    bpy.types.Scene.shape_key_mirror_base = StringProperty(
        name="Base Shape",
        description="Optional base shape key. Leave empty to use the first shape key automatically.",
        default="",
    )
    bpy.types.Scene.shape_key_mirror_show_mirror_tools = BoolProperty(
        name="Mirror Shape Keys",
        description="Show shape key mirror controls.",
        default=True,
    )
    bpy.types.Scene.shape_key_mirror_show_utility_tools = BoolProperty(
        name="Utility Tools",
        description="Show utility tools for symmetry repair, reset, and modifier application.",
        default=True,
    )
    bpy.types.Scene.shape_key_mirror_show_base_settings = BoolProperty(
        name="Base Shape Settings",
        description="Show optional base shape key selection.",
        default=False,
    )
    bpy.types.Scene.shape_key_mirror_modifier = StringProperty(
        name="Selected Modifier",
        description="Modifier to apply while preserving shape keys.",
        default="",
    )
    bpy.types.Scene.shape_key_mirror_tolerance = FloatProperty(
        name="Vertex Match Tolerance (%)",
        description="Larger values tolerate more asymmetry but may mismatch vertices. Smaller values are stricter.",
        default=0.5,
        min=0.0,
        max=5.0,
        soft_max=2.0,
    )
    bpy.types.Scene.shape_key_mirror_show_arkit_tools = BoolProperty(
        name="ARKit Tools",
        description="Less-used helpers for creating ARKit shape keys and switching left/right naming style.",
        default=False,
    )
    bpy.types.Scene.shape_key_mirror_show_vrm_tools = BoolProperty(
        name="VRM Tools",
        description="Helpers for VRM0 Blend Shape Proxy setup.",
        default=True,
    )
    bpy.types.Scene.shape_key_mirror_arkit_to_symmetrical = BoolProperty(
        name="Convert ARKit names to _L/_R",
        description="Next ARKit naming conversion direction.",
        default=True,
    )

    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    for prop_name in SCENE_PROPERTY_NAMES:
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
    try:
        bpy.app.translations.unregister(TRANSLATION_KEY)
    except Exception:
        pass
