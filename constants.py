# Copyright (C) 2026 Fengjishi Studio
# SPDX-License-Identifier: GPL-3.0-or-later




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
