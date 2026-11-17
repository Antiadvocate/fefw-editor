# Story progression — Test 1

**Archived test guide:** all twelve progression cases failed. Use the
[Test 2 comparison](testing-story-entry-test2.md) for the next experiment.

The kit contains an editor, **12 independent chapter cases**, an untouched
control and a results template. All cases start from the accepted B0-01
Chapter 9 baseline; existing later unlocks are preserved. They do not become
new baselines merely by being tested.

## Preparation

1. Close the game. Back up the complete current save directory into a new,
   separate directory. Keep the accepted baseline and this backup untouched.
2. Extract the kit. Run `editor/editor.py` using the usual Python setup.
3. For each game test, install only that case's **Auto**, using the same
   working save location as previous tests. Keep the rest of your working
   save folder as usual; do not mix Auto files from different cases. Fully
   close the game before replacing it. Preserve each game-resaved return
   under its case name before moving to the next independent case.
4. Use **Continue / Auto**, not an old chapter checkpoint or battle rewind.
   Those snapshots have deliberately not been rewritten.

## Editor checks

| ID | Action | Expected |
|---|---|---|
| STORY-UI01 | Open a disposable Leda Part 1 Auto; Player → Story progression…; cancel the warning | Exact caution title and all four requested bullets; no edit |
| STORY-UI02 | Continue past the warning; inspect the list; cancel | Chapters 1–12, evidence labels, no edit |
| STORY-UI03 | Apply a different chapter; Undo and Redo | Chapter summary follows each action; units and other fields unchanged |
| STORY-UI04 | Save, reopen, then test Undo/save in the same editing session | Load-screen and live chapter stay consistent; original `.bak` retained and subsequent saves create numbered backups |
| STORY-UI05 | Open the new real **Cai** save, then switch back to Leda | Cai summary is read-only and Story progression button disabled; Leda becomes editable again. Cai file unchanged, including if you try Undo/Redo after switching from an edited Leda slot |
| STORY-UI06 | Enable “Also edit this route’s other saves”; attempt story edit | Refused; no route-wide chapter change |

UI04's Undo history lasts only for the editor session, as in the rest of the
editor. A fresh launch is a reopen check, not a promise of persistent Undo.

## Game checks — one independent case per chapter

For **every case**, perform the user's two acceptance checks:

1. **Load:** the actual chapter starts, rather than just the save label changing.
2. **Next beat:** the next main-story sequence or battle happens. Wait for it
   when the game is in free time; if the opening instead requires a conversation,
   travel or a scripted objective, follow that immediate main-story prompt and
   note what was required. Do not interpret an unavailable Wait command as an
   editor failure by itself.

Then save and reload if possible and return one game-resaved Auto, named with
the case ID. A screenshot is useful for a wrong scene, blocked objective or
unexpected condition; no need to photograph every pass. If it fails, record
where it stopped and retain the failed case's Auto. Do not fix it by enabling
additional flags in the same test; that would make the result harder to isolate.
No full campaign or full battle clear is required for this first acceptance run.

| ID / folder | Target | Load | Next main beat | Save/reload |
|---|---|---|---|---|
| STORY-01-Leda-P1-Chapter-01 | Chapter 1 | Pending | Pending | Pending |
| STORY-02-Leda-P1-Chapter-02 | Chapter 2 | Pending | Pending | Pending |
| STORY-03-Leda-P1-Chapter-03 | Chapter 3 | Pending | Pending | Pending |
| STORY-04-Leda-P1-Chapter-04 | Chapter 4 | Pending | Pending | Pending |
| STORY-05-Leda-P1-Chapter-05 | Chapter 5 | Pending | Pending | Pending |
| STORY-06-Leda-P1-Chapter-06 | Chapter 6 | Pending | Pending | Pending |
| STORY-07-Leda-P1-Chapter-07 | Chapter 7 | Pending | Pending | Pending |
| STORY-08-Leda-P1-Chapter-08 | Chapter 8 | Pending | Pending | Pending |
| STORY-09-Leda-P1-Chapter-09 | Chapter 9 | Pending | Pending | Pending |
| STORY-10-Leda-P1-Chapter-10 | Chapter 10 | Pending | Pending | Pending |
| STORY-11-Leda-P1-Chapter-11 | Chapter 11 | Pending | Pending | Pending |
| STORY-12-Leda-P1-Chapter-12 | Chapter 12 | Pending | Pending | Pending |

Chapter 9 is a useful first comparison with the earlier successful restoration;
the current source is the repaired baseline, so it still needs its own result.
Then test the others in any convenient order. If the control itself fails to
load in the test setup, resolve that before attributing failures to a chapter.

A passing load/next-beat result will establish only those steps on this source
and game version. It will not establish full chapter completion, earlier
prerequisite grants, other routes or long-term safety.
