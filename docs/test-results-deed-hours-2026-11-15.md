# Hours Played Test 1 — accepted game result and validation

Date: 2026-11-15. **HOURS-01–03 passed by player report.** Both returned game
saves corroborate the edited total, completion, claim and exact reward.

The user requested Hours Played first, then consideration of other game-wide
counter Deeds using the result as a working assumption. This branch adds one
experimental editable counter to the accepted 32; the other 14 remain read-only.
It does not modify the already merged main branch.

## Player acceptance and returned saves

| Field | Prepared Auto | Hours-before-claim | Hours-after-claim |
|---|---:|---:|---:|
| Hours Played counter eb92a0f6 | 20 | 20 | 20 |
| 10-hour claim e0de8be2 | 4 | 4 | 4 |
| 20-hour claim 71725a0a | Absent | 2 — complete, unclaimed | 4 — claimed |
| Karma Shards | 410 | 410 | 430 |
| Gold / Renown | 1523 / 6640 | 1523 / 6640 | 1523 / 6640 |

The game creates the completion state itself after the counter-only edit,
then records the claim and grants exactly 20 Karma. The player reports the
brief-play, save/quit/reload and no-repeat-claim checks all passed. No new
screenshots were supplied. The stored totals/states and currency are directly
verified from the returns; the act of restarting and the menu's refusal to
offer a second claim remain player-reported.

Both returned containers have valid checksums and object trees. All parsed
flag maps match the accepted baseline except Hours 17 → 20 and the new
20-hour state. This preserves other Deeds/claims, Boon flags, shop restrictions,
the Kalla gate, tutorials, travel and audiences. Blessing EXP, selections and
Divine Sand match. Parsed unit values match after excluding structural offsets;
the added claim record moves subsequent objects by eight bytes. All nine
repaired live unit numbers remain distinct and unchanged. The files were
read without modification. Game-resaved payloads are not byte-identical to
the editor-generated probe.

| Capture | Bytes | SHA-256 |
|---|---:|---|
| Hours-before-claim | 48,555 | `f9e46675094eae692e9d14dedf9e0ed77bf40638e6ae27cc90a4d9824eac51ef` |
| Hours-after-claim | 48,555 | `6e5d791a0fd8fcdb98fe8dd5912fb9d14263a6ce7832c918df91cc8f4f634bf2` |

These are acceptance captures. The accepted baseline remains the supplied
Auto from B0-01-Unit-Selection-Test-1.zip; neither return replaces it.

## Exact prepared probe

Source is the accepted Auto from B0-01-Unit-Selection-Test-1.zip, SHA-256
8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663.

| Record | Before | Prepared |
|---|---:|---:|
| Hours counter eb92a0f6 (実績_プレイ時間) | 17 | 20 |
| 10-hour claim e0de8be2 | 4 | 4 |
| 20-hour claim 71725a0a | Absent | Absent |
| Karma | 410 | 410 |
| Gold / Renown | 1523 / 6640 | 1523 / 6640 |

The 20-hour milestone has a catalogue reward of 20 Karma. No claimed target is
left unmet by the increase. The prepared save does not write a completion flag.

The accepted counter uses wide encoding. Only its low value byte at payload
offset 4236 changes, from 17 to 20; the encoding and payload size remain intact.
That offset describes this exact baseline, not a portable patch address.
The generator locates the counter structurally and checks the source digest.

The output Auto is 39,541 bytes, SHA-256
3eabad4f66701912747a2005eeee90a5b1621787ed9000d6f0b144e1db3c5ea3.
Source/output checksums and object trees pass. Embedded checksum refresh adds
no payload changes for this probe. Every other payload byte, including the
header, units, other maps, claims and any separate elapsed-time fields, is
unchanged. Container compression/checksums account for the file-size difference.
The source is byte-identical after generation.

## Scope and checks

The supplied Test 1 UI marks Hours **Experimental**, including a note that the game may
recalculate it. Existing bounds, unknown-state refusal, claims-at-risk warning,
mirroring guard and Undo/Redo remain applicable. Only Hours is newly enabled.

New regressions cover the 33/14 editing boundary, counter identity, experimental
labels, preservation of other records and outside-map bytes, compact/wide values,
range/unknown-state refusal, undo/redo and cancelling a claimed-target decrease.
An opt-in private check reproduces the exact probe and prevents overwriting its
input or an existing output directory.

All **121 local tests passed**: 101 public tests and 20 opt-in private checks
using the accepted baseline and existing captures. Real Tk checks passed the
experimental label, target-fill/Apply, exact prepared-probe payload, Undo/Redo,
save/reopen, cancellation of a claimed-target decrease, mirroring refusal and
numbered backups. Flags remains the rightmost tab. The English controls and
experimental note fit the dark 1240×800 and light 1000×640 layouts.

Reproduce with FEFW_WEAPONS_TEST_SAVE pointing to the accepted B0-01 Auto and
the existing private capture variables, then run:
python -m unittest discover -s tests -v

Generate the probe with:
python research/deed_hours_probe.py --source /path/to/accepted/Auto --output /new/probe/directory

Private saves, screenshots and game binaries are not in GitHub or the editor
source archive. The separately supplied probe archive is private test evidence.

The opt-in returned-save regression is enabled by FEFW_HOURS_CAPTURE_DIR,
alongside FEFW_WEAPONS_TEST_SAVE. It checks the exact captures, game-created
completion, 2 → 4 claim transition, 20-Karma reward, preserved progress and
unchanged input files. Private capture files remain excluded from public CI.
All **19 focused Deeds tests passed** with the returned-save check enabled.
This acceptance update changes documentation and adds that private regression;
it does not alter editor behavior or require another download.

## Acceptance boundary

[HOURS-01–03](testing-deed-hours.md) establishes the 17 → 20 counter-only edit,
game completion, reward accounting and short-session persistence on the tested
Leda Chapter 9 setup. No immediate recalculation overwrote the edited total.
A later natural hour boundary, higher Hours tiers and every other counter
remain untested. The next game-wide counter group may use this result as a
labelled working assumption; that is inference, not individual acceptance.
