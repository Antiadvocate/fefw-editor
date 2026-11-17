# Cai Part 2 — Test 2

**All Test 2 cases and editor checks passed (17 November 2026).** Together
with Test 1, Cai Part 2 Chapters **1–6** passed opening and next-battle checks
from the natural Part 2 baseline. Both Chapter 5 repair cases passed, as did
conversion from the Cai Part 1 Chapter 4 control to Part 2 Chapter 1.
Other conversion starting states, Obelisk loading and long-term progression
remain untested. The instructions below document the completed tests.

## Chapter 5

The blocked save has Dagsion upper-area access unlocked, but retains the
separate upper-area movement restriction. The game's `A30` access event checks
that restriction. The tested fix clears only that flag. It preserves the
lower-area restriction and all other progression, units and inventory.

| Case | Starting state | Test |
| --- | --- | --- |
| 05A-Resume-UpperMovement | Your returned blocked Chapter 5 save | Resume where you stopped, enter the upper city and follow “Head to Dagda’s temple.” |
| 05B-Reenter-UpperMovement | Fresh Chapter 5 entry from the original Part 2 baseline | Confirm the editor-applied repair survives chapter entry and lets the objective progress. |

Test 05A first, then 05B independently. Save after reaching the next story event
or battle if possible. If blocked, return the save and describe the door/path or
missing interaction. Both cases have now passed; both returned progress saves
reach the Chapter 5 battle with the upper movement restriction cleared.

In the editor, selecting Part 2 Chapter 5 applies the repair automatically.
For an already-blocked save, Functions → Area access → **Dagsion upper-area
movement** applies the same single change when enabled. Do not confuse it with
**Dagsion upper-area access**, which was already unlocked in this save.

## Part 1-to-2 experiment

`00-Part1-Control/Auto` is the unchanged known Cai Chapter 4 free-time save.
It has four units, so this is a different starting roster from your six-unit
natural Part 2 baseline.

`X1-Part1-to-Part2/Auto` is generated from that control using the editor's new
**Try Cai Part 2 entry…** action. It targets Part 2 Chapter 1, retaining the
Part 1 roster, stats, inventory, flags and map records. It sets the part/chapter,
entry sequence and clock, and clears cached restart state. It does not import
another save's progression or grant transition rewards. This case passed:
the returned arrival retains the four-unit roster and the progress save reaches
the Part 2 Chapter 1 battle.

1. Load X1 and confirm the intended Part 2 opening plays.
2. Save at the first controllable point as `X1-arrival`.
3. Complete the first objective or reach the next battle. Save as
   `X1-after-progress` if allowed.
4. Check the retained roster and report anything missing, duplicated or blocked.

Use disposable copies and load each case independently. Do not overwrite your
natural progression saves. Battle saves and the special `Part_Kai_2` handoff
state remain ineligible for this editor action.

To reproduce X1 through the UI, open a copy of `00-Part1-Control/Auto` and choose
**Try Cai Part 2 entry…** beside Story progression. Apply stages the experiment;
Save writes it. Check Undo/Redo, including Undo after saving, then save/reopen and
verify that the displayed part agrees. The action affects only the selected save
and does not automatically create a chapter file. These editor checks passed.

**The action changes the selected save to Part 2, but does not create the
separate `Part_Kai_2` handoff file.** The optional `Chapter_Kai_2_N` chapter
file is different and does not replace it.

## What `Part_Kai_2` contains

This is not the same state as `Chapter_Kai_2_1`. Its live metadata is still
**Cai Part 1 Chapter 12**, dated **10 December 1449**, with a distinct transition
resume state. Its cached restart data contains Chapter 12 entry, free-time and
battle snapshots. That suggests a native handoff for starting Part 2.

The tester observed an inventory carryover screen when Part 2 started and
reported that removing `Part_Kai_2` during entry still seemed fine. This is a
successful short-session observation, not proof that the file is unnecessary
for every loading, replay or later progression case. No automatic creation or
deletion of that file is performed by the editor.

## Return format

- `05A: pass/fail; notes; returned save`
- `05B: pass/fail; notes; returned save`
- `X1: opening pass/fail; first objective pass/fail; roster notes; returned saves`
- `Editor conversion checks: pass/fail; notes`

The editor includes the upstream support-level and convoy updates and retains
Add unit. Main and the preserved unit-creation branch are unchanged by Test 2.
