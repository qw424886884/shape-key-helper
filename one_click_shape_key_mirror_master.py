# Shape Key Helper
# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name": "Shape Key Helper",
    "author": "Fengjishi Studio / 风纪石",
    "version": (1, 14, 1),
    "blender": (5, 1, 0),
    "location": "Object Data Properties > Shape Keys",
    "description": "Mirror and repair shape keys, fix mesh symmetry, and apply modifiers without losing shape keys.",
    "category": "Object",
}

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
from mathutils import Vector
from mathutils.kdtree import KDTree


NAME_PAIRS = (
    ("Left", "Right"),
    ("left", "right"),
    ("LEFT", "RIGHT"),
    ("L_", "R_"),
    ("L.", "R."),
    ("L-", "R-"),
    ("L ", "R "),
    ("l_", "r_"),
    ("l.", "r."),
    ("l-", "r-"),
    ("l ", "r "),
    ("_L", "_R"),
    (".L", ".R"),
    ("-L", "-R"),
    (" L", " R"),
    ("_l", "_r"),
    (".l", ".r"),
    ("-l", "-r"),
    (" l", " r"),
    ("左", "右"),
)

MIRROR_MODE_ITEMS = (
    ("AUTO", "Active Key Auto", "Use the active shape key as source and mirror to the opposite side."),
    ("MANUAL", "Manual Pair", "Choose source and target shape keys manually."),
)

ARKIT_SHAPE_KEYS = [
    # Eyebrows
    "BrowDownLeft", "BrowDownRight", "BrowInnerUp", "BrowOuterUpLeft", "BrowOuterUpRight",
    # Eyes
    "EyeBlinkLeft", "EyeBlinkRight",
    "EyeLookDownLeft", "EyeLookDownRight",
    "EyeLookInLeft", "EyeLookInRight",
    "EyeLookOutLeft", "EyeLookOutRight",
    "EyeLookUpLeft", "EyeLookUpRight",
    "EyeSquintLeft", "EyeSquintRight",
    "EyeWideLeft", "EyeWideRight",
    # Mouth and jaw
    "JawForward", "JawLeft", "JawRight", "JawOpen",
    "MouthClose", "MouthFunnel", "MouthPucker", "MouthLeft", "MouthRight",
    "MouthSmileLeft", "MouthSmileRight", "MouthFrownLeft", "MouthFrownRight", "MouthDimpleLeft", "MouthDimpleRight",
    "MouthStretchLeft", "MouthStretchRight",
    "MouthRollLower", "MouthRollUpper", "MouthShrugLower", "MouthShrugUpper",
    "MouthPressLeft", "MouthPressRight",
    "MouthLowerDownRight", "MouthLowerDownLeft",
    "MouthUpperUpLeft", "MouthUpperUpRight",
    # Cheeks and nose
    "CheekPuff", "CheekSquintLeft", "CheekSquintRight", "NoseSneerLeft", "NoseSneerRight",
    # ARKit's 52nd key; the referenced page does not list it in the visible category blocks.
    "TongueOut",
]

VRM_PROXY_CASE_ITEMS = (
    ("UPPER", "Title Case", "Import ARKit proxy groups as BrowDownLeft, EyeBlinkLeft, ..."),
    ("LOWER", "Lower Camel Case", "Import ARKit proxy groups as browDownLeft, eyeBlinkLeft, ..."),
)

VRM0_DEFAULT_EXPRESSION_MAPPINGS = (
    {"name": "Neutral", "preset": "neutral", "keys": ()},
    {"name": "A", "preset": "a", "keys": ("JawOpen",)},
    {"name": "I", "preset": "i", "keys": ("MouthStretchLeft", "MouthStretchRight")},
    {"name": "U", "preset": "u", "keys": ("MouthPucker", "MouthFunnel")},
    {"name": "E", "preset": "e", "keys": ("MouthSmileLeft", "MouthSmileRight", "MouthStretchLeft", "MouthStretchRight")},
    {"name": "O", "preset": "o", "keys": ("JawOpen", "MouthFunnel", "MouthPucker")},
    {"name": "Blink", "preset": "blink", "keys": ("EyeBlinkLeft", "EyeBlinkRight")},
    {"name": "Joy", "preset": "joy", "keys": ("MouthSmileLeft", "MouthSmileRight", "CheekSquintLeft", "CheekSquintRight")},
    {"name": "Angry", "preset": "angry", "keys": ("BrowDownLeft", "BrowDownRight", "EyeSquintLeft", "EyeSquintRight")},
    {"name": "Sorrow", "preset": "sorrow", "keys": ("MouthFrownLeft", "MouthFrownRight", "BrowInnerUp")},
    {"name": "Fun", "preset": "fun", "keys": ("MouthSmileLeft", "MouthSmileRight", "MouthDimpleLeft", "MouthDimpleRight")},
    {"name": "LookUp", "preset": "lookup", "keys": ("EyeLookUpLeft", "EyeLookUpRight")},
    {"name": "LookDown", "preset": "lookdown", "keys": ("EyeLookDownLeft", "EyeLookDownRight")},
    {"name": "LookLeft", "preset": "lookleft", "keys": ("EyeLookOutLeft", "EyeLookInRight")},
    {"name": "LookRight", "preset": "lookright", "keys": ("EyeLookInLeft", "EyeLookOutRight")},
    {"name": "Blink_L", "preset": "blink_l", "keys": ("EyeBlinkLeft",)},
    {"name": "Blink_R", "preset": "blink_r", "keys": ("EyeBlinkRight",)},
)

ARKIT_DIRECTION_EXCEPTION_KEYS = {
    "MouthLeft", "MouthRight", "JawLeft", "JawRight",
    "mouthLeft", "mouthRight", "jawLeft", "jawRight",
}

TRANSLATIONS = {
    "zh_HANS": {
        ("*", "Shape Key Helper"): "形态键一键镜像大师",
        ("*", "Mirror and repair shape keys, fix mesh symmetry, and apply modifiers without losing shape keys."): "镜像和修复形态键、修正模型对称，并在不丢失形态键的情况下应用修改器。",
        ("*", "Active Key Auto"): "自动识别",
        ("*", "Use the active shape key as source and mirror to the opposite side."): "当前形态键作为来源，自动镜像到对侧。",
        ("*", "Manual Pair"): "手动指定",
        ("*", "Choose source and target shape keys manually."): "手动选择来源和目标形态键。",
        ("*", "Manual mode needs both source and target shape keys."): "手动模式需要同时选择来源和目标形态键。",
        ("*", "Basis cannot be used as source or target."): "Basis 不能作为来源或目标。",
        ("*", "No usable base shape key found. Shape keys need a base shape key as the first shape key, usually named Basis/基型/基础. Select a mesh with shape keys, or recreate/reimport the model so the base shape is present before using mirror, reset, or repair."): "没有找到可用的基础形态键。形态键需要把基础形态放在第一项，通常叫 Basis / 基型 / 基础。请选择带形态键的网格；如果模型的基础形态缺失，请先重建或重新导入模型，再使用镜像、恢复或修复功能。",
        ("*", "Base shape key not found: {name}. Clear Base Shape to use automatic first-key detection, or choose an existing base shape key."): "找不到指定的基础形态：{name}。清空“基础形态”可自动使用第一项，或选择一个已经存在的基础形态键。",
        ("*", "The selected base shape key cannot be reset. Select a normal shape key; if this is wrong, clear Base Shape or choose the model's default base shape."): "指定的基础形态不能恢复它自己。请选择普通形态键；如果这里判断错了，请清空“基础形态”或选择模型默认的基础形态。",
        ("*", "The selected base shape key cannot be used as source or target. Select normal expression keys; if this is wrong, clear Base Shape or choose the model's default base shape."): "指定的基础形态不能作为来源或目标。请选择普通表情形态键；如果这里判断错了，请清空“基础形态”或选择模型默认的基础形态。",
        ("*", "The first shape key is treated as the base shape key and cannot be reset. Select a normal shape key; if this is wrong, set the base shape as the first shape key."): "第一项形态键会被当作基础形态，不能恢复它自己。请选择普通形态键；如果这里判断错了，请把真正的基础形态放到形态键列表第一项。",
        ("*", "The first shape key is treated as the base shape key and cannot be used as source or target. Select normal expression keys; if this is wrong, set the base shape as the first shape key."): "第一项形态键会被当作基础形态，不能作为来源或目标。请选择普通表情形态键；如果这里判断错了，请把真正的基础形态放到形态键列表第一项。",
        ("*", "Source and target shape keys cannot be the same."): "来源和目标形态键不能相同。",
        ("*", "Cannot infer opposite shape key for: {name}"): "无法识别对侧形态键：{name}",
        ("*", "Mesh is asymmetric; mirror cancelled. Unmatched vertices: {count}. Try a larger tolerance or fix mesh symmetry first. Current tolerance: {percent:.2f}% ({distance:.6f}), max deviation: {max_distance:.6f}."): "模型非对称，无法镜像：{count} 个顶点找不到镜像点。可尝试调大容差，或先修正模型对称。当前容差 {percent:.2f}%（{distance:.6f}），最大偏差 {max_distance:.6f}。",
        ("*", "Mirror Active Shape Key"): "镜像当前形态键",
        ("*", "Mirror the resolved source shape key into the target shape key. Does not create, delete, or rename shape keys."): "把来源形态键镜像到目标形态键；不会创建、删除或改名形态键。",
        ("*", "Reset Active Shape Key"): "恢复当前形态键到默认",
        ("*", "Copy base shape coordinates into the active shape key. This clears the current key without changing the base shape or other shape keys."): "把基础形态坐标复制到当前形态键；只清空当前形态键，不修改基础形态或其他形态键。",
        ("*", "Batch Mirror Selected Meshes"): "批量镜像选中网格同名键",
        ("*", "Apply the current source -> target direction to selected mesh objects. Each mesh must contain matching source and target shape keys."): "把当前来源 -> 目标方向应用到选中的网格对象；每个网格必须有同名来源和目标形态键。",
        ("*", "Vertex Match Tolerance (%)"): "顶点匹配容差(%)",
        ("*", "Larger values tolerate more asymmetry but may mismatch vertices. Smaller values are stricter."): "数字越大越宽松但可能错配；数字越小越严格。",
        ("*", "Mode"): "模式",
        ("*", "Choose automatic opposite-side detection or manual source/target selection."): "自动识别对侧，或手动指定来源和目标。",
        ("*", "Source"): "来源",
        ("*", "Manual source shape key name."): "手动模式下的来源形态键。",
        ("*", "Target"): "目标",
        ("*", "Manual target shape key name."): "手动模式下的目标形态键。",
        ("*", "Base Shape"): "基础形态",
        ("*", "Base Shape Settings"): "基础形态设置",
        ("*", "Optional base shape key. Leave empty to use the first shape key automatically."): "可选的基础形态键。留空时自动使用形态键列表第一项。",
        ("*", "Show optional base shape key selection."): "显示可选的基础形态手动选择。",
        ("*", "Base: Auto (first shape key)"): "基础形态：自动（第一项形态键）",
        ("*", "Base: Auto ({name})"): "基础形态：自动（{name}）",
        ("*", "Base: {name}"): "基础形态：{name}",
        ("*", "Opposite side not recognized"): "未识别对侧",
        ("*", "Choose source and target shape keys."): "请选择来源和目标形态键",
        ("*", "Select a source shape key."): "请选择来源形态键",
        ("*", "Mirror Automatically"): "按自动识别镜像",
        ("*", "Mirror Manually"): "按手动设置镜像",
        ("*", "Auto Mirror"): "自动镜像",
        ("*", "Manual Mirror"): "手动镜像",
        ("*", "Batch Mirror"): "批量镜像",
        ("*", "ARKit Tools"): "ARKit 工具",
        ("*", "Less-used helpers for creating ARKit shape keys and switching left/right naming style."): "不常用辅助工具：创建 ARKit 形态键，或切换左右命名格式。",
        ("*", "Add ARKit Keys"): "添加 ARKit 键",
        ("*", "Add missing ARKit 52 shape keys to the active object. Existing keys are kept and not duplicated."): "给当前对象补齐 ARKit 52 个形态键；已有形态键会保留且不重复添加。",
        ("*", "Convert Naming"): "转换命名",
        ("*", "Toggle ARKit names between Left/Right and _L/_R style. Directional names such as MouthLeft are kept."): "在 Left/Right 和 _L/_R 命名之间切换；MouthLeft 等方向动作名会保留。",
        ("*", "Repair 52 Symmetry"): "修复52对称",
        ("*", "Repair symmetry drift across the existing ARKit 52 shape keys. Does not add, delete, or rename shape keys."): "修复已有 ARKit 52 形态键里的左右偏差；不会新增、删除或重命名形态键。",
        ("*", "VRM Tools"): "VRM 工具",
        ("*", "Helpers for VRM0 Blend Shape Proxy setup."): "VRM0 混合形态代理辅助工具。",
        ("*", "Adapt Default Expressions"): "适配默认表情",
        ("*", "Bind the existing ARKit 52 shape keys to VRM0 default Blend Shape Proxy expressions."): "把已有 ARKit 52 形态键绑定到 VRM0 默认混合形态代理表情。",
        ("*", "Cancel Default Adaptation"): "取消适配",
        ("*", "Remove ARKit 52 binds from VRM0 default Blend Shape Proxy expressions while keeping the default groups."): "从 VRM0 默认混合形态代理表情中移除 ARKit 52 绑定，并保留默认表情组。",
        ("*", "Import to VRM Proxy"): "导入 VRM 代理",
        ("*", "Import ARKit 52 keys into the VRM0 Blend Shape Proxy. Existing ARKit proxy groups are reused or renamed without duplicate binds."): "把 ARKit 52 写入 VRM0 混合形态代理；已有 ARKit 代理组会复用或改名，不重复绑定。",
        ("*", "VRM Proxy needs VRM Add-on and a VRM0 armature."): "需要启用 VRM Add-on，并在场景中保留 VRM0 骨架。",
        ("*", "VRM Add-on is not available. Enable the VRM Add-on before importing ARKit keys into Blend Shape Proxy."): "未检测到 VRM Add-on，无法写入混合形态代理。请先启用 VRM 插件。",
        ("*", "No VRM0 armature found. Select a mesh bound to a VRM0 armature or keep the VRM0 armature in the scene."): "未找到 VRM0 骨架。请选择绑定到 VRM0 骨架的网格，或在场景中保留 VRM0 骨架。",
        ("*", "The detected VRM armature is not VRM 0.0. Blend Shape Proxy is a VRM0 feature."): "当前检测到的 VRM 骨架不是 VRM 0.0；混合形态代理是 VRM0 功能。",
        ("*", "No mesh with shape keys was found for the VRM0 armature."): "未找到可用于 VRM0 骨架的形态键网格。",
        ("*", "No ARKit 52 shape keys were found on the selected or VRM0-bound meshes."): "选中网格或 VRM0 绑定网格中没有找到 ARKit 52 形态键。",
        ("*", "Select a mesh or curve object."): "请选择网格或曲线对象。",
        ("*", "No shape keys found on the selected object."): "当前对象没有形态键。",
        ("*", "Select a mesh object."): "请选择网格对象。",
        ("*", "Selected mesh has no active shape key."): "当前网格没有激活的形态键。",
        ("*", "Selected mesh has no vertices."): "当前网格没有顶点。",
        ("*", "Repair Model Symmetry"): "修复模型对称",
        ("*", "Center and symmetrize the mesh data without deleting vertices, changing topology, or touching UVs. Shape key deltas are preserved."): "把网格数据居中并修成完全对称；不删除顶点、不改拓扑、不碰 UV，并保留形态键相对变形。",
        ("*", "Repair Active Key Symmetry"): "修复当前形态对称",
        ("*", "Repair the active shape key against itself. If only one side was edited, the edited side is mirrored to the untouched side."): "只修复当前形态键自身对称；如果只改了一侧，会把已改侧镜像到未改侧。",
        ("*", "Mirror Shape Keys"): "镜像形态键",
        ("*", "Utility Tools"): "实用功能",
        ("*", "Selected Modifier"): "选择修改器",
        ("*", "Apply Modifier Keep Shape Keys"): "应用修改器并保留形态键",
        ("*", "Apply the selected modifier while rebuilding all existing shape keys. Other modifiers are temporarily disabled to avoid double application."): "应用选中的修改器，并重建保留所有已有形态键。其他修改器会临时关闭，避免重复叠加。",
        ("*", "Select a modifier first."): "请先选择一个修改器。",
        ("*", "Selected modifier not found: {name}"): "找不到选择的修改器：{name}",
        ("*", "No modifiers found on the selected object."): "当前对象没有修改器。",
        ("*", "The modifier result changes vertex count inconsistently between shape keys. Cancelled to protect shape keys."): "修改器在不同形态键下生成的顶点数量不一致。为保护形态键，已取消。",
        ("*", "Shape key NLA tracks are not supported yet. Remove or bake the NLA tracks before applying a modifier."): "暂不支持带 NLA 轨道的形态键。请先移除或烘焙 NLA 轨道，再应用修改器。",
        ("*", "Could not apply the modifier while preserving shape keys: {error}"): "应用修改器并保留形态键失败：{error}",
        ("*", "Repaired model symmetry on {name}: {changed}/{total} vertices, X shift {shift:.6f}, preserved {keys} shape keys"): "{name}：修复模型对称，顶点 {changed}/{total}，X 轴平移 {shift:.6f}，保留形态键 {keys}",
        ("*", "Repaired symmetry for {key} on {name}: {changed} relations changed, {deviated} deviations found"): "{name}：修复 {key} 自身对称，修复关系 {changed}，偏差关系 {deviated}",
        ("*", "Applied modifier {modifier} on {name}, preserved {keys} shape keys and {vertices} vertices"): "{name}：应用修改器 {modifier}，保留形态键 {keys}，顶点 {vertices}",
        ("*", "Applied modifier {modifier} on {name}; no shape keys were present"): "{name}：应用修改器 {modifier}；对象没有形态键",
        ("*", "Repaired ARKit symmetry on {name}: checked {checked}/52 keys, repaired {groups} groups and {relations} relations, {missing} keys missing"): "{name}：修复 ARKit 对称，检查 {checked}/52 个键，修复 {groups} 组和 {relations} 个关系，缺失 {missing} 个键",
        ("*", "Adapted VRM0 default expressions: {groups} groups added, {added} binds added, {existing} binds kept, {missing} groups missing"): "适配 VRM0 默认表情：新增组 {groups}，新增绑定 {added}，保留绑定 {existing}，缺失组 {missing}",
        ("*", "Removed VRM0 default adaptation: {removed} binds removed, {kept} other binds kept, {missing} groups missing"): "取消 VRM0 默认适配：移除绑定 {removed}，保留其他绑定 {kept}，缺失组 {missing}",
        ("*", "Imported ARKit keys to VRM proxy ({case}): {groups} groups added, {renamed} renamed, {added} binds added, {existing} binds kept, {missing} groups without binds"): "导入 ARKit 到 VRM 代理（{case}）：新增组 {groups}，改名 {renamed}，新增绑定 {added}，保留绑定 {existing}，无绑定组 {missing}",
        ("*", "Title Case"): "开头大写",
        ("*", "Lower Camel Case"): "开头小写",
    }
}
TRANSLATIONS["zh_CN"] = TRANSLATIONS["zh_HANS"]

VISIBLE_LABELS_ZH = {
    "Auto Mirror": "自动镜像",
    "Manual Mirror": "手动镜像",
    "Batch Mirror": "批量镜像",
    "Reset Active Shape Key": "恢复当前形态键到默认",
    "ARKit Tools": "ARKit 工具",
    "Add ARKit Keys": "添加 ARKit 键",
    "Convert Naming": "转换命名",
    "Repair 52 Symmetry": "修复52对称",
    "VRM Tools": "VRM 工具",
    "Adapt Default Expressions": "适配默认表情",
    "Cancel Default Adaptation": "取消适配",
    "Import to VRM Proxy": "导入 VRM 代理",
    "VRM Proxy needs VRM Add-on and a VRM0 armature.": "需要启用 VRM Add-on，并在场景中保留 VRM0 骨架。",
    "Repair Model Symmetry": "修复模型对称",
    "Repair Active Key Symmetry": "修复当前形态对称",
    "Mirror Shape Keys": "镜像形态键",
    "Utility Tools": "实用功能",
    "Apply Modifier Keep Shape Keys": "应用修改器保留形态键",
    "No modifiers found on the selected object.": "当前对象没有修改器。",
}


def _tr(message, **kwargs):
    translated = bpy.app.translations.pgettext_iface(message)
    return translated.format(**kwargs) if kwargs else translated


def _current_ui_language():
    candidates = []
    try:
        candidates.append(bpy.context.preferences.view.language)
    except Exception:
        pass
    try:
        candidates.append(bpy.app.translations.locale)
    except Exception:
        pass

    for candidate in candidates:
        if candidate and candidate != "DEFAULT":
            return str(candidate)
    return str(candidates[0]) if candidates else ""


def _ui_label(message, language=None):
    language = language or _current_ui_language()
    if str(language).lower().startswith("zh"):
        return VISIBLE_LABELS_ZH.get(message, message)
    return message


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


MISSING_BASIS_MESSAGE = "No usable base shape key found. Shape keys need a base shape key as the first shape key, usually named Basis/基型/基础. Select a mesh with shape keys, or recreate/reimport the model so the base shape is present before using mirror, reset, or repair."


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


def _mirrored_delta(delta):
    return Vector((-delta.x, delta.y, delta.z))


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


class OBJECT_OT_shape_key_mirror_selected_meshes(bpy.types.Operator):
    """Mirror the resolved source key name into the target key on every selected mesh."""

    bl_idname = "shape_key_mirror.selected_meshes"
    bl_label = "Batch Mirror Selected Meshes"
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

        layout.prop(scene, "shape_key_mirror_tolerance")

        mirror_col = layout.column(align=True)
        row = mirror_col.row()
        row.prop(
            scene,
            "shape_key_mirror_show_mirror_tools",
            text=_ui_label("Mirror Shape Keys"),
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
                    "shape_key_mirror.selected_meshes",
                    text=_ui_label("Batch Mirror"),
                    icon="MOD_MIRROR",
                )
                op.tolerance = scene.shape_key_mirror_tolerance

                base_row = mirror_col.row(align=True)
                base_row.prop(
                    scene,
                    "shape_key_mirror_show_base_settings",
                    text=_tr("Base Shape Settings"),
                    icon="TRIA_DOWN" if scene.shape_key_mirror_show_base_settings else "TRIA_RIGHT",
                    emboss=False,
                )
                if scene.shape_key_mirror_show_base_settings:
                    base_col = mirror_col.column(align=True)
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
            else:
                mirror_col.label(text=_tr("No shape keys found on the selected object."), icon="INFO")

        layout.separator()
        utility_col = layout.column(align=True)
        row = utility_col.row()
        row.prop(
            scene,
            "shape_key_mirror_show_utility_tools",
            text=_ui_label("Utility Tools"),
            icon="TRIA_DOWN" if scene.shape_key_mirror_show_utility_tools else "TRIA_RIGHT",
            emboss=False,
        )
        if scene.shape_key_mirror_show_utility_tools:
            op = utility_col.operator(
                "shape_key_mirror.repair_mesh_symmetry",
                text=_ui_label("Repair Model Symmetry"),
                icon="MOD_MIRROR",
            )
            op.tolerance = scene.shape_key_mirror_tolerance

            if has_shape_keys:
                row = utility_col.row(align=True)
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


classes = (
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


def register():
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass
    bpy.app.translations.register(__name__, TRANSLATIONS)

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
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    for prop_name in (
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
    ):
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
    try:
        bpy.app.translations.unregister(__name__)
    except Exception:
        pass


if __name__ == "__main__":
    register()
