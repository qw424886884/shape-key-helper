# Changelog

All notable changes to Shape Key Helper are documented here.

## [1.14.4] - 2026-10-04

- Fixed loss of shape-key multi-selection and edit-lock states when using
  Apply Modifier Keep Shape Keys, preserving each property where supported
- Passed runtime regression tests on Blender 4.2.9, 4.3.2, 4.4.3, 4.5.12 LTS,
  5.0.1, 5.1.2, and 5.2.2 LTS
- The separately reported mouse drag/reorder issue has not yet been reproduced
  and is not claimed as fixed in this release

## [1.14.3] - 2026-07-21

- Expanded the declared minimum version to Blender 4.2 LTS
- Verified the complete runtime regression suite in Blender 4.2.9, 4.3.2,
  4.4.3, 4.5.12 LTS, 5.0.1, 5.1.2, and 5.2.0 LTS without version-specific
  code paths

## [1.14.2] - 2026-07-18

- Reorganized the extension into focused modules for core shape key operations,
  modifier handling, ARKit, VRM, operators, UI, translations, and registration
- Reduced the release package to runtime files and the required license
- Switched release packaging to Blender's official extension build command

## [1.14.1] - 2026-07-17

- Renamed the public extension to Shape Key Helper
- Added Blender Extensions manifest and package entry point
- Preserved shape key drivers, animation actions, active index, mute states,
  vertex groups, relative-key chains, and absolute shape keys when applying a
  modifier
- Added transactional rollback when shape key rebuilding fails
- Changed the default public interface and reports to English with Simplified
  Chinese translations
- Replaced proprietary header text with GPL-3.0-or-later licensing

## [1.14.0] - 2026-06-26

- Added mesh symmetry repair without deleting vertices or changing UVs
- Added active shape key self-symmetry repair
- Added apply modifier while keeping shape keys
- Reorganized the panel into mirror, utility, VRM, and ARKit sections
