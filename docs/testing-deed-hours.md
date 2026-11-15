# Hours Played experiment — Test 1

Status: **HOURS-01–03 passed by player report**, corroborated by both returned
saves. See the [acceptance report](test-results-deed-hours-2026-11-15.md).
The procedure below records the completed DEED-R14 experiment; no repeat is
requested. The other 14 counters await the next scoped build.

## Prepared inputs

Use the Auto in **Deeds-Hours-20-Test-1.zip** for the game experiment. It is a
disposable copy of the accepted B0-01 baseline with only the Hours Played
counter changed from **17 to 20**. Keep the accepted baseline separately.

| Field | Baseline | Prepared Auto |
|---|---:|---:|
| Hours Played Deed total | 17 | 20 |
| 10-hour milestone claim | Claimed (4) | Claimed (4) |
| 20-hour milestone claim | Not stored | Not stored |
| Karma Shards | 410 | 410 |
| Gold / Renown | 1523 / 6640 | 1523 / 6640 |

Only one payload byte changes. The editor does not create completion or claim
flags, spend/grant Karma, or change separate elapsed-time fields. The game must
decide whether 20 hours completes this Deed. This probe does not adopt the
later all-max Boon test as baseline.

## Game checks

Close the game before installing the prepared Auto using the same save workflow
as the earlier tests. Avoid other reward claims, purchases, battles or quests.

| Case | Action | Record |
|---|---|---|
| HOURS-01 | Load the prepared save and inspect the Hours Played Deeds. Do not claim yet. | Displayed total; whether the 20-hour reward is available; whether the existing 10-hour claim remains claimed. A screenshot is useful. |
| HOURS-02 | Spend about 2–3 minutes in normal unpaused play, then save, quit and reload. Check the same Deed again. | Whether 20 remains, reverts, or changes. Copy that game-resaved slot as **Hours-before-claim**. |
| HOURS-03 | If the 20-hour reward is available, claim only that reward once. Save, quit and reload again. | Expected reward is 20 Karma: 410 → 430, with the reward still claimed after reload. Copy the slot as **Hours-after-claim** and note whether it can be claimed again. |

If the total reverts or the reward is unavailable, stop before claiming and
return the game-resaved file with the observed result. Do not modify other
flags to force completion. The exact filenames do not matter if labelled.

A short session and reload can detect immediate recalculation. They cannot
rule out a later update at a real hour boundary. If all three checks pass, a
subsequent normal hour of play will provide stronger evidence when convenient;
waiting an hour is not required for this first experiment.

## Editor build

**FEFW-Deeds-Hours-Test-1.zip** contains the editor source, without private saves.
Extract into a fresh folder and run editor.py using the existing Python setup.
The header says **Deeds Hours Test 1**. In Notable Deeds, search **Hours played**:
the counter is labelled **Experimental** and has the normal Apply, target-fill,
Undo/Redo, mirroring refusal and claimed-reward warning controls. Flags is last.

The prepared Auto already contains the edit, so no editor change is needed to
run the game checks. To reproduce it manually, open a copy of the accepted
baseline, turn off route mirroring, set Hours played to 20 and save.

## Interpreting the result

- Retained total, refreshed completion and one persistent 20-Karma claim support
  counter-only editing for this Hours Played case.
- Reversion indicates a game writer or dependency overrides the stored counter.
- Retained total without completion shows that persistence alone is insufficient.
- A successful Hours result can support a labelled working assumption for a
  later group of game-wide counters. It does not prove that ranks, conversations,
  blessings, paralogues or every other counter shares the same behavior.

The returned files now establish 20 hours, complete/unclaimed state 2 followed
by claimed state 4, and exactly 20 Karma gained. Broader counter behavior is
still an inference to test, not an observed result of this Hours experiment.
