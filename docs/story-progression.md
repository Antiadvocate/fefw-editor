# Story progression — Leda Part 1 experiment

**Current status: general chapter editing is paused.** UI01–06 passed, but
all twelve Test 1 progression cases failed. Test 2's four candidates also failed
to establish a working transition. See the
[latest returned evidence](test-results-story-test2-return.md) and
[Test 3 resume comparison](testing-story-resume-test3.md).

Player → Story progression… still shows the caution warning and a read-only
research list for Chapters 4–12. Apply is disabled and direct UI edit calls are
refused. Chapters 1–3 are deferred pending location work. The requested Obelisk
Chamber warning appears directly above the fresh-directory backup note.

The technical description below records the original sequence-only experiment;
it is retained for reproducibility, not a working general transition.

**Only Leda Part 1 saves can enter the research dialog.** The editor reads the save's live route,
part and chapter, not its filename or which units happen to be recruited.
Cai, Dietrich, Theodora, Eshmel, other parts, unknown layouts and disagreeing
route/sequence copies are refused. Direct calls recheck this guard before refusing
the paused edit.
Other routes retain a read-only progression summary. Route mirroring must be off.

## What the experiment does

It selects an inferred chapter-start sequence and updates the two live chapter
fields. Serialization mirrors chapter and sequence into the outer load-screen
summary. Selecting the current chapter can therefore restart its entry rather
than being a no-op; it is a no-op only if that entry sequence is already stored.

The editor does not grant previous facilities, features, tutorials, map points,
side quests, recruited units or other earlier progress. Existing values are
preserved, so jumping backwards also does not remove later unlocks. Currency,
unit identities, inventory, Boons, Deeds, supports and blessings are unchanged.
It does not reset Calendar/GameSchedule, HubSeq, quests, history flags or the
embedded restart snapshot. The game may change state while running its entry
scripts; editor-side preservation is not a promise that the game will preserve
every value after loading.

This is a chapter-entry experiment, **not a complete save reconstruction**.
Old flags, dates, objectives or restart/battle state may conflict with a chosen
chapter. Start from a disposable out-of-battle save. Do not use battle rewind
or an old checkpoint to judge the new live entry: those snapshots are unchanged.
No new checkpoint file or route is created by the UI, and existing slot names
are not renamed. Main and the accepted personal baseline are unchanged.

## Warning and evidence

The warning is titled **CAUTION - UNEXPECTED CONSEQUENCES POSSIBLE** and includes
five points: Leda Part 1 only; no prior unlocks/units; limited
chapter-start/next-sequence testing; the Obelisk Chamber limitation; and an
immediate fresh-directory backup. The Obelisk point appears directly above backup.
An additional sentence makes the current evidence explicit: the earlier
Chapter 9 restoration alone has the reported in-game load/progression result.
The new selector's twelve game cases failed progression; those results supersede the original preparation status. Long-term behavior is
unverified even after a successful start/next-beat test.

The chapter research list now reports Test 1 failures for all entries and
keeps Chapter 9's earlier restoration evidence separate.
Do not promote any new entry simply because its header has the right number
or its container checksums are valid.

## Format and write boundary

| Location | Known layout | Edit |
|---|---|---|
| Live Header | Unique top-level Header, 220 bytes, version marker 15 at block+8 | Chapter at block+14; u64 sequence at block+45 |
| Live GameUserData | Unique top-level block, marker 23 at body+0; route/part/chapter at body+3/+4/+5 | Chapter at body+5 |
| Live sequence child | Direct child at GameUserData body+76, 16 bytes, version 0 | u64 sequence at child+5 (body+81) |
| Outer summary | Marker 15 at raw+36; route/part agree with live data | Chapter at raw+42 and u64 sequence at raw+73 on serialization |

The object tree verifies boundaries and the sequence child's identity/layout.
Header and GameUserData route/part/chapter and sequence must agree; route 4,
part 1 and chapters 1–12 are required. Duplicate or missing live blocks are
refused. An inferred target is never applied by scanning for every occurrence
of a sequence hash. Embedded copies and unrelated bytes are left alone.

The original Chapter 1 and Chapter 2 checkpoints store sequence IDs
`b7b6cc2aad8afbbd` and `b7b9cc2aad8d3152`. Reversing their FNV-1 64-bit suffixes
`1_1` and `2_1` yields the same prefix state, `fde8dadc5dfc1118`. Appending
`9_1` gives `b79bcc2aad7433e5`, the successful earlier restoration's value.
The original implementation exactly reproduces that restoration's decompressed
payload when applied to its original Chapter 2 source. The full symbolic key
has not been recovered; Chapters 3–8 and 10–12 extend this pattern and remain
inferred. Chapter 1/2 IDs are save-observed, but selecting them from the current
baseline failed the Test 1 progression check.

`Timeline_Part1_Led.bin` independently contains 12 title rows, IDs
`MCID_1_LED_title01` through `MCID_1_LED_title12`. Its SHA-256 is
`8fd921c3dd2ca18af17fa54f22fd3b99fadbaffdacfcc28f8ef377435caab5d5`.
Chapter existence does not establish the inferred save sequence mapping.
Reproduce the read-only observation with:

```sh
python research/story_timeline_report.py /path/to/GameData
```

`story.sync_outer_summary` derives the two outer fields from the current valid
Leda P1 payload at serialization. This is important after Undo **and after a
save**: raw container state is not kept outside the existing payload history.
Other routes, unknown layouts and disagreeing outer route/part are left alone.
All other outer fields stay unchanged apart from ordinary lengths/checksums.

## Historical Test 1 assets

[Testing guide](testing-story-progression.md) and
[preparation report](test-results-story-test1.md). That private kit included
12 independently edited Auto files, each based on the same accepted B0-01
Chapter 9 baseline, plus an untouched control. No case is based on another
case's return. Saves, screenshots and GameData stay out of Git.

Reproduce a set from a private source using a fresh output directory:

```sh
python research/story_probes.py /path/to/Auto /path/to/new-probe-directory
```

The script refuses existing outputs or invalid source checksums, verifies
route/layout, checks all writes against the exact field boundary, reopens all
outputs, and records hashes. It never overwrites its input.
