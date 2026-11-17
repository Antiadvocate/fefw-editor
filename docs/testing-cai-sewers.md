# Cai Chapter 4 — Sewers dialogue prerequisite test

**One candidate, using your latest natural Chapter 4 arrival. No editor update
or replay of Chapters 2/3 is needed.** Arena testing remains deferred.

The screenshot identifies the Sewers entrance beside the Item Shopkeeper.
Its game-data condition requires a specific Chapter 2 dialogue to be read.
That key is missing from your current save. This is a focused hypothesis, not
yet an accepted fix: the candidate adds the one dialogue-history record as 1.

## Files

- `C4-Sewers-Dialogue-Read/Auto`: one dialogue-history record added.
- `00-Control-Natural-Chapter-04/Auto`: your unchanged Chapter 4 arrival.

Both retain March 1, 15:00 and the current first-objective sequence. The
candidate preserves all four units, including the unit gained during Chapter 3,
and the rest of your progression. No Journal/function switches are changed.
The exact identifier and technical limits are in `EVIDENCE.md`.

## Test

1. Back up the complete save folder into a fresh directory. Close the game,
   replace Auto with the candidate, and use **Continue**. Do not use Restart
   or the Obelisk; those could load an unedited checkpoint.
2. Go to the **Sewers doorway beside the Item Shopkeeper**, as shown in your
   screenshot. Check whether its entrance prompt and objective marker appear
   and whether you can enter. Keep a game-resaved Auto as **`01-entry/Auto`**.
   If it is still inaccessible, return the nearest Auto and describe whether
   the prompt is absent or the game refuses entry.
3. If you can enter, follow **Find the dungeon** and try the first objective.
   Keep **`02-after-objective/Auto`** once the next story beat occurs. If blocked
   farther inside, return that save and identify the doorway/NPC involved.
   No need to finish Chapter 4 or test the Arena.

Keep any checkpoint files the game writes, but do not create or overwrite them
with the editor for this test. Stop after the objective result so the comparison
stays focused. If a manual control comparison is useful, use the supplied
untouched Auto independently; do not chain a control from the edited result.

The source fingerprint is
`968a783fbce421e0b0abf3e92cb493de5cb4aa2310437bd62c843d4f27026ef9`.
The generator refuses any other input and an existing output directory. It
checks that removing the inserted record restores every normalized object,
then verifies checksum/serialization roundtrip. In-game success is pending.
