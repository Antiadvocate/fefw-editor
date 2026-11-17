# Milestone 1 test guide: Tutorials and names

Complete [source setup](source-setup.md) first. Python 3.12 is recommended;
record installation or launch problems as SETUP-01 before starting game tests.

## Record the environment

Use a disposable copy of a known working save folder. Close the game and editor
before copying files. Keep the original folder separately as **B0**; do not rely
on an old `.bak` or a snapshot inside the test folder as your only original.
Do not test on the only copy of a playthrough.

Record the editor commit/build, OS, game version, emulator/recomp version or
hardware, route/part/chapter and B0 filename. For this reference test B0 is the
working Leda Part I Chapter 9 save after claiming deeds and buying EXP +10%.
It should contain Foresight and Obelisk Chamber, but neither Drifting Reliquary
nor Third Eye (Cai). If it differs, report that before applying the reference
expectations. Do not change story progress to match this guide.

Run each case from a fresh copy of B0 unless the steps explicitly continue an
edit. Keep **Also edit this route's other saves** off except in TUT-06.

## Test cases

| ID | Steps | Expected result | Evidence |
|---|---|---|---|
| TUT-01 | Open Auto → Tutorials. Search `Foresight`, `戦いの助言`, then `08373a0e`. Check the same entry in Flags. | All searches find Foresight. Flags Name is `Tutorial: Foresight`; Reads as is `TUTO_戦いの助言`. Obelisk is Present (1); the two extras are Absent. | Screenshot of rows; report count. |
| TUT-02 | Select Foresight → Remove selected → Ctrl+Z → Ctrl+Y → Ctrl+Z. | State goes Absent → Available (2) → Absent → Available (2). Other rows stay unchanged. | PASS/FAIL and any unexpected state. |
| TUT-03 | Fresh B0: remove Foresight; Ctrl+S; close/reopen editor. Load this test save in game, inspect Tutorials, save in game, close game and reopen editor. | Foresight is absent after export and after the game saves. Other entries remain. | Screenshot in game and post-game state. |
| TUT-04 | Continue with the TUT-03 copy: make Foresight available, save, reopen, load in game, save and reopen again. | Foresight returns and persists. Boon and deed claim state remain as B0. | Screenshot of Foresight and post-game state. |
| TUT-05 | Fresh B0: make Drifting Reliquary and Third Eye (Cai) available, save and reopen editor. Select both and remove them; save/reopen. Load only this final corrected copy in game. | Both added rows show 2 before removal, then Absent. Foresight remains 2 and Obelisk remains 1. Final in-game list matches B0. | Screenshot of final list. |
| TUT-06 | Fresh B0: check **Also edit this route's other saves**, directly below the Slot selector, and attempt to remove Foresight. Uncheck it, clear selection and click Remove selected. Then select Foresight and Make available. Detailed steps below. | The first action warns and makes no tutorial edit. Empty selection and an already-available row make no change or extra undo entry. | PASS/FAIL for each subcheck; other slots unchanged, or no other slots available. |
| TUT-07 | On the TUT-04 or final TUT-05 result, inspect current chapter/location, blessings, inventory/gold, support progress, fast travel, claimed deeds and EXP +10% Boon. Compare with B0. | No regression caused by these edits. Ordinary play or saving may change time/location; record actions taken. | List any differences; screenshot failures. |

If the game fails to load, crashes, loses progress or rewrites an unexpected
value, stop that case. Preserve the failing copy, restore B0, and report it.
Do not compensate by changing additional flags: that makes the cause harder to
identify. Success in the editor alone is not a game-validation pass.

## TUT-06: checkbox and no-change checks

**Mirroring** is the editor's **Also edit this route's other saves** checkbox,
directly below the **Slot** selector at the top of the window. It normally
copies supported edits to other saves on the same route. The Tutorials page
deliberately refuses edits while it is checked, because its undo history covers
only the selected slot. It is unrelated to display or monitor mirroring.

Close the editor, start it again and open a fresh disposable copy of B0. Keep
the game closed. Do not make unrelated edits during this case.

1. **TUT-06a — edit blocked:** In Tutorials, search for and select **Foresight**.
   Check **Also edit this route's other saves** and click **Remove selected**.
   The status bar at the bottom should say
   **Turn off 'Also edit this route's other saves' for tutorial edits.**
   Foresight must remain **Available (2)**. This warning is a status message,
   not a pop-up. The checkbox may end with **(none here)** when no other live
   slot exists; the warning should still appear.
2. **TUT-06b — empty selection:** Uncheck the checkbox. Ctrl-click the selected
   Foresight row to deselect it, then click **Remove selected**. Expect
   **Select one or more tutorials first.** Nothing should change.
3. **TUT-06c — already available:** Select Foresight and click **Make available**.
   Expect **Selected tutorials already have the requested state.** Foresight
   must remain **Available (2)**.
4. Click the Foresight row and press **Ctrl+Z**. Expect **Nothing to undo.**
   No slot should have an unsaved-change marker from these actions. If there
   are other slots in the test folder, check that none gained that marker.

Leave the checkbox **unchecked** afterwards; its setting is remembered. These
checks should not require saving or loading the game. Report a/b/c and the
undo check separately if any differ. With only one slot, report the other-slot
check as **not applicable** rather than claiming multiple slots were tested.

## Return results

Use PASS, FAIL or BLOCKED for each ID. Include exact steps for a failure rather
than only “doesn't work”. Send save files privately if a comparison is needed;
do not attach personal saves or game dumps to the public repository.

```text
Editor commit/build:
OS:
Game version:
Emulator/recomp version or hardware:
Route / part / chapter:
B0 file:
SETUP-01 (setup / launch):
TUT-01:
TUT-02:
TUT-03:
TUT-04:
TUT-05:
TUT-06:
TUT-07:
Unexpected changes / screenshots:
Post-game save supplied privately: yes/no
```

## Developer checks

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Tests use synthetic object trees. They cover identity corrections, shifting list
indices, preservation of narrow/wide unknown records, unrelated block content,
atomic rejection, absent versus zero, no-op identity, and the real page's
single-slot edit/undo/redo/cache wiring through a display-free harness. They do
not render Tk widgets or run the game. CI defines Python 3.10/3.12 runs on Linux
and Windows; a defined workflow is not evidence those jobs have run.

Optional private-save tests run with `FEFW_TEST_SAVE` set to a local slot
path. It reads that file, writes only into a temporary directory, checks
compression/checksums after edits, and checks that all non-tutorial bytes are
unchanged after pointer relocation is accounted for. The Blessings regression
also edits all seven EXP fields, checks exact two-byte write boundaries and
reloads each serialized result. Never commit the fixture. Blessings game tests
have a [separate guide](testing-blessings.md).

Before merging, review the diff, run the automated checks, render the GUI,
execute TUT-01 through TUT-07 on the supported game build and record results.
Before releasing binaries, verify packaged `tutorial_names.json` loads on each
target platform. The source test candidate is not an upstream release.
