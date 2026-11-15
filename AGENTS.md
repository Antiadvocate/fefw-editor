# Project instructions

Before every merge into `main`:

- Remove temporary test/build wording from the application header, such as
  "Deeds Hours Test 1". Keep the product name and upstream version.
- Add newly established English names to the Flags catalogue. The Name column
  shows English; Reads As preserves the exact original Japanese identifier.
  Never translate identifiers used for hashing or invent unrecovered names.
- Run `python build_flag_names.py --refresh-labels`, review the label changes,
  then run `python build_flag_names.py --check-labels` and relevant tests.
- Keep Flags as the furthest-right tab. Preserve evidence labels such as
  Inferred when behaviour has not been tested; header cleanup is not acceptance.
- Keep private saves, screenshots, videos and game binaries out of Git.

These are standing user requirements, not a separate permission gate. Follow
the user's existing authorization to publish and merge their branches.
