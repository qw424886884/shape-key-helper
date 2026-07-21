import importlib.util
import json
import os
import sys
from pathlib import Path

import bpy


PLUGIN_ROOT = Path(os.environ.get("PLUGIN_PATH_OVERRIDE") or Path(__file__).parent)
if PLUGIN_ROOT.is_file():
    PLUGIN_ROOT = PLUGIN_ROOT.parent
PACKAGE_NAME = "shape_key_helper_runtime_test"


def load_plugin():
    for module_name in tuple(sys.modules):
        if module_name == PACKAGE_NAME or module_name.startswith(f"{PACKAGE_NAME}."):
            del sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        PLUGIN_ROOT / "__init__.py",
        submodule_search_locations=[str(PLUGIN_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)
    return module


def rounded_coords(key_block):
    return [
        (round(point.co.x, 6), round(point.co.y, 6), round(point.co.z, 6))
        for point in key_block.data
    ]


def rounded_deltas(shape_key, basis):
    return [
        tuple(round((shape_key.data[index].co - basis.data[index].co)[axis], 6) for axis in range(3))
        for index in range(len(basis.data))
    ]


def max_delta(shape_key, basis):
    return max(
        (shape_key.data[index].co - basis.data[index].co).length
        for index in range(len(basis.data))
    )


def create_quad_object(name):
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata(
        [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    return obj


def main():
    module = load_plugin()
    module.register()
    module.unregister()
    module.register()
    try:
        assert callable(getattr(bpy.ops.shape_key_mirror, "repair_mesh_symmetry"))
        assert callable(getattr(bpy.ops.shape_key_mirror, "repair_active_self_symmetry"))
        assert callable(getattr(bpy.ops.shape_key_mirror, "apply_modifier_keep_shape_keys"))

        mesh = bpy.data.meshes.new("symmetry_test_mesh")
        mesh.from_pydata([(-0.9, 0, 0), (1.1, 0, 0), (0.1, 1, 0)], [], [(0, 1, 2)])
        mesh.update()
        obj = bpy.data.objects.new("symmetry_test", mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        basis = obj.shape_key_add(name="Basis", from_mix=False)
        smile = obj.shape_key_add(name="Smile", from_mix=False)
        smile.data[0].co.y += 0.2
        smile.data[1].co.x += 0.1
        smile.data[1].co.y += 0.3
        smile.data[2].co.y += 0.5

        model_result = module.repair_mesh_symmetry(obj, tolerance_percent=0.5)
        assert rounded_coords(basis) == [(-1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        assert rounded_deltas(smile, basis) == [(0.0, 0.2, 0.0), (0.1, 0.3, 0.0), (0.0, 0.5, 0.0)]

        one_side = obj.shape_key_add(name="OneSide", from_mix=False)
        for index, point in enumerate(basis.data):
            one_side.data[index].co = point.co.copy()
        one_side.data[1].co.x += 0.2
        one_side.data[1].co.y += 0.3

        self_result = module.repair_active_shape_key_self_symmetry(obj, "OneSide", tolerance_percent=0.5)
        assert rounded_coords(one_side)[:2] == [(-1.2, 0.3, 0.0), (1.2, 0.3, 0.0)]

        mod_obj = create_quad_object("modifier_keep_keys")

        mod_basis = mod_obj.shape_key_add(name="Basis", from_mix=False)
        raise_key = mod_obj.shape_key_add(name="Raise", from_mix=False)
        raise_key.data[0].co.z += 0.25
        raise_key.value = 0.4

        muted_key = mod_obj.shape_key_add(name="Muted", from_mix=False)
        muted_key.data[1].co.z += 0.3
        muted_key.mute = True

        mask_group = mod_obj.vertex_groups.new(name="HalfMask")
        mask_group.add([0], 0.5, "REPLACE")
        masked_key = mod_obj.shape_key_add(name="Masked", from_mix=False)
        masked_key.data[0].co.z += 0.4
        masked_key.vertex_group = mask_group.name

        parent_key = mod_obj.shape_key_add(name="Parent", from_mix=False)
        parent_key.data[2].co.z += 0.2
        child_key = mod_obj.shape_key_add(name="Child", from_mix=False)
        child_key.data[2].co.z += 0.6
        child_key.relative_key = parent_key
        mod_obj.active_shape_key_index = 5

        raise_key.keyframe_insert(data_path="value", frame=1)
        original_action = mod_obj.data.shape_keys.animation_data.action

        bpy.context.scene["shape_key_helper_driver_input"] = 0.75
        driver_fcurve = masked_key.driver_add("value")
        driver_fcurve.driver.type = "SCRIPTED"
        driver_fcurve.driver.expression = "input_value * 0.5 + source_value * 0.0"
        variable = driver_fcurve.driver.variables.new()
        variable.name = "input_value"
        variable.type = "SINGLE_PROP"
        variable.targets[0].id_type = "SCENE"
        variable.targets[0].id = bpy.context.scene
        variable.targets[0].data_path = '["shape_key_helper_driver_input"]'
        source_variable = driver_fcurve.driver.variables.new()
        source_variable.name = "source_value"
        source_variable.type = "SINGLE_PROP"
        source_variable.targets[0].id_type = "KEY"
        source_variable.targets[0].id = mod_obj.data.shape_keys
        source_variable.targets[0].data_path = 'key_blocks["Raise"].value'

        solidify = mod_obj.modifiers.new("KeepKeysSolidify", "SOLIDIFY")
        solidify.thickness = 0.1
        original_vertex_count = len(mod_obj.data.vertices)

        modifier_result = module.apply_modifier_keep_shape_keys(bpy.context, mod_obj, "KeepKeysSolidify")
        key_blocks = mod_obj.data.shape_keys.key_blocks
        assert mod_obj.modifiers.get("KeepKeysSolidify") is None
        assert [key.name for key in key_blocks] == ["Basis", "Raise", "Muted", "Masked", "Parent", "Child"]
        assert len(mod_obj.data.vertices) > original_vertex_count
        assert round(key_blocks["Raise"].value, 6) == 0.4
        assert max_delta(key_blocks["Raise"], key_blocks["Basis"]) > 0.2
        assert key_blocks["Muted"].mute is True
        assert max_delta(key_blocks["Muted"], key_blocks["Basis"]) > 0.25
        assert key_blocks["Masked"].vertex_group == "HalfMask"
        assert max_delta(key_blocks["Masked"], key_blocks["Basis"]) > 0.35
        assert key_blocks["Child"].relative_key == key_blocks["Parent"]
        assert max_delta(key_blocks["Child"], key_blocks["Parent"]) > 0.35
        assert mod_obj.active_shape_key_index == 5

        new_animation_data = mod_obj.data.shape_keys.animation_data
        assert new_animation_data.action == original_action
        assert len(new_animation_data.drivers) == 1
        new_driver = new_animation_data.drivers[0]
        assert new_driver.data_path == 'key_blocks["Masked"].value'
        assert new_driver.driver.expression == "input_value * 0.5 + source_value * 0.0"
        assert new_driver.driver.variables[0].targets[0].id == bpy.context.scene
        assert new_driver.driver.variables[1].targets[0].id == mod_obj.data.shape_keys

        absolute_obj = create_quad_object("absolute_keep_keys")
        absolute_basis = absolute_obj.shape_key_add(name="Basis", from_mix=False)
        absolute_key = absolute_obj.shape_key_add(name="AbsolutePose", from_mix=False)
        absolute_key.data[0].co.z += 0.35
        absolute_obj.data.shape_keys.use_relative = False
        absolute_obj.data.shape_keys.eval_time = 6.0
        absolute_solidify = absolute_obj.modifiers.new("AbsoluteSolidify", "SOLIDIFY")
        absolute_solidify.thickness = 0.1

        module.apply_modifier_keep_shape_keys(bpy.context, absolute_obj, "AbsoluteSolidify")
        absolute_blocks = absolute_obj.data.shape_keys.key_blocks
        assert absolute_obj.data.shape_keys.use_relative is False
        assert round(absolute_obj.data.shape_keys.eval_time, 6) == 6.0
        assert round(absolute_blocks["AbsolutePose"].frame, 6) == 10.0
        assert max_delta(absolute_blocks["AbsolutePose"], absolute_blocks["Basis"]) > 0.3

        rollback_obj = create_quad_object("modifier_rollback")
        rollback_obj.shape_key_add(name="Basis", from_mix=False)
        rollback_key = rollback_obj.shape_key_add(name="RollbackShape", from_mix=False)
        rollback_key.data[0].co.z += 0.2
        rollback_obj.modifiers.new("RollbackSolidify", "SOLIDIFY")
        rollback_mesh = rollback_obj.data
        original_restore_animation = module.modifier_tools._restore_shape_key_animation

        def force_restore_failure(*_args, **_kwargs):
            raise RuntimeError("forced rollback test")

        module.modifier_tools._restore_shape_key_animation = force_restore_failure
        try:
            try:
                module.apply_modifier_keep_shape_keys(bpy.context, rollback_obj, "RollbackSolidify")
            except ValueError as exc:
                assert "forced rollback test" in str(exc)
            else:
                raise AssertionError("Expected modifier rebuild rollback")
        finally:
            module.modifier_tools._restore_shape_key_animation = original_restore_animation

        assert rollback_obj.data == rollback_mesh
        assert rollback_obj.modifiers.get("RollbackSolidify") is not None
        assert [key.name for key in rollback_obj.data.shape_keys.key_blocks] == ["Basis", "RollbackShape"]

        print(
            "SHAPE_KEY_MIRROR_SMOKE",
            json.dumps(
                {
                    "version": module.bl_info["version"],
                    "model_changed_vertices": model_result["changed_vertices"],
                    "model_center_shift_x": round(model_result["center_shift_x"], 6),
                    "self_changed_relations": self_result["changed_relations"],
                    "modifier_vertices": modifier_result["vertices"],
                    "modifier_shape_keys": modifier_result["shape_keys"],
                    "modifier_drivers": len(new_animation_data.drivers),
                    "absolute_shape_keys": len(absolute_blocks),
                    "rollback_preserved": rollback_obj.data == rollback_mesh,
                },
                ensure_ascii=False,
            ),
        )
    finally:
        module.unregister()


if __name__ == "__main__":
    main()
