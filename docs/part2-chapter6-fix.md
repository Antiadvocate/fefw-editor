# Part 2 — remaining routes results and Chapter 6 fix

The 18 returned cases reach their next battles. Leda and Dietrich Chapters 1–6
passed from their Part 1 baselines, as did Theodora Chapters 1–5. Theodora
Chapter 6 reached its battle after the tester manually enabled midtown access.
All 36 returned saves have valid checksums and matching route/part/chapter.
These are opening and next-battle results, not complete playthroughs. The
remaining-route editor checklist has not been separately confirmed.

## Chapter 6 prerequisite

The blocked Theodora arrival has `行動範囲制限_中層` (`16b679c4`) set to 1.
The edited progress save has that restriction removed. This is the existing
**Functions → Area access → Dagsion middle-area movement** control. The same
restriction is already clear in the successful Cai, Leda and Dietrich Chapter 6
arrivals.

Selecting **Part 2 Chapter 6** now enables middle-area movement for all four
routes. It clears only that restriction, preserving other access controls,
story flags, units and inventory. Already-unrestricted cases are unchanged.
Theodora's manual repair and the focused automatic fresh-entry retest both passed
on 18 November 2026. Returned arrival and progress saves validate; both keep the
middle restriction clear and the progress capture reaches the next battle. Part 1 behavior is unchanged.

## Completed focused game check

The package contains an updated editor and `test-saves/Theodora-Chapter6/Auto`.
This fresh Chapter 6 entry is generated from the same original Theodora Part 1
Chapter 3 baseline, through the updated production conversion and chapter writer.

1. Load it using your usual disposable-save procedure.
2. Confirm you can pass the midtown gate and follow **Head to Dagda's cauldron**
   without changing Functions yourself.
3. Reach the next story event/battle and return `Auto-after-progress` if saving
   is available. A pass/fail report is enough if saving is not possible.

The other 17 cases do not need repeating. Existing blocked Chapter 6 saves can
use the same Functions switch; no need to restart the chapter to repair access.

## Separate part files

The tester reports that no separate `Part_Led_2`, `Part_Dit_2` or `Part_Seo_2`
files were created during these conversion tests. The editor intentionally does
not create them, and its warning remains. Native progression may create them,
but the exact trigger has not been established. Optional `Chapter_*_2_N` files
are different. These short tests do not establish all future replay/loading
requirements, so existing part files should be retained.

The fix remains on `feature/part2-story`. Main stays unchanged and keeps its
recent documentation/archive cleanup.
