# Part 2 — Leda, Dietrich and Theodora Test 1

There are **18 independent tests: six chapters per route**. Cai Chapters 1–6
already passed; you do not need to repeat them for this package.

All three new routes are **inferred — game tests pending**. The game has one
shared Part 2 timeline, six common chapter titles and dates, and route-specific
events within that timeline. We reuse the entry sequences tested on Cai while
retaining each save's route. Shared structure does not establish that every
route's prerequisites are satisfied.

## What's included

| Folder | Original baseline | Retained units | Tests |
| --- | --- | --- | --- |
| Leda | Part 1 Chapter 9 | 9 | Part 2 Chapters 1–6 |
| Dietrich | Part 1 Chapter 4 | 3 | Part 2 Chapters 1–6 |
| Theodora | Part 1 Chapter 3 | 3 | Part 2 Chapters 1–6 |

Each route has an unchanged `00-Part1-Control/Auto` and six ready-to-load
`P2-XX-Chapter-XX/Auto` files. Each chapter was generated independently from
that route's original Part 1 save. These are **Part 1 conversion tests**, not
captures from naturally reached Part 2. Chapter 1 also tests the conversion
opening. Later chapters let you check access without playing through earlier
battles first.

The candidates retain party, stats, inventory, tutorials, map records and
progression. They change the part/chapter, entry sequence, clock and cached
restart state. Chapter 5 additionally clears the upper-city movement
restriction, using the Cai-tested repair. Its behavior on these three routes
is still inferred. No broad area unlocks, recruited units, transition rewards
or equipment have been added. The small Dietrich/Theodora rosters may make
battles difficult; reaching the next battle is enough for this pass.

## Game checks

Use the same backup-and-copy procedure as the earlier test packs. Load only
one case at a time from a disposable copy; keep your normal saves backed up.

1. For each route, test Chapter 1 first. Confirm the intended protagonist and
   Part 2 opening. Note any inventory carryover screen and whether it completes.
2. At the first controllable point, save and return it as `Auto-arrival`.
3. Follow the objective to the next story event or battle. Return that save as
   `Auto-after-progress` where saving is possible. No need to win the battle.
4. Load Chapters 2–6 **independently**, repeating the arrival/progression check.
   A failed Chapter 1 does not prevent you testing the other prepared cases.
5. For Chapter 5, check the city gate and the “Head to Dagda's temple” objective.
   For Theodora Chapter 1, also check the starting position and movement: the
   shared timeline has a separate Theodora placement event.

On a failure, return the blocked save if possible and give the objective,
location and what prevents progress. A screenshot is useful for a blocked
path or interaction. If a chapter immediately launches into a fight and offers
no save opportunity, just say so.

These files do not create the separate `Part_Led_2`, `Part_Dit_2` or
`Part_Seo_2` handoff files. Optional `Chapter_Led_2_N`, `Chapter_Dit_2_N` and
`Chapter_Seo_2_N` chapter files are different. Cai's successful short test after
removing `Part_Kai_2` does not establish that handoff files are unnecessary in
every case. **Do not remove existing handoff files for this test.** Note whether
any corresponding file was already present when reporting the results.

## Editor checks

Run `editor/editor.py` using your usual Python setup. On disposable copies of
each route's `00-Part1-Control/Auto`:

1. Choose **Try Part 2 entry…**. Check that the warning names the correct route
   and its separate `Part_*_2` file. Cancel once and confirm nothing changes.
2. Apply, Save and reopen. Confirm the same protagonist, Part 2 Chapter 1,
   unchanged unit numbers, party and inventory. No handoff file should appear.
3. Check Undo/Redo, including Undo after Save; save/reopen each state. The
   displayed part should agree with what was saved. Other open saves should
   remain unchanged.
4. In Part 2 Story progression, confirm Chapters 1–6 are selectable and marked
   **Inferred**, including Chapter 5. Cai should still show its tested status.
5. Optionally select “Create a chapter start file using this state” and Save
   in the disposable directory. Check the route-specific `Chapter_*_2_N` name.
   This checks file creation only; Obelisk loading is a separate game test.

## Return format

Keep the route/case folders when zipping saves. For each route, report:

```text
Leda / Dietrich / Theodora:
Chapter 1: opening / carryover / progression; notes
Chapter 2: pass/fail; notes
Chapter 3: pass/fail; notes
Chapter 4: pass/fail; notes
Chapter 5: gate / objective pass/fail; notes
Chapter 6: pass/fail; notes
Editor checks: pass/fail; notes
Separate Part_*_2 file already present: yes/no/unknown
```

The package retains Add unit and the integrated upstream updates. It is built
from `feature/part2-story`; main and `feature/unit-creation` are unchanged.
Successful short tests establish entry and the next story beat, not a complete
playthrough or Obelisk compatibility.
