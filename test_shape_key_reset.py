import importlib.util
import sys
import types
from pathlib import Path


PLUGIN_ROOT = Path(__file__).parent
PACKAGE_NAME = "shape_key_helper_test"


class Coord:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @property
    def xyz(self):
        return (self.x, self.y, self.z)

    def copy(self):
        return Coord(self.x, self.y, self.z)

    @property
    def length(self):
        return (self.x * self.x + self.y * self.y + self.z * self.z) ** 0.5

    def __add__(self, other):
        return Coord(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Coord(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, value):
        return Coord(self.x * value, self.y * value, self.z * value)

    def __rmul__(self, value):
        return self.__mul__(value)

    def __eq__(self, other):
        return isinstance(other, Coord) and self.xyz == other.xyz

    def __repr__(self):
        return f"Coord{self.xyz!r}"


class FakeKDTree:
    def __init__(self, size):
        self.items = []

    def insert(self, co, index):
        self.items.append((co.copy(), index))

    def balance(self):
        pass

    def find(self, co):
        best_co = None
        best_index = None
        best_distance = None
        for candidate_co, candidate_index in self.items:
            distance = (candidate_co - co).length
            if best_distance is None or distance < best_distance:
                best_co = candidate_co
                best_index = candidate_index
                best_distance = distance
        return best_co, best_index, best_distance


class Point:
    def __init__(self, co):
        self.co = co


class ShapeKey:
    def __init__(self, name, coords):
        self.name = name
        self.data = [Point(Coord(*co)) for co in coords]


class KeyBlocks:
    def __init__(self, items=None):
        self._items = []
        for item in items or []:
            self.append(item)

    def append(self, item):
        self._items.append(item)

    def __iter__(self):
        return iter(self._items)

    def __contains__(self, name):
        return any(item.name == name for item in self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, name):
        for item in self._items:
            if item.name == name:
                return item
        raise KeyError(name)

    def names(self):
        return [item.name for item in self._items]


class ShapeKeys:
    def __init__(self):
        self.key_blocks = KeyBlocks([
            ShapeKey("Basis", [(0, 0, 0), (1, 0, 0)]),
            ShapeKey("SmileLeft", [(0, 0.2, 0), (1, 0.3, 0)]),
            ShapeKey("SmileRight", [(0, -0.4, 0), (1, -0.5, 0)]),
        ])


class Mesh:
    def __init__(self):
        self.vertices = [
            Point(Coord(0, 0, 0)),
            Point(Coord(1, 0, 0)),
        ]
        self.shape_keys = ShapeKeys()
        self.updated = False

    def update(self):
        self.updated = True


class Obj:
    type = "MESH"

    def __init__(self):
        self.data = Mesh()
        self.name = "MeshObject"
        self.active_shape_key = None

    def shape_key_add(self, name, from_mix=False):
        key = ShapeKey(name, [(0, 0, 0), (1, 0, 0)])
        if self.data.shape_keys is None:
            self.data.shape_keys = ShapeKeys()
            self.data.shape_keys.key_blocks = KeyBlocks()
        self.data.shape_keys.key_blocks.append(key)
        return key


def install_fake_blender_modules():
    bpy = types.ModuleType("bpy")
    bpy.app = types.SimpleNamespace(
        translations=types.SimpleNamespace(
            pgettext_iface=lambda message: message,
            register=lambda *args, **kwargs: None,
            unregister=lambda *args, **kwargs: None,
        )
    )
    bpy_props = types.ModuleType("bpy.props")
    bpy_props.EnumProperty = lambda **kwargs: kwargs.get("default")
    bpy_props.FloatProperty = lambda **kwargs: kwargs.get("default")
    bpy_props.StringProperty = lambda **kwargs: kwargs.get("default", "")
    bpy_props.BoolProperty = lambda **kwargs: kwargs.get("default", False)
    bpy.props = bpy_props
    bpy.types = types.SimpleNamespace(
        Operator=object,
        Panel=object,
        Scene=type("Scene", (), {}),
    )
    bpy.utils = types.SimpleNamespace(
        register_class=lambda cls: None,
        unregister_class=lambda cls: None,
    )

    mathutils = types.ModuleType("mathutils")
    mathutils.Vector = lambda value: Coord(*value)
    kdtree = types.ModuleType("mathutils.kdtree")
    kdtree.KDTree = FakeKDTree

    sys.modules["bpy"] = bpy
    sys.modules["bpy.props"] = bpy_props
    sys.modules["mathutils"] = mathutils
    sys.modules["mathutils.kdtree"] = kdtree


def load_plugin():
    install_fake_blender_modules()
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


def test_reset_shape_key_to_basis_only_changes_named_key():
    plugin = load_plugin()
    obj = Obj()
    other_before = [point.co.copy() for point in obj.data.shape_keys.key_blocks["SmileRight"].data]

    result = plugin.reset_shape_key_to_basis(obj, "SmileLeft")

    basis = obj.data.shape_keys.key_blocks["Basis"]
    target = obj.data.shape_keys.key_blocks["SmileLeft"]
    other = obj.data.shape_keys.key_blocks["SmileRight"]
    assert [point.co for point in target.data] == [point.co for point in basis.data]
    assert [point.co for point in other.data] == other_before
    assert obj.data.updated is True
    assert result == {"shape_key": "SmileLeft", "reset": 2}


def test_reset_shape_key_to_basis_rejects_basis():
    plugin = load_plugin()
    obj = Obj()

    try:
        plugin.reset_shape_key_to_basis(obj, "Basis")
    except ValueError as exc:
        assert "base shape key" in str(exc)
    else:
        raise AssertionError("Expected Basis reset to fail")


def test_first_shape_key_is_used_as_base_when_basis_name_absent():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys.key_blocks = KeyBlocks([
        ShapeKey("基础", [(0, 0, 0), (1, 0, 0)]),
        ShapeKey("SmileLeft", [(0, 0.2, 0), (1, 0.3, 0)]),
        ShapeKey("SmileRight", [(0, -0.4, 0), (1, -0.5, 0)]),
    ])

    result = plugin.reset_shape_key_to_basis(obj, "SmileLeft")

    base = obj.data.shape_keys.key_blocks["基础"]
    target = obj.data.shape_keys.key_blocks["SmileLeft"]
    assert [point.co for point in target.data] == [point.co for point in base.data]
    assert result == {"shape_key": "SmileLeft", "reset": 2}


def test_first_shape_key_is_rejected_as_reset_target():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys.key_blocks = KeyBlocks([
        ShapeKey("基础", [(0, 0, 0), (1, 0, 0)]),
        ShapeKey("SmileLeft", [(0, 0.2, 0), (1, 0.3, 0)]),
    ])

    try:
        plugin.reset_shape_key_to_basis(obj, "基础")
    except ValueError as exc:
        message = str(exc)
        assert "base shape key" in message
        assert "first shape key" in message
        assert "set the base shape" in message
    else:
        raise AssertionError("Expected first shape key reset to fail")


def test_explicit_base_shape_key_overrides_first_shape_key():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys.key_blocks = KeyBlocks([
        ShapeKey("ImportedFirst", [(9, 9, 9), (8, 8, 8)]),
        ShapeKey("基础", [(0, 0, 0), (1, 0, 0)]),
        ShapeKey("SmileLeft", [(0, 0.2, 0), (1, 0.3, 0)]),
    ])

    result = plugin.reset_shape_key_to_basis(obj, "SmileLeft", base_shape_key_name="基础")

    base = obj.data.shape_keys.key_blocks["基础"]
    target = obj.data.shape_keys.key_blocks["SmileLeft"]
    assert [point.co for point in target.data] == [point.co for point in base.data]
    assert result == {"shape_key": "SmileLeft", "reset": 2}


def test_explicit_base_shape_key_is_rejected_as_reset_target():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys.key_blocks = KeyBlocks([
        ShapeKey("ImportedFirst", [(9, 9, 9), (8, 8, 8)]),
        ShapeKey("基础", [(0, 0, 0), (1, 0, 0)]),
        ShapeKey("SmileLeft", [(0, 0.2, 0), (1, 0.3, 0)]),
    ])

    try:
        plugin.reset_shape_key_to_basis(obj, "基础", base_shape_key_name="基础")
    except ValueError as exc:
        assert "base shape key" in str(exc)
    else:
        raise AssertionError("Expected explicit base reset to fail")


def test_missing_base_error_explains_cause_and_next_action():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys.key_blocks = KeyBlocks()

    try:
        plugin.reset_shape_key_to_basis(obj, "SmileLeft")
    except ValueError as exc:
        message = str(exc)
        assert "base shape key" in message
        assert "first shape key" in message
        assert "Basis/基型/基础" in message
    else:
        raise AssertionError("Expected missing base reset to fail")


def test_add_missing_arkit_shape_keys_adds_only_missing_keys():
    plugin = load_plugin()
    obj = Obj()
    obj.shape_key_add(name="BrowInnerUp", from_mix=False)

    result = plugin.add_missing_arkit_shape_keys(obj)

    names = obj.data.shape_keys.key_blocks.names()
    assert len(plugin.ARKIT_SHAPE_KEYS) == 52
    assert names.count("BrowInnerUp") == 1
    assert "TongueOut" in names
    assert result["added"] == 51
    assert result["skipped"] == 1


def test_arkit_shape_key_order_uses_site_groups_with_paired_sides():
    plugin = load_plugin()

    assert all(name[0].isupper() for name in plugin.ARKIT_SHAPE_KEYS)
    assert plugin.ARKIT_SHAPE_KEYS[:5] == [
        "BrowDownLeft",
        "BrowDownRight",
        "BrowInnerUp",
        "BrowOuterUpLeft",
        "BrowOuterUpRight",
    ]
    assert plugin.ARKIT_SHAPE_KEYS[5:19] == [
        "EyeBlinkLeft",
        "EyeBlinkRight",
        "EyeLookDownLeft",
        "EyeLookDownRight",
        "EyeLookInLeft",
        "EyeLookInRight",
        "EyeLookOutLeft",
        "EyeLookOutRight",
        "EyeLookUpLeft",
        "EyeLookUpRight",
        "EyeSquintLeft",
        "EyeSquintRight",
        "EyeWideLeft",
        "EyeWideRight",
    ]
    assert plugin.ARKIT_SHAPE_KEYS[-6:] == [
        "CheekPuff",
        "CheekSquintLeft",
        "CheekSquintRight",
        "NoseSneerLeft",
        "NoseSneerRight",
        "TongueOut",
    ]


def test_convert_arkit_shape_key_names_keeps_directional_exceptions():
    plugin = load_plugin()
    obj = Obj()
    key_blocks = obj.data.shape_keys.key_blocks
    key_blocks.append(ShapeKey("BrowDownLeft", [(0, 0, 0), (1, 0, 0)]))
    key_blocks.append(ShapeKey("EyeBlinkRight", [(0, 0, 0), (1, 0, 0)]))
    key_blocks.append(ShapeKey("MouthLeft", [(0, 0, 0), (1, 0, 0)]))
    key_blocks.append(ShapeKey("JawRight", [(0, 0, 0), (1, 0, 0)]))

    result = plugin.convert_arkit_shape_key_names(obj, to_symmetrical=True)
    names = key_blocks.names()
    assert "BrowDown_L" in names
    assert "EyeBlink_R" in names
    assert "MouthLeft" in names
    assert "JawRight" in names
    assert "Smile_L" in names
    assert "Smile_R" in names
    assert result["renamed"] == 4

    result = plugin.convert_arkit_shape_key_names(obj, to_symmetrical=False)
    names = key_blocks.names()
    assert "BrowDownLeft" in names
    assert "EyeBlinkRight" in names
    assert "MouthLeft" in names
    assert "JawRight" in names
    assert "SmileLeft" in names
    assert "SmileRight" in names
    assert result["renamed"] == 4


def test_visible_labels_do_not_append_source_language():
    plugin = load_plugin()

    assert plugin.bl_info["name"] == "Shape Key Helper"
    assert plugin.bl_info["version"] == (1, 14, 4)
    assert plugin.bl_info["blender"] == (4, 2, 0)
    assert plugin._ui_label("Auto Mirror", language="zh_HANS") == "自动镜像"
    assert plugin._ui_label("Batch Mirror", language="zh_HANS") == "批量镜像"
    assert plugin._ui_label("Auto Mirror", language="en_US") == "Auto Mirror"


def test_base_shape_settings_are_collapsed_by_default():
    plugin = load_plugin()
    import bpy

    plugin.register()
    try:
        assert bpy.types.Scene.shape_key_mirror_base == ""
        assert bpy.types.Scene.shape_key_mirror_show_mirror_tools is True
        assert bpy.types.Scene.shape_key_mirror_show_utility_tools is True
        assert bpy.types.Scene.shape_key_mirror_show_base_settings is False
        assert bpy.types.Scene.shape_key_mirror_modifier == ""
    finally:
        plugin.unregister()


def test_base_shape_error_opens_base_settings():
    plugin = load_plugin()
    obj = Obj()
    obj.active_shape_key = obj.data.shape_keys.key_blocks["Basis"]
    scene = types.SimpleNamespace(
        shape_key_mirror_base="",
        shape_key_mirror_show_base_settings=False,
    )
    context = types.SimpleNamespace(object=obj, scene=scene)
    reports = []
    operator = plugin.OBJECT_OT_shape_key_mirror_reset_active()
    operator.report = lambda levels, message: reports.append((levels, message))

    result = operator.execute(context)

    assert result == {"CANCELLED"}
    assert scene.shape_key_mirror_show_base_settings is True
    assert reports and "base shape key" in reports[-1][1]


def rounded_coords(key_block):
    return [
        (round(point.co.x, 6), round(point.co.y, 6), round(point.co.z, 6))
        for point in key_block.data
    ]


def test_repair_mesh_symmetry_centers_basis_and_preserves_shape_key_deltas():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys.key_blocks = KeyBlocks([
        ShapeKey("Basis", [(-0.9, 0, 0), (1.1, 0, 0), (0.1, 1, 0)]),
        ShapeKey("Smile", [(-0.9, 0.2, 0), (1.2, 0.3, 0), (0.1, 1.5, 0)]),
    ])

    result = plugin.repair_mesh_symmetry(obj, tolerance_percent=0.5)

    basis = obj.data.shape_keys.key_blocks["Basis"]
    smile = obj.data.shape_keys.key_blocks["Smile"]
    assert rounded_coords(basis) == [(-1.0, 0, 0), (1.0, 0, 0), (0.0, 1, 0)]
    assert rounded_coords(smile) == [(-1.0, 0.2, 0), (1.1, 0.3, 0), (0.0, 1.5, 0)]
    assert result["changed_vertices"] == 3
    assert round(result["center_shift_x"], 6) == -0.1
    assert result["shape_keys_adjusted"] == 2
    assert obj.data.updated is True


def test_repair_mesh_symmetry_works_without_shape_keys():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys = None
    obj.data.vertices = [
        Point(Coord(-0.8, 0, 0)),
        Point(Coord(1.2, 0, 0)),
    ]

    result = plugin.repair_mesh_symmetry(obj, tolerance_percent=0.5)

    assert rounded_coords(types.SimpleNamespace(data=obj.data.vertices)) == [(-1.0, 0, 0), (1.0, 0, 0)]
    assert result["shape_keys_adjusted"] == 0
    assert round(result["center_shift_x"], 6) == -0.2


def test_repair_active_shape_key_self_symmetry_copies_one_edited_side():
    plugin = load_plugin()
    obj = Obj()
    obj.data.shape_keys.key_blocks = KeyBlocks([
        ShapeKey("Basis", [(-1, 0, 0), (1, 0, 0)]),
        ShapeKey("Smile", [(-1, 0, 0), (1.2, 0.3, 0)]),
    ])

    result = plugin.repair_active_shape_key_self_symmetry(obj, "Smile", tolerance_percent=0.5)

    smile = obj.data.shape_keys.key_blocks["Smile"]
    assert rounded_coords(smile) == [(-1.2, 0.3, 0), (1.2, 0.3, 0)]
    assert result["shape_key"] == "Smile"
    assert result["changed_relations"] == 1
    assert obj.data.updated is True


if __name__ == "__main__":
    test_reset_shape_key_to_basis_only_changes_named_key()
    test_reset_shape_key_to_basis_rejects_basis()
    test_first_shape_key_is_used_as_base_when_basis_name_absent()
    test_first_shape_key_is_rejected_as_reset_target()
    test_explicit_base_shape_key_overrides_first_shape_key()
    test_explicit_base_shape_key_is_rejected_as_reset_target()
    test_missing_base_error_explains_cause_and_next_action()
    test_add_missing_arkit_shape_keys_adds_only_missing_keys()
    test_arkit_shape_key_order_uses_site_groups_with_paired_sides()
    test_convert_arkit_shape_key_names_keeps_directional_exceptions()
    test_visible_labels_do_not_append_source_language()
    test_base_shape_settings_are_collapsed_by_default()
    test_base_shape_error_opens_base_settings()
    test_repair_mesh_symmetry_centers_basis_and_preserves_shape_key_deltas()
    test_repair_mesh_symmetry_works_without_shape_keys()
    test_repair_active_shape_key_self_symmetry_copies_one_edited_side()
    print("shape key reset tests passed")
