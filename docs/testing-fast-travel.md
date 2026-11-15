# Milestone 3: Fast travel and Open button acceptance

Candidate: **FEFW-Fast-Travel-Test-1**, branch `feature/fast-travel`.
Read `BUILD.txt` for the exact commit. The window's upstream version is still
1.3.7. This candidate includes the accepted Tutorials and Blessings features,
including the corrected **Fortuna** display name.

**Acceptance completed 2026-11-15:** the player reported OPEN-01–02 and
FT-01–08 passed, with label corrections supplied for FT-01. See the
[validation report](test-results-fast-travel-2026-11-15.md). The instructions
below retain Test 1's original labels for reproducibility. In current source,
**Harbor is Port**, and all 16 English labels match the supplied game screenshots.
The Test 1 ZIP is unchanged. No repeat game run is required for these label edits.

## Prepare once

* Reuse the working Python environment. Extract into a new directory and run
  that directory's `editor.py`. No new dependencies; see [setup](source-setup.md).
* Keep the accepted B0 save/folder as an untouched baseline. Make a working
  copy. Close the game before editing and close the editor before running the
  game. Keep **Also edit this route's other saves** unchecked.
* Continue on Leda Part I Chapter 9 / `fefw-recomp-0.1.5`. Record any changes to
  the previously reported Bazzite 45 environment and record the Python version.
* For game checks, load the exact edited slot, inspect the travel menu before
  moving, then save and quit before reopening in the editor. Record the actual
  slot used if the game writes to a different one.
* Stop on a crash, wrong scene or unexpected progress change; retain the
  failing copy and revert to the untouched baseline. Do not continue that
  failure into the next case.

The English row names below were provisional translations in Test 1; use the hash to
identify a row if the in-game name differs. [All 16 identities](fast-travel.md)
are documented. Do not spend resources or progress a chapter during these checks.

## OPEN-01 — Visible action and file chooser

1. Check **Open…** is visible beside Restore, Snapshot, Reload and Save. Shrink
   the window to its minimum width and confirm Open remains reachable. Restore
   normal width for the rest of testing.
2. Click Open and cancel the chooser. The current save should remain loaded.
3. Click Open again and select the working `Auto` file. Confirm the expected
   folder/slot loads. Check Ctrl+O still opens the same chooser; cancel it.

Expected: both ways work; cancel does not switch slots or lose data. Capture
one screenshot of the new header and Fast travel tab.

## OPEN-02 — Unsaved edits are protected

1. In Fast travel, search `1b5a4006` (Harbor), select it and click
   **Remove selected**. Do not save.
2. Click Open. At the save/discard prompt, choose **Cancel**. The editor should
   stay on this save, with Harbor Absent and an unsaved-change indicator.
3. Undo (Ctrl+Z). Harbor should return to Available (1). If the editor still
   marks the undo as a change, Reload and discard that in-memory state.

Expected: the existing prompt protects edits. No save-file change is needed.

## FT-01 — Baseline and labels

1. Open a fresh B0 copy. All 16 known destinations should be Available (1),
   with 14 other list records preserved in this reference.
2. Confirm the Japanese keys render in Reads as and searches work by label,
   Japanese substring and hash. Use the horizontal scrollbar if needed.
3. In game, capture the whole fast-travel list, scrolling as needed. Match
   what you can to the editor labels and report any different English wording.

Expected: the known reference list is represented accurately. A translation
correction is useful feedback, not grounds to guess a different flag identity.

## FT-02 — Editor remove, undo/redo and save

1. Start from a fresh B0 working copy. Search `1b5a4006`, select Harbor, remove.
2. Confirm Absent / 15 of 16. Undo: Available / 16. Redo: Absent / 15.
3. Save, Reload, and confirm Harbor remains Absent and the other known
   destinations remain Available. Leave this removed copy for FT-03.

Expected: only the selected destination changes. Capture its row after Reload.

## FT-03 — Removal in game and persistence

1. Use FT-02's removed copy. Load away from Harbor; if the baseline starts
   there, prepare a save elsewhere first. Open the travel menu before moving.
2. Confirm the Harbor destination is missing. Do not walk into that area.
3. Save, quit, and reopen the game's written slot in the editor. Harbor should
   still be Absent. Retain this file as `Auto (FT-03)` outside the live folder.

Expected: one destination disappears, with no other missing entries. If it
reappears, record whether this happened immediately on load, when opening the
menu, or after saving. This may identify automatic rediscovery behavior.

## FT-04 — Restore and actually travel

1. Copy the FT-03 result and make Harbor available in the editor. Save/reload
   to confirm Available (1), then close the editor.
2. In game, confirm it is back, travel to it and check the arrival location.
3. Save, quit, and reopen the written slot. Confirm Available (1). Retain it
   as `Auto (FT-04)` outside the live folder.

Expected: the correct destination returns and is usable. Capture the menu and
arrival scene; a visible entry alone does not establish successful travel.

## FT-05 — Temple destination

Use a fresh B0 copy. Repeat FT-02 through FT-04 for **Kalla's Temple**,
hash `b482d5dc`, instead of Harbor. Start away from the temple. Confirm removal,
restore it, travel there, then save/quit/reopen to check persistence. Do not
change blessing EXP, selection or spend Divine Sand during this case.

Expected: the temple's scoped destination flag works; Kalla's blessing and
Divine Sand remain as before. Only send this case's save if there is a failure.

## FT-06 — Stables destination is not a facility unlock

Use a fresh B0 copy, in which the stable facility is locked. Repeat removal
and restoration for **Stables**, hash `2478dd30`. After restoring, travel to
the destination and confirm the facility is still locked. Save/quit/reopen
and check the destination remains Available (1).

Expected: destination availability changes while stable services remain as
before. Stop and report if services become available unexpectedly.

## FT-07 — Guards and no-op

1. With a fresh copy, select an Available row and click Make available again.
   Expect an already-in-that-state message and no new unsaved edit.
2. Check **Also edit this route's other saves**, attempt Remove selected, and
   expect refusal with no row change. Uncheck it afterward. If the checkbox is
   disabled because there is only one slot, report **BLOCKED (single slot)**
   for this substep; do not add saves to your live folder just to enable it.
3. Clear search, focus the destination list and Ctrl+A to select all 16. Try
   Remove selected. It must refuse the whole batch because at least three
   known entries must remain. All 16 should stay Available. Do not save.

## FT-08 — Regression check

On FT-04's restored copy, check the Tutorials/Blessings tabs load correctly,
the world map and chapter/quests still match baseline, and the already accepted
EXP boon/deed claim state remain unchanged. Fortuna should now be named
**Fortuna**, with Special / unknown; its stored EXP should not have changed.
No repeat of the whole TUT/BLESS test suite is requested.

## Report back

```text
Build: FEFW-Fast-Travel-Test-1; commit from BUILD.txt:
Environment changes / Python version:
Route, chapter and recomp version:
OPEN-01: PASS / FAIL / BLOCKED
OPEN-02: PASS / FAIL / BLOCKED
FT-01: PASS / FAIL / BLOCKED; English label corrections:
FT-02: PASS / FAIL / BLOCKED
FT-03: PASS / FAIL / BLOCKED
FT-04: PASS / FAIL / BLOCKED
FT-05: PASS / FAIL / BLOCKED
FT-06: PASS / FAIL / BLOCKED
FT-07: PASS / FAIL / BLOCKED (note individual substeps)
FT-08: PASS / FAIL / BLOCKED
Unexpected behavior:
```

Useful evidence: header/baseline screenshot, the full in-game travel list,
Harbor's removed/restored menu and arrival screenshots, and the two private
case saves `Auto (FT-03)` and `Auto (FT-04)`. Share failures with their exact
steps. Private saves/screenshots will not be committed to the public repository.
