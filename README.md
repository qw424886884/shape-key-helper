# Shape Key Helper

[简体中文](README_zh_CN.md)

Shape Key Helper is a Blender extension for mirroring shape keys, repairing
symmetry, and applying modifiers without losing existing shape keys.

![Shape Key Helper symmetry repair comparison](media/shape-key-helper-feature-1920x1080.png)

The comparison above shows an asymmetric facial shape key repaired across the
mesh X axis. The original mesh and its UVs stay intact.

## Interface

![Shape Key Helper in Blender 5.1](media/shape-key-helper-zh-cn.png)

The screenshot uses Blender's Simplified Chinese interface. The extension ships
with English source labels and Simplified Chinese translations.

## Features

- Mirror the active left/right shape key automatically
- Choose source and target shape keys manually
- Batch mirror same-side shape keys on the active mesh, creating missing counterparts
- Repair a visually symmetric mesh without deleting half of it or changing UVs
- Repair only the active shape key or reset it to the base shape
- Apply one modifier while preserving relative or absolute shape keys
- Preserve shape key names, order, values, mute states, vertex groups,
  relative-key links, animation actions, and drivers
- Add and repair ARKit 52 shape keys
- Assist VRM0 default expression and Blend Shape Proxy setup
- English interface with Simplified Chinese translations

## Requirements

Version 1.14.6: batch mirroring works on multiple shape keys within the active
mesh. Existing targets are skipped by default; overwrite is optional. The reported
mouse-drag issue is not yet reproduced and is not claimed as fixed.

- Blender 4.2 LTS or newer
- Version 1.14.6 batch workflow verified in Blender 5.2.3 LTS
- Version 1.14.4 previously tested in Blender 4.2.9, 4.3.2, 4.4.3,
  4.5.12 LTS, 5.0.1, 5.1.2, and 5.2.2 LTS
- A mesh object for symmetry and modifier tools
- Existing shape keys for mirror, reset, and active-key repair tools

## Installation

Install Shape Key Helper from its [official Blender Extensions page](https://extensions.blender.org/add-ons/shape-key-helper/)
or search for `Shape Key Helper` in Blender's Get Extensions view.

To install a downloaded release ZIP manually:

1. Download the release ZIP.
2. Open Blender Preferences > Get Extensions.
3. Open the menu and choose Install from Disk.
4. Select the ZIP and enable Shape Key Helper.

## Quick Start

1. Select a mesh and open Object Data Properties > Shape Keys.
2. Expand Shape Key Helper below Blender's shape key panel.
3. Use Model Preparation for small symmetry corrections on an intentionally
   symmetric model, then open Shape Key Operations for mirroring.
4. For batch mirroring, select a clearly named left or right source key, confirm
   the direction, and mirror all same-side keys on this mesh. Missing targets are
   created; existing targets are skipped unless Overwrite Existing is enabled.
5. Use Utility Tools for active-key repair, reset, or modifier application.

## Modifier Safety

The modifier tool evaluates the basis and every shape key through the same
selected modifier. Other visible modifiers are temporarily disabled. The
operation is cancelled before replacing the mesh if evaluated vertex counts
are inconsistent.

Back up production files before topology-changing operations. Shape key NLA
tracks are not rebuilt yet; remove or bake those tracks before applying a
modifier with this tool.

## Privacy and Permissions

The extension does not request network, file, clipboard, camera, or microphone
permissions.

## Maintainer and Open-source Direction

- **Maintainer:** [Feng Ji Shi](https://github.com/qw424886884)
- **Related project:** [Rig Bridge](https://github.com/qw424886884/rig-bridge)

I make my living as a 3D freelancer, not a professional software engineer.
I had studied some code and wanted for years to build tools for problems I
faced in daily production. After months of intensive Codex use, I turned that
experience into two open-source Blender extensions: Rig Bridge and Shape Key Helper.

Codex helps me translate practical 3D knowledge into code; I remain responsible
for testing, review, and releases. I want to keep maintaining these tools and
share Blender workflows that other artists can use in real work.

### Public release snapshot — 16 September 2026

- Public release at the snapshot date: **1.14.3**
- **544 cumulative downloads** on [Blender Extensions](https://extensions.blender.org/add-ons/shape-key-helper/)
- **3 public releases** on [GitHub](https://github.com/qw424886884/shape-key-helper/releases)

These are cumulative download counts observed on the date above, not monthly
downloads, unique users, or active users. See the linked pages for current figures.

## License

Shape Key Helper is licensed under the GNU General Public License v3.0 or
later. See [LICENSE](LICENSE).
