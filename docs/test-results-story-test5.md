# Leda Test 5 — acceptance and Chapter 1 exclusion

Reported 2026-11-16:

| Test | Result | Accepted scope |
|---|---|---|
| Chapter 1 | Fail | Opening plays; no music after control resumes; reaching the first objective does not advance |
| Chapter 2 | Pass | Opening and next main story beat |
| Chapter 3 | Pass | Opening and next main story beat/battle |
| UI5-01–05 | Pass | Warning/labels, Save-only staging, Undo/Redo/Reload, creation, overwrite confirmation/backups and unchecked behavior |
| OB5-01, Chapter 8 | Pass, user reported | Editor-created file appears/loads and works through the Obelisk |
| OB5-01, Chapter 9 | Pass, with returned files | Editor-created file appears/loads and works through the Obelisk; progression return supplied |

Together with Tests 3/4, **Leda Part 1 Chapters 2–12** are accepted for opening
and the next main story beat. This is not full-campaign or long-term testing.
The user considers this Leda test round complete and requests Cai next.

## Chapter 1 handling

The user accepted excluding Chapter 1. It is removed from the picker and the
public chapter-entry action refuses it before creating history or a file request.
The first warning bullet explains that Chapter 1 cannot be selected because its
first objective does not advance. No further Chapter 1 game test is requested.
A supported save already in Chapter 1 can still select an offered later chapter.

Its returned save has valid checksums, Chapter 1 and sequence
`d1bd1c2f1828e550`, free-time context `12 05`, and December 1, 1444 at 18:30.
The expected roster, catalogued facility/travel flags and chapter-start snapshot
are present. This does not identify the missing music/progression prerequisite.
The old candidate remains reproducible through the explicitly historical
`research/story_early_probes.py`; it is not an enabled editor target.

## Returned evidence

Eight files were supplied: five early-chapter returns, the editor-created
Chapter 9 file, and two Obelisk Chapter 9 game returns. All eight container and
payload checksums pass; live Header and GameUserData chapter/sequence agree.

| Capture | Saved clock | Sequence | Context |
|---|---|---|---|
| Chapter 2 opening | 1449-01-15 12:00 | `d1c71c2f183139d7` | `12 05` |
| Chapter 2 advancement | 1449-01-16 08:00 | `b4098cf8d6f4e8d5` | `12 06`, unsupported event context |
| Chapter 3 opening | 1449-02-01 10:00 | `d1c45c2f182f70fe` | `12 05` |
| Chapter 3 advancement | 1449-02-01 13:00 | `a29502ce5e7b409b` | `12 02`, battle |
| Editor-created Chapter 9 | 1449-07-10 18:00 | `b79bcc2aad7433e5` | `10 0b`, chapter entry |
| Obelisk Chapter 9 opening | 1449-07-12 12:00:28 | `d1a25c2f18128a5b` | `12 05` |
| Obelisk Chapter 9 advancement | 1449-09-01 12:30 | `a27302ce5e5e5a75` | `12 02`, battle |

The editor-created Chapter 9 file has the expected entry resume identifier,
clock, mirrored summary and cleared internal restart slots. Reapplying the
Chapter 9 entry is byte-identical at payload level. Its Obelisk returns have the
same opening/next-battle sequences observed in the earlier successful tests,
and rebuild the Chapter 9 start snapshot with the expected current roster.
The filename suffix `(1)` belongs to the uploaded copy; it is not part of the
game's checkpoint naming convention.

The seven captures supported by the full object-tree decoder retain the
catalogued facility and travel flags. The five checkpoint/free-time captures
retain the expected nine unit numbers. Battle live unit records are not decoded
using the free-time gear layout. Supported game returns have the expected
chapter-start snapshot; this does not claim all intermediate snapshots have
identical roster layouts.

**Inspection limit:** Chapter 2's advancement return has valid checksums but
context `12 06` triggers recursion in the generic tree decoder. Its full tree,
facility flags and restart records were not validated. Story editing now rejects
unsupported contexts before traversing variable objects, and a story-tree
recursion failure is converted to a clear save-layout error. This is a decoder
coverage limit, not evidence that the player's working save is corrupt.

No Chapter 8 Obelisk file was supplied; that pass is recorded from the user's
report. Other chapters' Obelisk discovery/loading remain untested. Existing
natural checkpoint creation at chapter boundaries remains a separate hypothesis.

Source uploads and the accepted B0-01 baseline remain unchanged. Private captures
are not committed to Git. Optional regressions use `FEFW_STORY5_RETURN_DIR` and
`FEFW_OBELISK5_DIR`.
