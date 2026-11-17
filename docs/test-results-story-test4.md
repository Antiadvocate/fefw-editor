# Story progression Test 4 — accepted results

Reported 2026-11-16: **all UI tests pass; all seven chapters work perfectly**.
Together with Test 3, Chapters 4–12 are accepted for opening and the next main
story beat. Long-term/full-campaign behavior remains untested. Chapters 1–3
and editor-created Obelisk files are the next experimental tests.

## Returned evidence

The supplied ZIP contains 14 saves: an opening Auto and an
Auto-after-advancement for each chapter. All outer and payload checksums pass;
all seven pairs retain the target chapter and have different sequence IDs.

| Chapter | Opening capture | Progression capture | Progression state | User result |
|---|---|---|---|---|
| 5 | 1449-04-07 08:00:00 | 1449-04-07 10:00:00 | Free time | Pass |
| 6 | 1449-05-09 10:00:00 | 1449-05-09 12:00:05 | Free time | Pass |
| 7 | 1449-05-29 12:00:02 | 1449-06-28 21:00:00 | Battle | Pass |
| 8 | 1449-06-29 14:00:00 | 1449-06-30 12:00:03 | Free time | Pass |
| 10 | 1449-09-28 12:00:02 | 1449-10-15 12:00:00 | Battle | Pass |
| 11 | 1449-10-16 12:00:09 | 1449-11-06 18:30:00 | Battle | Pass |
| 12 | 1449-11-07 12:00:02 | 1449-11-27 12:00:00 | Battle | Pass |

- All ten free-time returns retain the baseline party IDs and unique unit numbers.
- Four progression returns are battle saves. Their live unit-record layout is
  not compared using the free-time decoder; story editing correctly refuses them.
- All 14 returns retain every catalogued facility and fast-travel flag from the
  baseline, including the battle returns.
- Each contains the target chapter-start snapshot, with its expected entry
  sequence and the baseline party IDs/numbers. Embedded checksums pass.
- Returned files and the accepted baseline were read only.

UI01–05 are accepted on the user's report: warning/cancel, target evidence,
Apply/Undo/Redo, save/reopen/summary/backups, and route/state/slot guards. No new
screenshots were required for this reported pass. The report does not claim
that external chapter-file creation or Obelisk loading has passed.

The Test 4 builder retains its historical seven targets so changing evidence
labels does not change reproduction. Optional private regressions use
`FEFW_STORY4_RETURN_DIR` and `FEFW_STORY_TEST_SAVE`; no captures are in Git.
