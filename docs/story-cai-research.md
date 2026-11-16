# Cai Part 1 — preparation

Requested after Leda Test 5 on 2026-11-16. This is the next route, not an enabled
editor feature yet. Native Cai save evidence is needed to establish its entry
sequence IDs, resume context, year, restart layout and chapter-file convention.
The current inputs did not contain an identifiable Cai save. The Leda source
must not be converted by changing its route byte: that would retain Leda's
party, progress and unrelated route-specific state.

## Primary data inspected

`Timeline_Part1_Kai.bin` contains exactly 12 chapter-title rows. Chapters 2–12
have explicit month/day/time values; year is inherited (0 in the title row).
Chapter 1 inherits the whole date. These are timeline facts, not tested save edits.

| Chapter | Title-row date/time | Game-edit evidence |
|---|---|---|
| 1 | Inherited; needs a native checkpoint | Unverified |
| 2 | 01-25 11:00 | Unverified |
| 3 | 02-04 08:00 | Unverified |
| 4 | 03-01 12:00 | Unverified |
| 5 | 03-14 12:00 | Unverified |
| 6 | 04-19 10:00 | Unverified |
| 7 | 06-09 12:00 | Unverified |
| 8 | 07-10 12:00 | Unverified |
| 9 | 09-03 12:00 | Unverified |
| 10 | 09-15 12:00 | Unverified |
| 11 | 10-16 08:00 | Unverified |
| 12 | 11-03 12:00 | Unverified |

Source SHA-256: `9d355336bff4a1d21a0a154f2d3fe3daeadf682dcc8c497f89a0f27c6fbeb819`.
Reproduce with:

```sh
python research/story_timeline_report.py /path/to/GameData --route cai
```

The report checks the Cai group, title IDs and all twelve chapter numbers. The
original Leda report remains the default. GameData is neither committed nor
required at runtime. The title rows do not supply the live save-sequence hashes.
The unrecovered type-84 boundary action also appears before Cai Chapters 2–12;
its presence does not establish when external chapter files are created.

## Input and first tests

Supply a native Cai Part 1 save folder containing **Auto** and any
**Chapter_Kai_1_*** files. A non-battle/free-time Auto from Chapter 2 or later is
ideal. Include Route_Kai if present; keep original names. Existing files are
enough—do not manufacture missing checkpoint files in the editor.

1. Validate the route/part and matching live/outer summaries. Check the context,
   year, direct sequence object and all restart records against the Leda layout.
2. Compare natural chapter checkpoint IDs. Confirm a route-specific mapping
   independently before generating other targets; do not reuse Leda's prefix.
3. Prepare independent initial probes at Chapters 2, 4 and 9 to cover an early
   location, a town opening and a later scheduled objective. Preserve the native
   Cai roster, flags, funds, facilities and other progress.
4. Test opening/location/date and the next main story beat, then save/reload.
   Only after those results, expand to the remaining targets and chapter-file
   creation. Label untested mappings Inferred and keep route guards.

Cai Chapter 1 is not assumed to share Leda's failure. Its inherited starting
state requires separate evidence before being offered. No Cai test save is
claimed ready in this preparation stage.
