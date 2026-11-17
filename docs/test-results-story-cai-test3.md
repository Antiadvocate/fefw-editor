# Cai Test 3 — Chapter 3 passed; natural Chapter 4 still blocked

Reported 2026-11-16. The player completed Chapter 3 and progressed naturally
into Chapter 4, where the first objective remained inaccessible. Both supplied
Autos pass container and payload checksums; no external chapter files were
included, which does not establish whether the game created any.

| Capture | Clock | Live sequence | Party |
|---|---|---|---|
| Chapter 3 opening | 1449-02-04 10:00 | `d645768c21a2c3a9` | Three units, numbers 4/6/7 |
| Natural Chapter 4 arrival | 1449-03-01 15:00 | `d63bb68c219adbe2` | Four units, numbers 4/6/7/37 |

Chapter 3 has a full-chapter player-reported pass on this source, with the
Chapter 4 capture corroborating the transition. The fourth unit and multiple
normal Chapter 3 unlocks were gained during play. The Chapter 4 sequence and
clock match the earlier blocked direct skip; naturally completing Chapter 3
alone did not resolve access. The research Chapter 3 candidate remains separate
from the production selector; its accepted result is recorded here.

## Screenshot and exact entrance check

The supplied video screenshot shows **Find the dungeon** at March 1 and an
objective marker on the **Sewers entrance beside the Item Shopkeeper**.
This identifies the walking entrance to inspect; it does not demonstrate that
the Arena spectating or Training services are required.

In `HubDispos/Hub_000.bin`, event group `イベント_A1`, row `0x2fbc10`, label
`A60へ` / `MID_Access_Goto_Sewar` requires:

- Cai's route (`KAI`).
- `既読済` for `MID_LGV_1KAI_c02_LG11_003_m06`.
- One allowed story/free-time phase; the list explicitly includes Cai Part 1
  Chapter 4's first restricted phase.

`Hub.bin` maps `既読済` to **`IsAlreadyRead`**. Cai's Chapter 2 timeline also
references the same dialogue key in the transition into the Sewers section
(row `0x3740`, type 31 with its fabrication marker set). That metadata is not a
decoded implementation of the action and does not by itself establish the save
map used by every script.

The dialogue hash **`0x7d18367a`** is absent from all parsed maps in the native
Chapter 2 Auto, its tested advancement, Chapter 3 opening, natural Chapter 4
arrival, and Chapter 9 advancement. The conversation-history candidate map
contains other completed dialogue IDs as value 1. It is a direct member of the
GameUserData flag-group struct, member key **`0xb631f2c1`**. Its current ordinal
is 4, but the probe locates it structurally with three known dialogue anchors.

This provides a specific missing prerequisite to test. **The mapping from
IsAlreadyRead to this saved map and the in-game result remain inferred.** The
test changes only that one record to 1 on the natural Chapter 4 arrival. It does
not import older state, replay Chapters 2/3, or change Journal, district, Arena,
Training or Practice flags. See [the Sewers test guide](testing-cai-sewers.md).

Reproduce the primary-data finding with
`python research/cai_sewers_report.py /path/to/GameData`.
The source SHA-256 values are:

- HubDispos/Hub_000.bin: `873b73807b308fc948812f84e8840ac526da9546122b9ab81639c0ac7de881a1`
- Hub.bin: `eb728dfe433aea8346445e527b5e3456c4c82248cbc23cb48b8bb73312226a6a`

GameData, screenshots and private captures are not committed. Optional private
tests use `FEFW_CAI3_RETURN_DIR` and `FEFW_GAMEDATA`.
