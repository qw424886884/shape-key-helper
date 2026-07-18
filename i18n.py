# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy


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
