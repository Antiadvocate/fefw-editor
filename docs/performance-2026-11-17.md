# Editor optimisation — 17 November 2026

Opening and refreshing pages repeatedly scanned the same save. A profile of
one representative panel-data pass found **24 object-tree parses and 24 flag
scans**. Functions data accounted for most of the duplicate work. Chapter
selection also rebuilt already-empty restart blobs: 14 of 16 in the early
Theodora sample.

## Changes

- Each decoded save retains one validated object tree on immutable bytes.
  Reuse requires a full byte equality check, so direct bytearray/slice/struct
  edits invalidate it as well as ordinary editor actions. Failed parsing does
  not replace the last valid snapshot; copies do not inherit caches.
- GameUserData flag scans are reused only when both absolute bounds and bytes
  match. Results return fresh Flag/FlagMap objects so callers cannot alter the
  cached records. There is no global collection of historical saves.
- Page readers and existing edit helpers share that validated tree. Resizing
  edits still run the independent structural readback check.
- The editor's decoded-slot cache also checks content, detecting in-place edits
  even if the payload object keeps the same identity.
- Chapter selection validates every restart blob but rebuilds only nonempty
  blobs. Exact empty records stay untouched.

## Measurements

Python 3.12 in the development environment; median of three sequential runs
per case, with baseline and optimised runs measured separately after tests.
Baseline code is public commit `805d48c0d60f7f3383b042397146535c0da58049`.
Sample 1 is a 140,084-byte early Theodora payload; sample 2 is a 164,564-byte
later Theodora payload. Private save bytes are not included.

These are **data-processing timings, not whole-window timings**. They exclude
Tk rendering, decompression and disk writes. A first read starts with a fresh
SaveFile; a repeat read reuses the same decoded save. Catalogue imports are
warm in both versions. Hardware and save contents affect absolute times.

| Sample | Workload | Before | After | Speedup |
| --- | --- | ---: | ---: | ---: |
| 1 | Panel data, first read | 927.8 ms | 47.4 ms | 19.6× |
| 1 | Panel data, repeat read | 922.2 ms | 5.6 ms | 165.7× |
| 1 | Functions data, repeat read | 594.0 ms | 2.5 ms | 240.9× |
| 1 | Chapter 9 entry | 701.5 ms | 171.0 ms | 4.1× |
| 2 | Panel data, first read | 1008.3 ms | 47.1 ms | 21.4× |
| 2 | Panel data, repeat read | 995.7 ms | 6.6 ms | 152.0× |
| 2 | Functions data, repeat read | 668.3 ms | 3.1 ms | 214.4× |
| 2 | Chapter 9 entry | 818.3 ms | 426.7 ms | 1.9× |

The reader results and Chapter 9 output payload hashes match across both
versions for both samples. The suite separately verifies all twelve Theodora
entries, the accepted repair exports, previous Dietrich behavior and other
editing features. These optimisations do not add story unlocks or broaden
accepted chapter scope.

Reproduce with two independent source checkouts and the same private inputs:

```bash
python research/benchmark_editor.py /private/Auto /private/later/Auto --source /checkout/before --repeat 3 --output /tmp/before.json
python research/benchmark_editor.py /private/Auto /private/later/Auto --source /checkout/after --repeat 3 --output /tmp/after.json
```

## Validation and main-merge checklist

- **256 tests: 205 passed, 51 skipped** for unavailable historical fixtures.
  No unresolved failures. Four new cache tests cover direct mutation, payload
  replacement, stale snapshots, returned-record isolation, copies and restart
  no-op validation. Existing malformed-tree tests inject at the shared reader
  boundary and retain the same refusal assertions.
- Flag-label refresh and check pass; no catalogue change was needed. Known
  English names remain in Name; exact Japanese identifiers remain in Reads As.
- Application header is already clean: Fortune's Weave / Save Editor v1.3.9.
  No temporary test/build wording; upstream version retained.
- Flags is the furthest-right tab. Inferred, Conditional pass and other evidence
  labels remain; optimisation does not promote untested behavior.
- Private save files, screenshots and game binaries are excluded from Git.
- No live Tk window was available in the development runtime. GUI drawing
  performance was not timed; existing UI/history tests run through harnesses.
