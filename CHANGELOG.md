# Changelog

All notable changes to Shape Key Helper are documented here.

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
