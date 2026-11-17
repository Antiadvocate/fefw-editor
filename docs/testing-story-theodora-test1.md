# Theodora story — Test 1

Theodora Part 1 Chapters 1–12 are **Inferred — game test pending**. This kit
contains the updated source editor and twelve independent generated Autos.
Previous Leda, Cai and Dietrich results remain accepted; there is no need to
repeat them or the tutorial-name checks for this round.

## Start here

1. Close the game and back up the complete working save directory. Test in a
   disposable copy, keeping any other files the game needs.
2. Start with `T1-03-Chapter-03`. Copy only its `Auto` into that test directory,
   then use Continue/Auto. Let the opening run and try the next main story
   event or battle.
3. Test `T1-02`, then `T1-01`, then Chapters 4–12. Load each case's packaged
   Auto independently; do not create the next test by progressing the last one.
   A blocked early chapter does not prevent testing the later cases.
4. Where saving is possible, return `Auto-arrival` and `Auto-after-progress`
   inside the corresponding case folder. For a chapter that immediately moves
   to the next one, report that transition; a second save is not required.
5. For any failure, note the objective and exact block and include a screenshot
   if useful. If you try a manual unlock, keep the original failed save and
   return the edited version separately as `Auto-after-editing` with the changes.

Every generated case starts from the supplied Chapter 3 Auto. All preserve its
three party units, money, flags, tutorials, facilities, quests and map state.
Selection does not recreate the units or unlocks of a naturally played campaign.

Chapters 1/2 deliberately test **backward replay** with that existing party.
The native Chapter 1 checkpoint has no live units before its opening. If an
early replay fails, optionally try the matching `Control-Chapter-01`, `02` or
`03`: these are the untouched native checkpoint bytes, already named `Auto`.
Keep control results separate. A native-control pass does not accept replay.
`00-Native-Control` also retains all four original files under their original
names. Do not copy this entire folder over a generated case.

## Entry clocks

These are the clocks set before the opening scripts run; scripts may advance
them. Chapters 1/2 must return to 1446 and Chapter 3 onward to 1449.

| Case | Chapter | Entry date | Time |
| --- | ---: | --- | --- |
| T1-01-Chapter-01 | 1 | 1446-02-01 | 12:00 |
| T1-02-Chapter-02 | 2 | 1446-02-13 | 12:00 |
| T1-03-Chapter-03 — first | 3 | 1449-02-04 | 07:00 |
| T1-04-Chapter-04 | 4 | 1449-03-01 | 12:00 |
| T1-05-Chapter-05 | 5 | 1449-03-07 | 20:00 |
| T1-06-Chapter-06 | 6 | 1449-03-21 | 23:00 |
| T1-07-Chapter-07 | 7 | 1449-04-21 | 05:00 |
| T1-08-Chapter-08 | 8 | 1449-06-01 | 12:00 |
| T1-09-Chapter-09 | 9 | 1449-07-01 | 12:00 |
| T1-10-Chapter-10 | 10 | 1449-08-25 | 12:00 |
| T1-11-Chapter-11 | 11 | 1449-09-17 | 12:00 |
| T1-12-Chapter-12 | 12 | 1449-10-16 | 10:00 |

## Theodora editor checks

Run the included editor as usual (`python3 editor.py` from the `editor`
directory). Use a separate disposable copy of `00-Native-Control`.

| ID | Action | Expected |
| --- | --- | --- |
| T1-UI01 | Open Auto → Player → Story progression; inspect then cancel | Theodora warning; Chapters 1–12 all Inferred; cancel changes nothing |
| T1-UI02 | Apply Chapter 2, Undo, Redo; then apply Chapter 3 | Chapter 2 uses 1446, Chapter 3 uses 1449; history restores the prior chapter/date; party and tutorials preserved |
| T1-UI03 | Select Chapter 2 with “Create a chapter start file”; Apply; Save | Apply writes nothing; Save asks before replacing `Chapter_Seo_1_2` and keeps its backup; cancelling leaves files unchanged |
| T1-UI04 | Reload saved Auto and `Chapter_Seo_1_2` | Both show Theodora Part 1 Chapter 2; no other route's chapter file created |

Obelisk discovery/loading is a separate optional check if naturally accessible.
Record it separately from Continue/Auto progression. No Route files are created.

## Evidence and reproduction

Route ID **3**, filename code **Seo**. The native checkpoint sequences are
`e51103b9b4fbaeb2`, `e50d03b9b4f7c59d` and `e509c3b9b4f52324`. Reversing the
FNV-1 suffix `<chapter>_1` gives the same prefix `a0f55a5342799b29` for all three.
The Auto has a later live sequence and is not a chapter-title anchor.

`Timeline_Part1_Seo.bin` SHA-256:
`964da5cf80e6b5385c9bb8c21e706b201b1f6154aa62c26b600970dd852a6741`.
Title rows `MCID_1_SEO_title01`–`12` establish twelve chapter entries. Chapter 1
inherits 1446-02-01 from the route start and matches the native checkpoint;
Chapter 2 inherits that year. Chapter 3 explicitly sets 1449. Later chapter
titles supply the month/day/time and inherit 1449. Preceding action 84 remains
unrecovered and is not proof of native checkpoint-file creation.

```bash
python research/story_timeline_report.py /private/GameData --route theodora
python research/theodora_test_kit.py /private/Theodora /fresh/test-saves
```

The builder checks all four source fingerprints and three native anchors,
source immutability, twelve exports/reopens, summary mirrors, entry clocks,
idempotence, unchanged flags/tutorials, and unrelated normalized roots. The
entry engine additionally checks every other GameUserData byte. Native control
copies retain their original bytes. Private saves and game binaries are not in
Git or needed at editor runtime. These checks establish file integrity, not
opening, objective, Obelisk or full-campaign acceptance.
