# Boons Test 1: existing EXP +10% on/off

This is the first **editable** Boons build. It switches the already-owned
**Increased Exp 10%** Boon on/off. It does not purchase Boons, change tiers,
refund/spend Karma, or edit other Boons. Research 1's BOON-01–04 results remain
accepted; do not repeat that capture round.

## Setup

Extract `FEFW-Boons-Test-1.zip` into a fresh folder and launch its `editor.py`
with the working Python environment. No new dependencies. The header should
say **Boons Test 1**. Use your reported Leda Part I Chapter 9 /
`fefw-recomp-0.1.5` setup, or report any change.

Back up the whole save folder and use a disposable copy/test profile. For
BEDIT-01–05, start with the known working EXP +10% baseline, such as
`B02-EXP-before` (On; Karma 710). For BEDIT-06, use the separate
`B04-reloaded` or `B03-purchase-after` baseline (Weapons Discount 10% purchased;
Karma 410). Keep those branches separate. Restore a copy under its original
slot filename (for example `Auto`); the checkpoint labels are not game slot
names. Load that exact slot and report its original filename.

Turn off **Also edit this route's other saves**. Do not claim Deeds, purchase
other Boons, change tiers or advance story during the state checks. Close the
game before installing an edited save. After a game test, save, wait for it
to finish, quit, and copy the actual resulting slot for inspection.

On the game menu, the left-hand **Increased Exp 20% / Locked** row is the
next tier. The right-hand **10%** is your owned value. Test the ON/OFF state
and continued ownership of 10%, not whether the next tier becomes unlocked.

## Numbered cases

| ID | Steps | Expected / return |
|---|---|---|
| **BEDIT-01 — Display and selection** | Open the baseline and select **Increased Exp, tier 1** on Boons. Check your theme and minimum window size. Search `Increased Exp`, `Experience` and `経験値`. Select tier 2 and a different Boon, then return to tier 1. | 81 reference tiers / 31 groups unfiltered; existing EXP state On and Karma 710 on the supplied baseline. Only **Turn off** is enabled when On. Both buttons disabled for other tiers/Boons. No edit from browsing. Report layout/wording issues. |
| **BEDIT-02 — Editor Off, game persistence** | Click **Turn off**, Save and Reload in the editor. Keep this as **E02-off-edited**. Load that slot in game and inspect Boons without using its in-game toggle. Save/quit and capture **E02-off-game**. Reopen that resulting file in the editor. | Off in editor and game; 10% remains owned; Karma unchanged. Return both slots and the game screenshot. If the game disagrees, send the files before trying to correct it through Flags. |
| **BEDIT-03 — Editor On, game persistence** | On a copy of E02-off-game, select EXP tier 1 and click **Turn on**. Save/Reload; capture **E03-on-edited**. Load it in game, inspect without toggling, save/quit; capture **E03-on-game** and reopen it in the editor. | On throughout, with 10% still owned and Karma unchanged. Return both slots and the game screenshot. |
| **BEDIT-04 — Undo/redo and single-slot guard** | On a fresh baseline copy, turn Off, Undo, Redo, then Undo. Switch to another tier/Boon and confirm buttons are disabled. Return to EXP tier 1, enable **Also edit this route's other saves**, try Turn off, then disable mirroring again. | Off → On → Off → On. Mirroring attempt warns and leaves the state unchanged. No edit to the other slot(s). This can stay unsaved; no capture needed unless it fails. |
| **BEDIT-05 — Actual EXP effect** | Use a normally accessible, repeatable battle checkpoint. Make two copies from the exact same checkpoint: editor On and editor Off. In each, perform the same battle action with the same unit, level, enemy, equipment and outcome. Record unit EXP before/after. Use fresh copies so the second run does not start after the first run's EXP gain. | Compare ordinary unit EXP, not weapon/class EXP. Look for an increase consistent with +10%; rounding can obscure a small award. Send both measured gains and screenshots, including any level crossing or different outcome. If a repeatable battle/checkpoint is unavailable, report **BLOCKED**; no story advance is requested solely for this case. A menu marker alone is not an effect pass. |
| **BEDIT-06 — Weapons Discount toggle mapping (research)** | On the independent purchased-discount baseline, capture **W06-before**. In the game only, switch **Weapons Discount 10%** Off and capture **W06-off**, then On and capture **W06-on**. Save/quit for each capture. Do not buy the displayed next tier. | Return all three actual slots and Off/On screenshots; Karma should stay 410 on the supplied baseline. Note any additional action. If convenient, photograph the same weapon's price in the same shop in both states without buying it; this optional observation helps the next control. The editor's discount row is still read-only. |
| **BEDIT-07 — Regression spot check** | On E03-on-game, inspect Tutorials, Blessings, Fast travel and Deeds, plus Gold/Renown/Karma. | Their values should match the starting baseline, allowing normal game state changes only. No need to repeat the full accepted milestone suites or claim a reward. Report anything unexpected. |

If EXP tier 1 says **Unknown / read-only**, send the save and message. Do not
force its records through Flags. Stored ownership values other than 1, or
disable values other than absent/1, intentionally remain uneditable.

## Return template

```text
Build: Boons Test 1 / source commit from BUILD.txt
Route / chapter / recomp / OS (if changed):
Original loaded slot filename:
BEDIT-01:
BEDIT-02:
BEDIT-03:
BEDIT-04:
BEDIT-05: On gain __; Off gain __; action/unit/levels __; PASS/FAIL/BLOCKED/inconclusive
BEDIT-06: toggle wording; Karma before/off/on; optional weapon price off/on
BEDIT-07:
Other actions / issues:
```

Expected files: E02-off-edited, E02-off-game, E03-on-edited, E03-on-game,
W06-before, W06-off, W06-on. Return the named slot copies, not a substitute
slot the game did not load; complete folders are also welcome if convenient.
The [15 read-only Deeds counters](deeds-follow-up.md) remain queued for their
own build and are not part of this round.
