# Milestone 1 test guide: Tutorials and names

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
| TUT-06 | Fresh B0: turn mirroring on and attempt to remove Foresight. Turn mirroring off, clear selection and click Remove. Then select Foresight and Make available. | Mirroring warns and makes no tutorial edit. Empty selection and an already-available row make no change or extra undo entry. | PASS/FAIL; other slots unchanged. |
| TUT-07 | On the TUT-04 or final TUT-05 result, inspect current chapter/location, blessings, inventory/gold, support progress, fast travel, claimed deeds and EXP +10% Boon. Compare with B0. | No regression caused by these edits. Ordinary play or saving may change time/location; record actions taken. | List any differences; screenshot failures. |

If the game fails to load, crashes, loses progress or rewrites an unexpected
value, stop that case. Preserve the failing copy, restore B0, and report it.
Do not compensate by changing additional flags: that makes the cause harder to
identify. Success in the editor alone is not a game-validation pass.

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

An optional private-save test runs with `FEFW_TEST_SAVE` set to a local slot
path. It reads that file, writes only into a temporary directory, checks
compression/checksums after edits, and checks that all non-tutorial bytes are
unchanged after pointer relocation is accounted for. Never commit the fixture.

Before merging, review the diff, run the automated checks, render the GUI,
execute TUT-01 through TUT-07 on the supported game build and record results.
Before releasing binaries, verify packaged `tutorial_names.json` loads on each
target platform. The source test candidate is not an upstream release.
