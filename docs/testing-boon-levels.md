# Boons Test 4: corrected skill keys

Extract FEFW-Boons-Test-4.zip into a fresh folder and launch its editor.py with
the working Python environment. No new dependencies. The header says
**v1.3.9 · Boons Test 4** and **Flags remains the far-right tab**.

Test 3 partly failed because eight skill-EXP groups used full catalogue names.
Brawling and Black-Magic keys now match independent captures of abbreviated
names. The other six aliases follow that pattern and need this game check.
See [the evidence](boon-key-investigation.md).

## Focused game check

1. Open a disposable copy of the accepted baseline in Test 4. Turn off
   **Also edit this route's other saves**, open Boons, use **Set all to max**
   and save. Close the game before writing its save file.
2. Load it in game. Check that Brawling, Black-Magic, White-Magic, Infantry,
   Rider, Heavy, Flier and Authority now show **+3**. Check remaining menu
   entries too, noting any missing/non-maximum group, particularly the six
   blessing-cost Boons not shown in the first failure screenshots.
3. Save in game, quit and reload to check persistence. Return that one
   game-resaved file, with screenshots of any discrepancy. Individual
   before/purchase/Off sets for every group are not needed at this stage.

Do not promote this test save to baseline automatically. No repeat of accepted
Weapons Discount price or earlier EXP battle tests is requested.

## Controls and evidence

| Control | Behavior |
|---|---|
| Set selected tier | Sets that group's owned tier, including before normal purchase requirements |
| Remove Boon | Removes its owned level and retains its independent On/Off marker |
| Turn on / Turn off | Changes activation for the selected, currently owned tier |
| Set all to max | Sets all 31 groups to their catalogue maxima, including hidden search results; retains existing Off states |
| Undo / Redo | Restores one complete action, including bulk max |
| Save | Writes the selected slot with upstream numbered backups |

**Game-tested** labels accepted EXP/Weapons effects. **Save-verified** labels
Brawling/Black-Magic tier 1 purchase/toggle records captured from the game;
it does not assert that this build has passed a game retest. **Inferred**
labels other mappings/tiers. Game cost and Required clears are reference
purchase requirements, not a decoded save-side lock status.

For a Test 3 edited save, incorrect full-name skill records are preserved but
ignored. Missing corrected keys therefore show Not owned. Explicitly setting
a tier or using bulk max writes the corrected key; nothing is migrated merely
by opening a save. Karma and progression are preserved, without refunds.
