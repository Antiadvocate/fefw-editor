# Story progression Test 1 — preparation

Prepared 2026-11-16 on `feature/leda-story-progression`, based on facility
acceptance commit `b5845b4`. **Superseded by returned results: UI passed; all twelve progression cases failed.**
See [the return report](test-results-story-test1-return.md). The accepted main
branch and personal baseline are unchanged.

## Evidence before this experiment

The original Chapter 1/2 checkpoint IDs share the inferred suffix pattern.
Applying the current Chapter 9 edit to the original Chapter 2 checkpoint
reproduces the earlier successful restoration's decompressed payload exactly.
The player previously loaded that restoration, reached the Chapter 9 fight
and continued. It is not a pass for the new selector or all current cases.

The private game-data report finds exactly 12 Leda Part 1 title rows. Their
existence supports the chapter range; it does not prove the hash mapping for
every chapter. See [format and boundaries](story-progression.md).

## Validation

Synthetic tests cover all 12 targets, shifted GameUserData, allowed-byte
preservation, no-ops, invalid chapter inputs, other routes/parts, conflicting
route/chapter/sequence copies, duplicate/missing blocks and unknown layouts.
The mutation boundary refuses Cai even when called without the UI. Warning
and picker cancellation leave history/payload unchanged; route is rechecked
after dialogs. Mirroring is refused. Serialize/reopen tests cover outer/live
agreement, Undo after a save, Redo and numbered backups; non-Leda summaries
remain unchanged. Undo/Redo is now bound to its originating loaded save object;
regression checks cover switching to Cai, switching back, reloading the same
path and starting a new edit on another slot. This closes the pre-existing
shared-history path that could otherwise bypass the new route guard.

Private checks generate all 12 cases from the accepted source, verify
checksums, reopen and compare every payload byte against the exact write
boundary. Source and control remain byte-identical. Existing output directories
are refused. Natural checkpoint IDs and the prior Chapter 9 edit are checked
independently.

The running interface was exercised at 1000×640 in dark/light themes: warning
with all requested bullets, cancellation, 12 chapter choices, application,
Undo/Redo, save/reopen, summary consistency and numbered backups. A synthetic
Cai route was read-only and refused direct application; this does not replace
the requested real Cai-save test. Flags remains last.

The full local run passed **154 tests**, including **27 private-fixture tests**.
The final cross-slot Undo fix added two regressions; the resulting public
suite passed **129 tests** (27 private tests skipped in that repeat). The final
running-GUI check also refused cross-slot Undo/Redo into the synthetic Cai save.
Known English flag labels pass the freshness check; this feature introduces no
new flag names or flag writes. The product/version header stays clean.

## Pending player results

Historical preparation status: STORY-UI01–06 and STORY-01–12 were pending.
They have now been returned; see the report linked above. For each chapter, capture actual
entry and the next main story beat, followed by a game-resaved file where
possible. Long-term testing is not claimed. No source save, screenshot, video
or GameData file is committed to the public branch.
