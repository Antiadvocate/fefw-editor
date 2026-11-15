# Polish Test 1: early travel and first audiences

Build: **FEFW-Polish-Test-1**, branch `feature/polish-audiences`.
The header says **Polish Test 1**; `BUILD.txt` identifies the exact source
commit and CI run. No new Python dependencies. Extract to a fresh directory
and launch **that directory's `editor.py`** with your working environment.
See [setup](source-setup.md) if needed.

This run tests four early-access destinations and the first-audience condition
for every god. Six gods have editable flags; Fortuna has no such condition.
Accepted Tutorials, blessing EXP, Open and original Fast travel behavior are
included, with the eight screenshot-confirmed destination-name corrections.

## Prepare

1. Keep your accepted **B0** save folder untouched. Make a disposable working
   folder for each case. Close the game before editing; close the editor before
   loading the edited save in game. Keep route mirroring unchecked.
2. Use **Leda Part I Chapter 9 / fefw-recomp-0.1.5**. We are testing access
   before the intended story point; do not change the chapter or route.
3. Start each destination and each god from a fresh B0 copy. Do not stack new
   travel flags with audience changes. Keep a before copy and the game's
   resulting save outside the live save folder, named by the case below.
4. Load the exact edited slot. If the game saves into another slot, retain
   that slot and note its name. Record environment changes and Python version.
5. For an unexpected cutscene, forced quest/chapter change, wrong scene,
   inability to leave, crash or hang, stop that case and return to B0. Keep
   the before file and any available after file; do not carry the state forward.

No need to repeat the whole earlier TUT/BLESS/OPEN/FT suites. Each case below
has a separate **storage result** and **game observation**. A persistent flag
without a visible effect is useful evidence, not proof that access is unlocked.

## POL-01 — Build and baseline

Check the header's build name and Open button. On Blessings, all seven gods,
the First audience column, form and horizontal scrollbar should be readable.
Select Fortuna: **Not required**, disabled audience checkbox. Select Mars or
Kalla: **Recorded (1)** and checked. The other four ordinary gods should show
**Not recorded** and unchecked in B0. Record differences if using another base.

Fast travel should show **16 of 20** available, **4 experimental**, and 14 other
records preserved in this reference. Scroll down to all four experimental rows;
they should be Absent. Existing names include Arena Plaza, Shopping Arcade,
City Streets, Upper/Lower Temple Row, Entertainment District, Port and Lowtown.
Check both tabs at your normal window size and the minimum size. Capture the
Blessings baseline and the four new travel rows.

## POL-02 — Controls, history and mirroring

On a disposable copy, select Mars and turn the audience checkbox off. Expect
Not recorded and an unsaved change. Ctrl+Z restores Recorded (1), Ctrl+Y removes
it again. Save, Reload and check off persists. Turn it back on, save/reload.
EXP, selected blessings and Divine Sand should retain their baseline values.

With route mirroring enabled, attempting an audience toggle must refuse the
change and return the checkbox to its stored state. Test the same refusal with
an experimental destination. If mirroring is disabled because there is only
one slot, report **BLOCKED (single slot)** for those two substeps.

Turn mirroring off. Add Aurora's garden, Undo, Redo, Save and Reload; verify
Absent/Available transitions and the count 16/17 of 20. Remove it and save.
Do not use this mixed editor-exercise save for the isolated game cases.

## FTX-01–04 — One additional destination per case

Names below are provisional translations. Use the hash to find the correct row
and report its exact English game-menu label. All four are expected Absent in B0.

| Case | Editor label | Hash |
|---|---|---|
| FTX-01 | Aurora's garden | `1e4d4a23` |
| FTX-02 | Aurora's private room | `38574e83` |
| FTX-03 | Salamis Guesthouse | `efb57d93` |
| FTX-04 | Yu-Fas Temple | `65411bed` |

Repeat this sequence separately for every row:

1. Fresh B0 copy. Add only this destination. Save/Reload: **Available (1)**,
   **17 of 20**. Other three experimental rows remain Absent. Preserve this
   edited pre-load file as `Auto (FTX-01 before)` (substitute the case ID).
2. Load in game and inspect the Base Map before moving. Record whether the
   destination is listed, its exact name, and whether it is selectable. Capture
   the menu. If unavailable, report the message/condition; do not add more flags.
3. If selectable, travel there. Capture arrival and confirm the place fits the
   label. Record any automatic dialogue, cutscene or quest/facility change.
   Do not talk to a god, progress a quest or spend currency during this check.
4. Leave via ordinary movement or fast travel to a known destination. Record
   whether leaving works. If it does, save/quit and reopen the game's written
   slot in the editor. Check the flag, other travel entries and chapter remain
   as expected. Keep the output as `Auto (FTX-01 after)`.
5. On a copy of that result, while positioned away from the experimental area,
   remove this destination, save and load again. Check whether it disappears
   before moving. Save/quit/reopen and record if it stays absent or is restored
   automatically. Keep the result as `Auto (FTX-01 removed)`.

If steps 2–4 are blocked, note where and whether the flag survived the load.
Only save if the scene is functioning normally. We must distinguish a flag
write that works from a destination that the chapter can actually use.

## AUD-01 — Audience baseline and unchanged EXP

Open a fresh B0 copy. Check the baseline against this table and capture the
game's Blessings screen without changing anything:

| God | First audience | B0 EXP | Case |
|---|---|---:|---|
| Mars | Recorded | 25 | AUD-02 |
| Credna | Not recorded | 0 | AUD-03 |
| Kalla | Recorded | 100 | AUD-04 |
| Jurah | Not recorded | 0 | AUD-05 |
| Smyrnos | Not recorded | 0 | AUD-06 |
| Aurora | Not recorded | 0 | AUD-07 |
| Fortuna | Not required | 0 | AUD-08 |

Divine Sand is 100 in B0, and Fortuna/Kalla are selected. Do not change those
fields. If your current baseline differs, record its actual values and use
those as preservation expectations. Do not reset legitimate progress.

## AUD-02–07 — One ordinary god per case, off and on

Use **two independent B0 copies** for each god: one Off and one On. This avoids
carrying game side effects from one condition into the other. Use the same EXP
in both copies; do not use the level buttons or add travel destinations.

1. **Off copy:** select this god, turn the first-audience checkbox off. If it
   is already off, turn on then off as an editor round-trip. Save/Reload and
   confirm Not recorded, with the same EXP/selection/Sand. Retain the pre-load
   file as `Auto (AUD-02 off before)` (substitute the case).
2. Load Off in game. Inspect Blessings before speaking to NPCs. Record the god's
   portrait visibility, Bless Lv, and any visible locked/unlocked indication.
   Capture the screen. Do not select a blessing or talk to the god, since those
   actions could independently change the state. Save/quit, reopen the written
   slot, record the audience state and EXP, and retain `Auto (AUD-02 off after)`.
3. **On copy:** return to fresh B0, turn this god's audience on. If already on,
   turn off then on in the editor. Save/Reload: Recorded (1). Retain
   `Auto (AUD-02 on before)`. Load it and repeat the same observations, save,
   quit and editor check; retain `Auto (AUD-02 on after)`.
4. Compare On against Off: flag persistence and visible effect are separate
   results. Note any automatic first-audience scene, new menu option, resource
   change or recalculation. **No noticeable effect** is a valid finding.

If zero EXP makes the difference impossible to assess, report that first.
Do not combine EXP and audience changes in this initial run; a follow-up can
hold both variants at the same nonzero EXP to isolate the audience effect.

## AUD-08 — Fortuna special case

On a fresh B0 copy, select Fortuna. Expect Not required, a disabled audience
checkbox, and the explanation that no flag will be written. Clicking the
disabled control must not mark the save changed. Check her existing blessing
and EXP remain as before. No additional maximum-EXP test is needed.

## POL-03 — Regression and restoring the baseline

After the isolated cases, restore untouched B0. Confirm Tutorials, Blessings,
Fast travel and World map load, and chapter/quests, existing boon, claimed
deeds and locked stable services match baseline. The accepted original 16
travel entries should still be available. Do not combine successful experiments
into your ongoing save until their reported effects have been reviewed.

## Report

```text
Build / commit from BUILD.txt:
Environment or baseline changes / Python version:
POL-01: PASS / FAIL / BLOCKED
POL-02: PASS / FAIL / BLOCKED (note mirroring substeps)
FTX-01: storage; menu name; visible/selectable; arrival/exit; persistence; removal
FTX-02: storage; menu name; visible/selectable; arrival/exit; persistence; removal
FTX-03: storage; menu name; visible/selectable; arrival/exit; persistence; removal
FTX-04: storage; menu name; visible/selectable; arrival/exit; persistence; removal
AUD-01: baseline matches / differences
AUD-02 Mars: Off persisted? On persisted? Visible difference? EXP unchanged?
AUD-03 Credna: Off persisted? On persisted? Visible difference? EXP unchanged?
AUD-04 Kalla: Off persisted? On persisted? Visible difference? EXP unchanged?
AUD-05 Jurah: Off persisted? On persisted? Visible difference? EXP unchanged?
AUD-06 Smyrnos: Off persisted? On persisted? Visible difference? EXP unchanged?
AUD-07 Aurora: Off persisted? On persisted? Visible difference? EXP unchanged?
AUD-08 Fortuna: PASS / FAIL / BLOCKED
POL-03: PASS / FAIL / BLOCKED
Unexpected cutscenes, quest/facility changes, errors or other observations:
```

Please supply the after saves for each new destination and both audience
variants, plus menu/arrival screenshots and audience-screen differences. Keep
all before copies locally; send them too for any failure or unexpected result.
These private files will be checked without committing them to the repository.
