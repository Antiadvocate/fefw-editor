# Cai remaining chapters and complete Tutorials — Test 5

Prepared for the planned 17 November 2026 test session. This is a candidate:
new chapter targets and tutorial entries are not yet accepted in-game.
Run the included `editor/editor.py` using your usual Python setup.

## Use each case independently

Keep a fresh backup of your complete save folder. Close the game before
replacing `Auto`. Load each case using Continue/Auto, not Restart or the
Obelisk. Copy only the chosen case's `Auto`; keep your existing chapter files.
Do not carry one case's resulting save into the next case.

The `controls` directory contains unchanged original inputs. In particular,
`controls/Auto-arrival/Auto` is the successful Cai Chapter 4 Sewers-arrival
control and the baseline for all three tutorial cases. No Leda saves are edited.

## Chapter cases

Start with C5-04, then the remaining chapters in whichever order is convenient.
C5-01 is separate and can be left until last. No Chapter 2/3/9 repeat or Arena
isolation is required for this round.

| Case | Cai chapter | Entry date/time, year 1449 | Source |
|---|---:|---|---|
| C5-01 | 1 | January 24, 02:00 | Supplied native Chapter_Kai_1_1 checkpoint |
| C5-04 | 4 | March 1, 12:00 | Original native Chapter 2 Auto; direct-jump retry |
| C5-05 | 5 | March 14, 12:00 | Successful Chapter 4 Sewers arrival |
| C5-06 | 6 | April 19, 10:00 | Same Chapter 4 arrival |
| C5-07 | 7 | June 9, 12:00 | Same Chapter 4 arrival |
| C5-08 | 8 | July 10, 12:00 | Same Chapter 4 arrival |
| C5-10 | 10 | September 15, 12:00 | Same Chapter 4 arrival |
| C5-11 | 11 | October 16, 08:00 | Same Chapter 4 arrival |
| C5-12 | 12 | November 3, 12:00 | Same Chapter 4 arrival |

For each case:

1. Confirm the chapter opening and scene load normally. Note any missing music,
   controls, objective, NPC or entrance.
2. Save/capture the first available arrival state as `Auto-arrival`.
3. Reach the first main objective and try to trigger the next story event or
   battle. Save the resulting state as `Auto-after-progress` when possible.
4. Report PASS, BLOCKED, CRASH/HANG or BATTLE-ONLY, with a short description.

If a chapter begins with a long battle, confirming the battle loads is useful;
record BATTLE-ONLY rather than spending the session completing it or treating
that as a progression pass. Full chapter completion is not required.

For C5-04 specifically, confirm that the Sewers doorway appears and can be
entered, then try the next objective. This is the direct Chapter 2 → 4 test
that remains outstanding after the successful natural Chapter 3 → 4 test.

All targets >=3 have the Sewers prerequisite enabled. Other old facilities,
Journal permissions, tutorials, quests and party units are not automatically
granted. Record any missing prerequisite before changing it manually. C5-04
retains the original three-unit party; later cases retain the four-unit party
from natural progression. The native Chapter 1 checkpoint has no live party
records yet; its opening scripts must create the initial party.

Cai 2/3/9 retain their previous tested labels; 4 is a conditional pass. Cai
1, 5–8 and 10–12 remain Inferred until their results return. Leda's Chapter 1
exclusion is unchanged. Cai Obelisk behavior is outside this test round.

## Tutorial editor checks

Use a disposable copy of `controls/Auto-arrival/Auto` with route mirroring off.

| ID | Check | Expected editor result |
|---|---|---|
| TUT5-UI01 | Open Tutorials; inspect filters and search for Practice, `TUTO_稽古`, `168a0508` | 218 total entries; 115 present in this control. All searches find the same row. Provisional name filter shows 103 rows. Exact original names/hashes remain available. |
| TUT5-UI02 | Select Practice and Make available; Undo, Redo, Save, reload | Practice becomes Available (2); Undo/Redo works; Save/reload retains it. No other function is unlocked. |
| TUT5-UI03 | Clear filters, Select shown, Remove selected; Save/reload; Select shown, Make available; Undo/Redo, Save/reload | Known list reaches 0, then 218 available entries. Editing remains usable after the empty-list reload. |
| TUT5-UI04 | Search Practice in Flags | English name includes `(provisional)`; Reads as stays `TUTO_稽古`. Flags remains the rightmost tab. |
| C5-UI01 | On a copied Cai save disable Sewers, then choose Chapter 5 or 12 | Chapter and Sewers change in one Undo/Redo step. Save/reload retains both. Other tutorial states are preserved. |

Filters cover category, state and naming evidence. Select shown selects only
the currently visible rows. Ctrl/Shift selection and Ctrl+A remain supported.
Unknown saved values are protected by refusing the whole batch. State 1 is
still Present (1); this build does not claim to distinguish read/unread status.

## Tutorial game cases

Each case starts at the same successful Chapter 4 Sewers-arrival state. It
changes only the tutorial list; its story, party, Functions and other flags
are preserved. Start each independently from its supplied `Auto`.

| Case | Tutorial change | What to check |
|---|---|---|
| TUT5-01-Focused | Adds Practice, Theatre, Thermae, Stables and Third Eye (Cai); 120 total stored records | Locate these five in the game's tutorial menu, open them, and capture their exact English titles. Note any entry hidden by the current story/route. Check that underlying facilities have not been unlocked by these help entries. |
| TUT5-02-All-218 | Makes every catalogue entry available (2) | Open and browse the menu, including later-game/other-route topics. Check for missing names, blank pages or crashes. Sample new entries; no need to read all 218. Record the game's visible count if shown. |
| TUT5-03-Empty | Removes every known tutorial; zero stored records in this source | Check whether the menu is empty or the game regenerates entries. Save, then inspect it in the editor. Report regenerated entries/prompts rather than assuming they are an editor failure. Restore the control if prompts interrupt play. |

For each tutorial case, return a save made in-game as `Auto-after-game` and
briefly report menu visibility, title differences and any unexpected prompts.
Screenshots of the focused five titles are especially useful: 103 labels are
provisional translations, while the original 115 labels retain their earlier
checks. All 218 keys/title IDs were matched to the supplied game tables; this
is complete metadata coverage, not proof that every entry appears in all routes.

## Returning results

Preserve the case folders, for example:

- `C5-05-Chapter-05/Auto-arrival`
- `C5-05-Chapter-05/Auto-after-progress`
- `TUT5-01-Focused/Auto-after-game`

Use `RESULTS-TEMPLATE.txt` and zip the returned case folders. Failed or partial
cases are useful; include the exact objective and what prevented progress.
The original controls and accepted Leda baseline should stay unchanged.
