# Story entry — Test 2 comparison

These four independent Auto files investigate why Test 1 did not start a fresh
chapter. They are **diagnostic candidates, not proven fixes or new baselines**.
The editor's general chapter writer is paused; no editor changes are needed
to use these prepared saves. Chapters 1–3 are deferred. Chapters 5–8 and 10–12
will follow only after the entry mechanism works in this comparison.

Back up the whole working save folder into a fresh directory. Close the game
between cases and install just that case's Auto in the usual location. Keep
other save files as usual, but load **Continue / Auto**, not an old Chapter file.
Each case starts from the unchanged accepted B0-01 baseline, not a returned
failed file or the previous case's game save.

| Order / folder | Target | Difference from the preceding Chapter 9 candidate |
|---|---|---|
| ST2-09A-Entry-mode | Chapter 9 | Original selector edit plus the two Header state bytes observed in genuine chapter-start checkpoints; outer summary mirrors them. Old date and restart cache retained. |
| ST2-09B-Empty-restart | Chapter 9 | A plus all eight internal restart slots emptied using the exact structure of the natural checkpoint. Old date/schedule retained. |
| ST2-09C-Entry-date | Chapter 9 | B plus clock set to July 10, 18:00, matching the chapter title row; remaining schedule state and Calendar cache cleared to checkpoint form. |
| ST2-04C-Entry-date | Chapter 4 | Same C profile, but Chapter 4 and March 1, 08:00, matching its title row. Tests whether entry scripts establish the correct location. |

The year remains 1449 from the accepted source. No objective strings, quest
flags, facilities, tutorials, world-map records or units are transplanted.
Profile B/C intentionally clear cached restart/history data; they do not
fabricate a replacement checkpoint or change existing Chapter_* files. The
question is whether loading properly initializes new restart data. The game
may change flags or units while executing the selected chapter's own scripts.

## What to check

Test **09A → 09B → 09C → 04C** separately. A short failure is useful; no need to
play through a long blocked session.

1. Does Continue play the chapter opening or resume the same free-time scene?
2. What location and date/time appear after the opening settles?
3. Do the HUD and adventure-journal main objective agree? Record remaining turns.
4. Can the next main story beat happen? Wait during free time or follow the
   immediate required conversation/travel prompt.
5. If Restart chapter is available, note which chapter it loads. In 09A the old
   cache deliberately remains; in B/C a rebuilt cache is the desired outcome.
   If testing restart would disrupt the next-beat check, save the first result
   and test restart on another copy.
6. Return a game-resaved Auto for each case, saved after the initial load/checks.
   If you also test restart, return that extra save with `-after-restart` in its
   name so it is distinguishable from the initial-load result.

Use `00-Control/Auto` only as an unchanged loading control. Screenshots are most
useful for conflicting objectives, wrong locations, dates or restart results.
Do not enable extra flags during these tests. Keep the real baseline separate.

## Interpretation

- A works: checkpoint-entry state may be the missing trigger; verify restart
  separately before choosing the smallest implementation.
- B improves on A: the stale restart cache also needs treatment.
- C improves on B: an explicit schedule/calendar initialization is implicated.
- 09C works but 04C fails: chapter-specific location/state handling is still
  needed; do not assume all Chapters 4–12 are ready.
- All fail: investigate hub/spawn state and timeline cursor initialization before
  broadening the writer. These results would not establish that the feature is
  impossible, but a general selector would remain unsupported.

## Reproduction and boundaries

`research/story_entry_probe.py` builds only these four diagnostics from the
fingerprinted private baseline, refuses existing output directories, and verifies
all outputs. Runtime field mappings and broader applicability remain unverified.

- A changes live chapter/sequence and the Header state pair, mirrored outside.
- B additionally clears the sixteen known Header/Data blobs in eight restart
  slots. It validates all slots, stored lengths, encodings and embedded checksums
  before clearing anything; object pointers are relocated by the existing engine.
- C additionally updates the Header and GameSchedule clock, clears the rest of
  GameSchedule, and clears the Calendar body while retaining its version byte.
- Every unrelated top-level object must remain byte-identical after pointer
  normalization. GameUserData may differ only in chapter and sequence. The empty
  restart block matches the natural Chapter 2 checkpoint after normalization.

The dates come from `Timeline_Part1_Led.bin` title rows: Chapter 4 at `0x3c50`
and Chapter 9 at `0xb0c0`. Their existence/date fields are data observations;
they do not prove that writing those values is sufficient for progression.
