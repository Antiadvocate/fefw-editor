# Cai Test 3 — Chapter 3 to natural Chapter 4

This is a **save-only research test**. Your existing editor remains suitable;
Chapter 3 is not added to its normal chapter selector yet. No UI or Arena
retest is required. Cai Chapter 4 still has a known direct-skip progression
failure; this test seeks an independent natural-transition comparison.

## Supplied files

- `CAI3-03-Chapter-03/Auto`: candidate Chapter 3 start, dated **4 February 1449,
  08:00**, using the date from Cai's chapter-title timeline.
- `00-Control-Chapter-02/Auto`: unchanged successful Chapter 2 advancement
  return from Cai Test 1, provided for reference/rollback.

The candidate uses the established chapter-start mechanics and Cai's inferred
Chapter 3 identifier. It preserves the source's three units, all flag maps,
funds and unrelated objects. It adds no Journal, first-free-time, district,
Training or Practice flags. The chapter's own scripts may change state during
play. Neither Chapter 3 success nor natural Chapter 4 success is assumed.

## Test sequence

1. Back up the complete save folder into a fresh directory. Close the game,
   copy the candidate `Auto` into the game save folder, and use **Continue**.
   Keep your existing chapter files; do not use Restart or the Obelisk to enter
   this test, and do not generate chapter files in the editor during it.
2. Check Chapter 3's opening, location, control/music, objective and ability
   to advance. Keep a copy of the first game-resaved Auto as
   **`03-opening/Auto`**. If Chapter 3 is blocked, stop and return that save
   with the objective and blocking point.
3. If it works, play Chapter 3 normally into Chapter 4 without further edits.
   A **`03-before-transition/Auto`** capture is useful if convenient, but is
   optional; do not replay a battle just to obtain it.
4. At the first save opportunity after Chapter 4's opening, before completing
   its first objective, keep **`04-arrival/Auto`**. Report whether the objective
   appears, whether the Journal agrees, and whether the destination/NPC is
   accessible. This capture is valuable even if progression is still blocked.
5. If possible, trigger the first Chapter 4 objective and keep
   **`04-after-objective/Auto`**. Stop there; no further Chapter 4 completion
   or Arena testing is required.

Also include any `Chapter_Kai_1_3` or `Chapter_Kai_1_4` files the **game writes
during this run**, identifying pre-existing ones if relevant. Their presence or
absence helps check the chapter-file creation hypothesis. Do not create them
manually for this comparison. Zip the named return folders together.

## Technical validation and scope

`research/story_cai_chapter3_probe.py` requires the unchanged passed Chapter 2
advancement (SHA-256
`3f997fc788a1eb61ee418645d33f4f1dedfb41a382805862c7ff9e120715f963`). It refuses
other source files and an existing output directory. Its edit helper checks
Cai Part 1 Chapter 2 and supported loading state before using the shared entry
engine. It validates checksum/serializer roundtrip, header summaries, date,
flag encodings and unit identities. The test does not convert routes or grant
earlier unlocks. The accepted Leda baseline and Main remain unchanged.
