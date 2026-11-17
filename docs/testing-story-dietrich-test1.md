# Dietrich story progression — Test 1

This kit adds Dietrich Part 1 Chapters 1–12 as **Inferred — game test pending**.
Cai's chapter/UI/tutorial results are already accepted. No further tutorial
screenshots are needed unless an unresolved title appears during normal play.

## Start here

1. Close the game and back up your complete working save directory.
2. Use a disposable copy of that directory. For each case, replace only its
   `Auto` with the `Auto` inside that case folder. Keep any other files the game
   needs. Do not mix arrival/progression Autos from different cases.
3. Run `D1-04-Chapter-04` first, then `D1-03-Chapter-03`. Use Continue/Auto,
   let the chapter opening finish, then reach the next main story event/battle.
4. If both pass, test 2, 1, then 5–12 independently. Each case begins from its
   own packaged Auto, not from the previous case's progressed state.
5. Save after arrival and again after a meaningful progression step. Return
   them in the case folder as `Auto-arrival` and `Auto-after-progress`, with a
   short pass/fail note. On failure, include the objective and what blocks it.

Chapter 1 uses the native Chapter 1 source, whose live party is initially empty;
let the opening populate it. The remaining cases preserve the Chapter 4 Auto's
party `[4, 13, 5]`, money, units, facilities, quests, map state and 113 tutorial
records. Missing earlier unlocks or under-levelled units may affect play:
chapter selection does not reconstruct a naturally progressed campaign.

`00-Native-Control` contains the untouched Auto and four native checkpoints.
Use it to compare an unexpected result. Keep it separate from generated cases.

## Cases and expected entry clocks

All years are 1449. Clocks below describe entry, before chapter scripts advance.

| Case | Chapter | Month/day | Time | Source |
| --- | ---: | --- | --- | --- |
| D1-04-Chapter-04 — first | 4 | 03/08 | 12:00 | Native Chapter 4 Auto |
| D1-03-Chapter-03 — second | 3 | 02/11 | 12:00 | Native Chapter 4 Auto |
| D1-02-Chapter-02 | 2 | 02/10 | 14:00 | Native Chapter 4 Auto |
| D1-01-Chapter-01 | 1 | 02/10 | 09:00 | Native Chapter 1 checkpoint |
| D1-05-Chapter-05 | 5 | 04/11 | 06:00 | Native Chapter 4 Auto |
| D1-06-Chapter-06 | 6 | 05/04 | 12:00 | Native Chapter 4 Auto |
| D1-07-Chapter-07 | 7 | 05/29 | 20:00 | Native Chapter 4 Auto |
| D1-08-Chapter-08 | 8 | 06/21 | 12:00 | Native Chapter 4 Auto |
| D1-09-Chapter-09 | 9 | 08/10 | 12:00 | Native Chapter 4 Auto |
| D1-10-Chapter-10 | 10 | 09/29 | 12:00 | Native Chapter 4 Auto |
| D1-11-Chapter-11 | 11 | 10/05 | 12:00 | Native Chapter 4 Auto |
| D1-12-Chapter-12 | 12 | 11/04 | 12:00 | Native Chapter 4 Auto |

## Editor checks

Use a separate copy of the native control for these checks.

| ID | Action | Expected |
| --- | --- | --- |
| D1-UI01 | Open Dietrich Auto → Player → Story progression | Dietrich warning; Chapters 1–12 all Inferred; cancel leaves the save unchanged |
| D1-UI02 | Apply Chapter 4, Undo, Redo | Entry clock/state and pending chapter-file choice undo/redo together; only selected save changes |
| D1-UI03 | Select Create a chapter start file, Apply, then Save | No disk write on Apply; Save offers `Chapter_Dit_1_4`, asks before replacing the native checkpoint and backs it up |
| D1-UI04 | Reload saved Auto | Correct Dietrich route/chapter; party, tutorials and feature flags preserved |
| D1-UI05 | Open Theodora, another part, or unsupported event/battle state | Story remains read-only |
| TUT-D1 | Tutorials filters and a search for Mentoring (Cai) | 218 identities: 180 Game title checked, 38 Provisional name; game categories; exact Japanese keys retained |

If naturally available, separately check whether the editor-created
`Chapter_Dit_1_4` appears and loads through the Obelisk. Record that separately
from Continue/Auto progression; neither result proves the other. Route files
are not synthesized by the editor.

## Tutorial screenshots

The 180 confirmed titles need no repeat checks. If a scenario tutorial appears
that is still labelled **Provisional name**, capture its title and, only when
needed to distinguish it, its open page. Include chapter and context. There is
no need to hunt for all 38 during this test.

## Evidence and limits

Native Chapter 1–4 sequences reverse to the same FNV-1 prefix
`13dfaa82ebb06dc7` with suffix `<chapter>_1`. Their clocks validate early entries;
Chapter 1 inherits its date in the timeline, so its native 09:00 clock is used.
Later dates come from `MCID_1_DIT_title05` through `12` in
`Timeline_Part1_Dit.bin` (SHA-256
`3a5ce16361180bdfdad676594cd2a0c73e93700f10c68ecc0d590eac848e59bd`).
The timeline inherits the native 1449 year. Its preceding action 84 is still
unrecovered and is not proof of natural checkpoint creation.

The entry engine changes chapter/sequence, resume context, clock/calendar and
validated restart caches. Unlike Cai, it makes no Sewers or other feature-flag
change. All other normalized roots and other GameUserData content must agree.
`research/dietrich_test_kit.py` checks source fingerprints, four checkpoint
anchors, all twelve exports and summaries, idempotence, unchanged flags/tutorials,
and unchanged source files. These are structural checks, not game acceptance.
