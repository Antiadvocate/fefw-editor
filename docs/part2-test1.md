# Cai Part 2 — Test 1

Historical test instructions. Chapters 1–4/6 and editor checks passed; Chapter 5
was blocked. See [Test 2](part2-test2.md) for the repair and conversion experiment.

This test build enables **Cai Part 2 chapters 1–6**, all provisional. It works
from a save already in Part 2. It does not convert Part 1 saves or enable other
routes' Part 2 selectors. The existing Part 1 targets are unchanged.

## What is known and assumed

Chapter 1 uses the sequence from the supplied `Chapter_Kai_2_1` checkpoint.
Replaying it from a progressed save is not yet game-tested. Chapters 2–6 use an
inferred sequence pattern: reversing the observed Chapter 1 hash with the `1_1`
suffix and substituting the chapter number, as in the Part 1 implementation.
One checkpoint anchors this assumption; it does not independently confirm it.

The Part 2 timeline has six title entries. Entry dates are:

| Chapter | Date and time in 1450 | Evidence |
| --- | --- | --- |
| 1 | 1 January, 12:00 | Captured native checkpoint and initial timeline row |
| 2 | 1 February, 12:00 | Timeline date; year inherited provisionally |
| 3 | 1 March, 12:00 | Timeline date; year inherited provisionally |
| 4 | 3 April, 12:00 | Timeline date; year inherited provisionally |
| 5 | 30 April, 09:30 | Timeline date; year inherited provisionally |
| 6 | 30 April, 12:00 | Timeline date; year inherited provisionally |

Each candidate is independently generated from the supplied `Auto-Cai-Part-2`
first-control save. Entry changes the chapter, sequence, date, resume mode and
cached restart state. It preserves the complete roster, inventory, flag stores,
tutorials, facilities, map records and other unrelated objects. Missing later
prerequisites may still block objectives. No guessed bulk unlocks are applied.

## Game checks

Back up the save directory. Use a disposable test directory, and load only one
case at a time; each case contains a file named `Auto`.

1. `00-Native-Arrival`: unchanged control. It should behave as your original save.
2. `P2-01-Chapter-01`: test replay of the captured Chapter 1 entry first.
3. `P2-02-Chapter-02` through `P2-06-Chapter-06`: test each independently, starting
   fresh from that case's `Auto`. Do not carry progress from one case into another.

For each edited case:

- Confirm the intended chapter opens and reaches a playable state.
- Save as soon as you regain control, labelled with the case and `arrival`.
- Complete the first story objective or reach the next story battle/checkpoint.
- Save again if possible, labelled with the case and `after-progress`.
- If it goes straight into battle or does not allow a save, report that; a
  screenshot of the objective or failure is sufficient.
- If blocked, describe where it stops: wrong chapter, loading failure, missing
  marker, locked door/path, unavailable dialogue, or battle deployment issue.
  Keep the returned save before changing flags so the cause remains traceable.

Short progression checks are enough for this pass. No full chapter playthrough
is required. Chapter 6 may lead into finale/spoiler content.

## Editor checks

Open a disposable copy of the natural Part 2 arrival using the included editor.

- Story progression should say **Cai · Part 2**, offer exactly chapters 1–6,
  and show captured/inferred evidence without claiming game acceptance.
- Apply Chapter 2, then Undo and Redo. Check that Part 2 remains selected and
  roster/inventory remain unchanged. Save, reopen, and check the chapter/date.
- Optional: select **Create a chapter start file using this state**. Apply should
  not write it immediately. Saving should create `Chapter_Kai_2_2`, preserving
  Part 1 chapter files. Existing targets must be confirmed and backed up.
- The checkbox tests file creation only. Obelisk loading remains a separate,
  untested game check; it is not needed for this first direct-entry pass.
- Part 1 saves should still show their existing Part 1 choices. Other routes'
  Part 2 saves and battle saves should remain unavailable for story editing.

Add unit/renumbering remains restricted to Part 1 in this build. Existing unit
editing is a separate feature; the reported successful add/level/class tests
are retained as evidence for the cases already tested.

## Results format

`P2-01: opening pass/fail; first objective pass/fail; notes; returned saves.`

Repeat for P2-02 through P2-06, followed by `Editor checks: ...`.

Local serialization, preservation and regression checks do not establish game
acceptance. No Part 2 target is promoted to game-tested until results return.
