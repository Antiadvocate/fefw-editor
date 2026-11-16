# Story Test 2 — returned results, 2026-11-16

Historical failure report. The subsequent [Test 3](test-results-story-test3.md)
passed Chapters 4/9; [current scope](story-progression.md) supersedes the paused
editor status described below.

**None of the four candidates established working chapter progression.** The
general editor action remains paused. UI01–06 from Test 1 remain accepted;
they are UI/guard results, not chapter-transition acceptance.

| Case | Player observation |
|---|---|
| 09A | Continue says Chapter 9; HUD objectives blank; journal says third qualifier; July 12. Restart restores apparently correct objectives, but journal becomes unavailable and facilities relock. |
| 09B | Same initial result as 09A; Restart disabled. |
| 09C | Same initial result, July 10; Restart disabled. |
| 04C | Continue says Chapter 4, March 1; HUD still says first main match with zero turns to September 1; journal says Meet with Kalla; Restart disabled. |

The returned ZIP includes four initial-load Auto files and a separate 09A
Auto-after-restart. The external Chapter_Led_1_9 was supplied separately.
All six containers pass checksums and object-tree parsing. The current accepted
baseline is not replaced by any of these files.

## What the restart evidence does and does not establish

09A preserves the original embedded Chapter 9 Data snapshot byte-for-byte.
B/C returns contain restart Header metadata but no populated Data snapshot;
loading did not rebuild one. Restart being disabled in those cases demonstrates
that merely retaining the external chapter file is insufficient for that
action to be available in this setup.

The supplied external checkpoint and the old embedded snapshot have identical
normalized UnitPool, HubData, GmapSpotMgr, GmapTroopMgr, Transporter and
GameSchedule objects. Both represent the older checkpoint context, not the
current reconstructed baseline. They differ in other save-wrapper/user-data
objects. Consequently the post-restart regression cannot distinguish an
external-file read from embedded restoration, or a combination of the two.
The earlier statement that the embedded snapshot alone explained the restart
source was too strong. Its availability role is supported; exclusive source
selection is not established.

09A after restart returns to the free-time sequence `d1a25c2f18128a5b`, with a
July 12 clock and older world/roster state. It has a newly populated restart
snapshot. Correct-looking objectives after reverting progress are not an
accepted skip that preserves the user's current save.

## Newly isolated resume-state difference

The live GameUserData v23 body contains a separate u64 at offset 58, before its
chapter-sequence child. It is distinct from the chapter-entry sequence at
body+81 that Tests 1/2 changed.

| Observation | u64 at GameUserData body+58 | HubSeq root member |
|---|---|---|
| Current baseline and all four failed Test 2 returns | `d8588d186b3f9502` | Present, empty 8-byte object |
| Natural Leda Chapter 1/2 checkpoints; earlier successful Chapter 9 candidate; supplied Chapter 9 checkpoint | `a2f3e9a7ff461708` | Absent |
| Natural prologue Chapter 2/3 checkpoints | `a2f3e9a7ff461708` | Absent |
| 09A after restart and return to free time | `d8588d186b3f9502` | Present |

The exact original name/type of the u64 is unrecovered. “Resume identifier” is
a research label: its correspondence with checkpoint versus hub resume context
is observed, while its causal role still needs a game test. Another route-start
capture has the free-time value without HubSeq, so absence alone is not a
universal chapter-start indicator. The optional removal test is restricted to
the known empty HubSeq layout.

The active Chapter 9 support/conversation record also survives 04C, including
`MID_SUP_1LED_c09_LG14_013_m01`. It is preserved in Test 3 because its role in
blocking entry has not been isolated; importing every older record would risk
the same progress regression as Restart.

## Next test and limits

[Test 3](testing-story-resume-test3.md) builds on each Test 2 C profile. D changes
only the separate resume identifier; E additionally removes the empty HubSeq
root member. Both Chapters 9 and 4 are supplied. No checkpoint's roster,
facility flags, currencies or other progression records are imported.

Date changes and empty restart data were insufficient on their own. Do not
enable a general chapter writer or expand to Chapters 5–8/10–12 until entry and
the next story beat work while preserving current progress. Chapters 1–3 remain
deferred. The Obelisk warning remains immediately above the backup instruction.

Private returns and checkpoint files stay out of Git. Optional tests use
`FEFW_STORY2_RETURN_DIR` and `FEFW_STORY2_CHAPTER` to reproduce the observations.

## Test 3 preparation validation

- 134 public tests passed (166 discovered, 32 private tests skipped).
- All five focused resume-probe tests passed with the accepted baseline and
  current private returns, covering bounded edits, unknown-layout refusal,
  container round trips, all flag maps and the checkpoint/snapshot comparison.
- All four generated candidates reopened with valid checksums. Unit records and
  unrelated root objects matched after pointer normalization; source files were
  unchanged. D differs from C by exactly the separate eight-byte identifier;
  E additionally removes only the validated empty HubSeq object/table entry.
- Running-editor warning, cancellation, disabled editing, Chapters 4–12 list,
  dark/light layout at 1000×640 and Flags-last checks passed.
- Game results for Test 3 remain pending. No general writer has been re-enabled.
