# Story Test 1 — returned game results, 2026-11-16

**UI01–06 passed. All twelve chapter progression cases failed.** The selector
fields persisted and the game recognized chapters, but the surrounding resume
state was not reinitialized. These results supersede the preparation report's
pending status. No chapter is accepted as a working general editor transition.

| Cases | Player observation |
|---|---|
| 1–3 | Chapter recognized, but wrong location prevents progress |
| 4–5 | Same location problem; Restart chapter is available but loads Chapter 9 |
| 6–8 | Deadline appears already passed and progression cannot advance |
| 9 | Zero turns left; HUD says first main match while journal says third qualifier |
| 10 | Similar zero-turn/HUD problem; new support notification; journal says first main match |
| 11 | Similar; journal says Semifinal |
| 12 | Similar; journal says Escape the underworld |

The supplied ZIP has twelve Auto files saved just after loading. All pass
container checksums and object-tree parsing. Each retains the requested Leda
Part 1 chapter and inferred entry sequence. Eleven retain Header state bytes
`12 05`; Chapter 1 stores `12 04` after loading. All retain the July 12 clock
(year 1449) and a second GameSchedule timestamp of September 1 at noon. This
second timestamp matches the old Chapter 9 scheduling context; its precise
field semantics have not been independently decoded. The zero-turn symptom
therefore cannot be explained simply as current time exceeding that timestamp.

All twelve also retain the same embedded Chapter 9 restart payload, including
sequence `b79bcc2aad7433e5`. This directly explains why changing only the live
chapter cannot make Restart chapter load a different checkpoint.

## Why the original Chapter 9 experiment differed

The earlier successful experiment began with a genuine Chapter 2 checkpoint.
Its Header state bytes were `10 0b`, GameSchedule held a January 2 clock with
the rest of its state zero, Calendar was empty, and all eight restart slots
were empty. Test 1 instead edited the current free-time baseline, preserving
`12 05`, its old schedule, hub/location state and populated restart cache.

Thus reproducing the original experiment's chapter/sequence writes did not
reproduce its starting context. The implementation's write-boundary checks
were correct but insufficient evidence for in-game progression. The original
checkpoint restoration's pass must not be generalized to arbitrary Auto files.
The exact enum meanings of the Header bytes are not recovered; “checkpoint
entry” and “free-time resume” describe observed source contexts, not an official
field-name mapping.

## Next recommendation and scope

Continue investigation for **Chapters 4–12**, starting with a bounded comparison
at Chapters 4 and 9. Chapters 1–3 are deferred because they start elsewhere and
have unresolved location requirements. The corrected loading context may let
the game's own scripts initialize location, date and objectives; that remains
a hypothesis until tested. The Chapter 4 timeline contains a Dagsion transfer
and initial-location setup, so it is a useful location-sensitive comparison.

The known-failing UI write is paused. The chapter research list shows 4–12,
with Apply disabled; direct calls also refuse without creating history. The
five-point warning now includes the requested Obelisk Chamber sentence directly
above the backup note. This warning records the user's limitation about chapter
save files; this experiment neither creates nor deletes those files.

See [Test 2 comparison guide](testing-story-entry-test2.md). Private captures
remain outside Git. `FEFW_STORY_RETURN_DIR` enables the read-only regression
check of all twelve selectors, clocks and embedded Chapter 9 snapshots.

## Test 2 preparation validation

- 132 public tests passed (161 discovered, 29 private tests skipped).
- A focused run of 18 story tests passed with private baseline, original
  checkpoints, prior successful restoration and all twelve returned saves.
- All four diagnostics reserialized and reopened with valid checksums. Their
  unrelated top-level objects matched after pointer normalization. The emptied
  restart object also matched the natural Chapter 2 checkpoint.
- Running-editor checks passed for the five-point warning, cancellation,
  Chapters 4–12 research list, disabled Apply, direct-call refusal, dark/light
  layout at 1000×640, Flags last, and unchanged source save.
- These checks validate file structure and UI behavior, not in-game progression.
  Test 2 game results remain pending.
