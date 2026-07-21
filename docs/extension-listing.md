# Blender Extensions Listing

## Identity

- Name: Shape Key Helper
- Extension ID: `shape_key_helper`
- Repository: `qw424886884/shape-key-helper`
- Version: `1.14.3`
- Minimum Blender version: `4.2.0`
- License: GPL-3.0-or-later

## Tagline

Mirror and repair shape keys without busywork

## Short Description

Mirror left and right shape keys, repair mesh or active-key symmetry, and apply
modifiers while preserving shape keys, animation actions, and drivers.

## 中文简介

自动或手动镜像左右形态键，修复模型与当前形态键对称，并在保留形态键、动画
Action 和驱动的情况下应用指定修改器。

## Review Notes

- Runs fully offline and declares no permissions.
- The full runtime regression suite passes in Blender 4.2.9, 4.3.2, 4.4.3,
  4.5.12 LTS, 5.0.1, 5.1.2, and 5.2.0 LTS.
- Uses Blender's Object Data Properties > Shape Keys panel.
- Supports relative and absolute shape keys.
- Cancels and restores the original mesh if modifier reconstruction fails.
- Shape key NLA tracks are rejected before mutation because they are not rebuilt.
