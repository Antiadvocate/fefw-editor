# Eshmel Part 3 and mirroring: test guide

Use disposable copies in a separate save directory. Run `python editor.py` from
this source folder. Nothing is written until Save. Do not run an older editor
against the test directory at the same time.

## Part 3

Open an Eshmel Part 3 free-time save (or a native chapter-start save). On Player,
Story progression should offer Chapters 1–6 with provisional evidence labels.
Other characters must not offer Part 3. Unknown and battle resume states remain
read-only. This feature does not perform a Part 2-to-3 transition.

For each chapter, test:

1. Apply its start and Save. Confirm the correct chapter and objective load.
2. Save at the first opportunity as `Auto-arrival`.
3. Reach the next story checkpoint or battle; save as `Auto-after-progress` when
   possible. If entry immediately starts a battle, record that instead.
4. Report any blocked route, missing unit, duplicated recruitment, inventory
   anomaly or unavailable interaction, with the objective and screenshot.

Also check Undo/Redo before Save, reopening the edited file, and the optional
`Chapter_Ism_3_N` file creation. Existing chapter files must require overwrite
confirmation and retain numbered backups. Obelisk loading needs a separate test.
No Part 3 progress repair is established yet; Troubleshoot Progress should offer
the upstream issue link when it has no known suggestion.

## Mirroring

Put two matching live saves (same character, part and playthrough) in the test
folder, alongside a chapter checkpoint and a different-character save. Open a
live save and enable “Also edit this route’s other saves”.

Test one reversible change on each of Tutorials, Blessings EXP and audiences,
Fast Travel, Notable Deeds, Boons, Functions and Flags. Both live saves should
change. Undo/Redo should restore both even after switching mirroring off. Save
and reopen both to verify persistence. Chapter checkpoints and other routes,
parts and playthroughs should stay unchanged.

For Add Unit, use supported Part 1 free-time saves. Test a character missing
from both saves, then one already present in a peer. Existing recruited records
must retain their number, stats and inventory. Inactive records should restore
recruitment; new records allocate an unused number in their own save. A duplicate
number or unsupported target should refuse the entire operation without partial
changes. Number edits require a free number in every affected save.

Maps, Support and existing unit/inventory controls retain mirroring. Story
progress and chapter-specific Troubleshoot Progress repairs require mirroring
to be off. Missing files are excluded from peers. If a dirty slot is renamed,
Save should explain that it is missing and keep edits in memory, without a
terminal traceback or silently recreating the file.

## Validation scope

Automated tests cover atomic preflight, multi-slot Undo/Redo, duplicate checking,
flag-list identity, peer selection, chapter state preservation and serialization.
They do not establish in-game acceptance or visual UI acceptance. All six Part 3
editor chapter entry paths remain provisional until tested in-game.
