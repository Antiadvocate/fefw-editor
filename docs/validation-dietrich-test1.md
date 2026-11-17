# Dietrich Test 1 — validation, 2026-11-17

## Automated results

- Full unittest discovery with private Dietrich captures and game tables:
  **232 tests, 181 passed, 51 skipped**. Skips require other historical private
  fixtures absent from this workspace. No failures.
- Recovered Cai Test 5 source controls: **2 additional private regression tests
  passed**, covering the twelve earlier chapter/tutorial exports, Chapter 1
  year and the Cai timeline dates.
- Dietrich: all five native sources validate and support all twelve target
  edits (60 combinations). Four captured sequence IDs independently anchor
  the rule; Chapters 2–12 dates match timeline title rows.
- The twelve packaged cases pass export/reopen, checksums, all outer summary
  mirrors, idempotence, flag/tutorial preservation and source-byte checks.
- Controller-level UI tests pass: route switching during dialogs, unsupported
  routes and resume states, Undo/Redo, Save-only chapter creation, overwrite
  cancellation/confirmation, backup preservation and wrong-route file guards.
- `build_flag_names.py --refresh-labels` and `--check-labels` pass. Review finds
  66 English flag-label changes (including removed provisional suffixes and
  Mentoring); exact original identifiers and every non-label field remain.
- All 218 tutorial key/hash/title-ID/source/offset records match the baseline.
  The screenshots support 180 visible names, 61 corrections and five categories;
  38 titles stay provisional. No save-state semantics changed.
- `git diff --check` passes. The application header is unchanged; Flags remains
  the final tab. No private save, screenshot or game binary is included in Git.

There was no live visual Tk desktop test in this environment: it has no usable
X display, and a local X server could not open its sockets. The editor UI checks
above exercise controller behavior, not visual layout. The kit guide includes
short manual UI checks. Dietrich game progression and Obelisk loading have not
been tested; all twelve targets remain **Inferred**.
