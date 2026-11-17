# Milestone 2 test guide: Blessings EXP

Candidate: **FEFW-Blessings-Test-1**, branch `feature/blessings-exp`.
The initial run passed on 2026-11-15; see the [results](test-results-blessings-2026-11-15.md).
This guide retains the tested build's **Photon** label for reproducibility;
the current editor calls the same special record **Fortuna**, matching the
in-game blessing name. This label correction does not require repeating the run.
Use the commit in the archive's `BUILD.txt` when reporting. This candidate
retains the accepted Tutorials changes and adds EXP editing for all seven gods.
No new dependency is needed: reuse your working Tutorials Python environment,
but launch the newly extracted `editor.py`. See [setup](source-setup.md) only
if needed. The upstream window version number alone does not identify this build.

## Preparation

1. Keep the working **B0** save separately: Leda Part I Chapter 9, with the
   notable deeds already claimed and Increased EXP 10% active. Leave this
   original untouched throughout testing.
2. Close the game and editor before replacing any save. Copy B0 into a
   disposable working folder, retaining the slot filename the game expects
   (for example `Auto`). Keep case labels in parent folders, not in the live
   slot filename.
3. Open that working folder in the new editor. Leave **Also edit this route's
   other saves**, immediately below the Slot selector, **unchecked** except
   for the explicit guard test. This is the mirroring checkbox from TUT-06.
4. Keep a separate result for each case. Start from a fresh B0 copy for every
   case; do not accumulate changes to different gods in the same test.

Environment already reported: Bazzite 45 NVIDIA Edition, KDE Plasma 6.8.2,
Frameworks 6.31.0, Qt 6.11.2, kernel `7.2.15-ogc1.1.fc45.x86_64`, Wayland;
Ryzen 7 5800X3D, 32 GiB RAM, RTX 5080; `fefw-recomp-0.1.5`; Leda Part I
Chapter 9. Reuse these details unless they changed. Please include your Python
version/setup method once; the underlying game data version is still unknown.

## BLESS-01: baseline

Open **Blessings** and compare with B0:

| God | Stored EXP | Level preview | Selected (stored) |
|---|---:|---|---|
| Photon | 0 | Special / unknown | Yes (1) |
| Mars | 25 | 1 | No (0) |
| Credna | 0 | 0 | No (0) |
| Kalla | 100 | 3 | Yes (1) |
| Jurah | 0 | 0 | No (0) |
| Smyrnos | 0 | 0 | No (0) |
| Aurora | 0 | 0 | No (0) |

Divine Sand should be **100 (read-only)**. Check the English names and Japanese
keys in **Reads as**. Send one screenshot of the full page. If your B0 has
changed, record the actual values rather than editing them to match this table.
Photon's disabled level buttons are intentional; its New EXP and Apply EXP
controls become enabled when its row is selected.

## BLESS-02: apply, undo, redo and export

Keep the game closed. On a fresh B0 copy:

1. Select Mars and click **Level 2: 60**. New EXP becomes 60, while the row's
   Stored EXP stays 25. A preset alone must not change the save.
2. Click **Apply EXP**. The row becomes 60 with preview 2.
3. Ctrl+Z → 25 / preview 1; Ctrl+Y → 60 / preview 2.
4. Ctrl+S, close and reopen the editor. Mars must still read 60 / preview 2;
   all other EXP values, selection bytes and Divine Sand must match B0.

The existing editor can retain a dirty marker after undo; compare the actual
values and the reopened result. Start a fresh B0 copy for the next case.

## BLESS-03 to BLESS-09: one god per game test

Use this sequence independently for **each** row in the table below:

1. Fresh B0 copy; select the specified god, type the target **New EXP**,
   click **Apply EXP**, then Ctrl+S. Close/reopen the editor to check export.
2. Close the editor. Put this test slot into the game's test save folder and
   load that exact slot. Note any unexpected tutorial, unlock, deed or other
   message. Do not claim rewards or change other flags to compensate.
3. Inspect the relevant god's blessing level and EXP bar where the game allows
   it. Capture a screenshot. Check the other gods, selected blessing and Divine
   Sand against B0 without spending sand or gaining blessing EXP.
4. Save in game to a known slot, quit the game, and open **that newly written
   slot** in the editor. Record its stored EXP and any other changed fields.
   Keep this post-game save privately under the case ID for comparison.

| ID | God | Set stored EXP to | Expected preview | Expected in-game observation to verify |
|---|---|---:|---|---|
| BLESS-03 | Mars | 61 | 2 | Level 2; check progress just above its 60 threshold |
| BLESS-04 | Credna | 41 | 2 | Level 2; check progress just above its 40 threshold |
| BLESS-05 | Kalla | 51 | 2 | Decrease from level 3 to level 2; check effects/UI recalculate |
| BLESS-06 | Jurah | 61 | 2 | Level 2; check progress just above its 60 threshold |
| BLESS-07 | Smyrnos | 61 | 2 | Level 2; check progress just above its 60 threshold |
| BLESS-08 | Aurora | 51 | 2 | Level 2; check progress just above its 50 threshold |
| BLESS-09 | Photon | 1 | Special / unknown | Observe effect, if any, and whether 1 survives the game save; no expected level |

For the six ordinary gods, unchanged post-game EXP is the intended result
when no EXP-producing activity occurred. The game may display **progress into
the current level**, rather than the editor's stored total; report both.

EXP alone does not grant an audience or temple access. If a god's screen is
unavailable, report **BLOCKED (audience/access)** for visual inspection and
separately report whether the edited EXP survives the game save. Do not mark
visual validation PASS just because the editor reloads successfully. We can
then plan a controlled access test without guessing flags.

**Photon:** report export, load and persistence separately. A reset to 0 is
useful evidence, not a reason to increase the number further. Its threshold
fields are all zero; normal EXP-driven levels are not established.

If a case fails to load, crashes, unexpectedly changes progress or rewrites
values, stop that case, preserve the failing copy and restore B0. Record the
exact action and result. A newly triggered deed could be a game-derived effect
of the EXP change; record its name/state without claiming it.

## BLESS-10: guard and input validation (editor only)

Fresh B0, game closed, select Mars:

1. Enter 60, check **Also edit this route's other saves**, click **Apply EXP**.
   Expect a warning in the bottom status bar and Mars still at 25. This applies
   even if the checkbox says **(none here)**. Uncheck it afterwards.
2. Try `-1`, `65536` and `abc` separately with Apply EXP. Each must be rejected;
   Stored EXP must remain 25. Negative and fractional values are not accepted.
3. Enter 25 and Apply EXP. Expect **This blessing already has the requested
   EXP.** With no other edits since opening, Ctrl+Z should say **Nothing to
   undo** and no new unsaved marker should appear.

The numeric bounds 0 and 65535 are already tested automatically for storage
and byte preservation. There is no request to load an extreme value in game.

## BLESS-11: regression and restore

On one successful ordinary-god post-game result, inspect chapter/location,
roster, inventory/gold, supports, fast travel, the Tutorials corrections,
claimed deeds and Increased EXP 10%. Compare with B0 and list differences.
Ordinary saving can change time/location; note actions taken. Specifically
record newly recalculated deed progress rather than treating it as a reward
that the editor deliberately granted. The editor does not write these fields.

Finally close the game and editor and restore your original working B0. Test
copies are evidence, not the new main playthrough until accepted.

## Report template

```text
Build/commit:
Environment changes from the recorded Bazzite setup:
Python version and launch method:
BLESS-01:
BLESS-02:
BLESS-03 (Mars):
BLESS-04 (Credna):
BLESS-05 (Kalla):
BLESS-06 (Jurah):
BLESS-07 (Smyrnos):
BLESS-08 (Aurora):
BLESS-09 (Photon):
BLESS-10:
BLESS-11:
For each god: exported EXP / in-game level and bar / post-game stored EXP
Unexpected changes and screenshots:
Post-game saves supplied privately:
Original B0 restored: yes/no
```

Use PASS, FAIL or BLOCKED for each case, with a short explanation for partial
coverage. Screenshots of the six ordinary gods plus their post-game EXP are
the main evidence; Photon needs its own persistence result. Personal saves and
game dumps must stay out of public GitHub issues/commits. Optional boundary
testing (for example Mars 24/25, 59/60, 119/120) can follow once this first
all-god run establishes whether the basic model holds.
