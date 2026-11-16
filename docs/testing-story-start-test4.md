# Story progression — Test 4

Chapters 4 and 9 passed Test 3. This kit uses the same D setup in the editor and
supplies the **seven remaining targets: 5, 6, 7, 8, 10, 11 and 12**. All remain
labelled Inferred until the chapter opening and next main story beat pass.
Chapters 1–3 are deferred. The accepted baseline remains unchanged.

## Prepared game cases

Back up the whole save folder into a fresh directory, close the game, and install
one case's Auto at a time. Use Continue/Auto and let the opening play. Each case
independently starts from the accepted B0-01 baseline; do not chain the cases.
An untouched 00-Control/Auto is included. Existing external chapter files stay
as they are; these tests do not create replacements for them.

For each chapter, report:

1. Opening plays, and the starting location/date/objective make sense.
2. HUD and adventure-journal objectives agree; any deadline has sensible time.
3. The next main story beat/cutscene/battle triggers by waiting or following the
   immediate objective, as appropriate.
4. The current roster, facility and travel registrations remain present. Note
   story restrictions separately from missing registrations.
5. Save/reload if practical. Return an Auto after initial checks and a distinct
   Auto-after-advancement where possible. Restart is optional; distinguish that
   return if tested.

If a chapter blocks or hangs, report where and stop that case. No need to play
whole chapters or change unrelated flags. Note any newly created Chapter_Led_
files, but their creation is not assumed: direct entry and external checkpoints
appear to be separate mechanisms.

## Editor checks

The included editor re-enables Player → Story progression… for supported Leda
Part 1 free-time/checkpoint saves. Apply writes the full entry setup, not just the
chapter label. No editor action is needed for the prepared cases above.

- UI01: Five-point warning; Obelisk note immediately before backup. Cancel leaves
  the save unchanged.
- UI02: Targets 4–12 only; 4/9 labelled Game-tested and the others Inferred.
- UI03: Apply Chapter 4 or 9 on a disposable baseline copy; Undo/Redo works.
- UI04: Save, reopen, then Undo/save if desired. Chapter, date and entry state
  remain consistent, and numbered backups still work.
- UI05: Cai/other routes and battle saves are read-only. Switching slots then
  Undo/Redo must not alter the newly loaded slot. Route mirroring is refused.

Previous UI passes still stand for the earlier implementation; these checks
cover the re-enabled full entry action and its expanded outer-header mirrors.
Automated/GUI validation is supplied, but it does not replace game tests.

## Boundaries

The edit retains all current flags and units, preserves HubSeq, sets the target
entry sequence/resume context/date, and clears old schedule/calendar/restart
state. Entry scripts rebuild the actual scene and internal chapter snapshot.
The full D setup is retained; an identifier-only edit was not tested in isolation.

No previous unlocks or units are granted by the editor. The game may apply
chapter-specific state changes during its opening. External Chapter_Led_ file
creation remains unconfirmed and no such files are written by this feature.

`research/story_remaining_probes.py` reproduces this set using the actual
`story_start.edited` and normal save serializer, with checksums and preservation
checks, from the fingerprinted private baseline into a fresh output directory.
