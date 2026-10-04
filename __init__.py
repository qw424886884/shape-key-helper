# Shape Key Helper
# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Shape Key Helper",
    "author": "Fengjishi Studio / 风纪石",
    "version": (1, 14, 4),
    "blender": (4, 2, 0),
    "location": "Object Data Properties > Shape Keys",
    "description": "Mirror and repair shape keys, fix mesh symmetry, and apply modifiers without losing shape keys.",
    "category": "Object",
}

from . import modifier_tools
from .arkit_tools import (
    add_missing_arkit_shape_keys,
    convert_arkit_shape_key_names,
    repair_arkit_shape_key_symmetry,
)
from .constants import ARKIT_SHAPE_KEYS
from .i18n import _ui_label
from .modifier_tools import apply_modifier_keep_shape_keys
from .operators import OBJECT_OT_shape_key_mirror_reset_active
from .registration import register, unregister
from .shape_key_core import (
    analyze_shape_key_mirror,
    infer_opposite_shape_key_name,
    mirror_shape_key_to_target,
    repair_active_shape_key_self_symmetry,
    repair_mesh_symmetry,
    reset_shape_key_to_basis,
)

__all__ = (
    "ARKIT_SHAPE_KEYS",
    "OBJECT_OT_shape_key_mirror_reset_active",
    "add_missing_arkit_shape_keys",
    "analyze_shape_key_mirror",
    "apply_modifier_keep_shape_keys",
    "bl_info",
    "convert_arkit_shape_key_names",
    "infer_opposite_shape_key_name",
    "mirror_shape_key_to_target",
    "modifier_tools",
    "register",
    "repair_active_shape_key_self_symmetry",
    "repair_arkit_shape_key_symmetry",
    "repair_mesh_symmetry",
    "reset_shape_key_to_basis",
    "unregister",
)
