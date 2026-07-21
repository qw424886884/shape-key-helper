# Contributing

Issues and pull requests are welcome after the first public release.

Before submitting a change:

1. Keep the default public interface in English and update Simplified Chinese
   translations for user-facing text.
2. Run `test_shape_key_reset.py` with Python.
3. Run `test_blender_symmetry_runtime.py` with the latest stable patch of each
   supported Blender minor branch when changing the declared version range.
4. Validate and build the extension with Blender's official extension command
   line:

   ```powershell
   blender --background --factory-startup --command extension validate .
   blender --background --factory-startup --command extension build --source-dir .
   ```

   The manifest build paths must contain only runtime modules and the license.
5. Do not include private scene files, credentials, generated caches, or local
   machine paths.
