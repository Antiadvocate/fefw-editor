# Hours Played Test 1 — preparation and validation

Date: 2026-11-15. **Game result pending.**

The user requested Hours Played first, then consideration of other game-wide
counter Deeds using the result as a working assumption. This branch adds one
experimental editable counter to the accepted 32; the other 14 remain read-only.
It does not modify the already merged main branch.

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

The UI marks Hours **Experimental**, including a note that the game may
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

## Acceptance boundary

Use [HOURS-01–03](testing-deed-hours.md). Game display, completion, recalculation,
reward accounting and game reload are unverified until returned evidence or
player results establish them. A short reload test cannot prove behavior at
every future hour boundary. Any later generalization to other counter groups
will be explicit inference, not retroactive acceptance of those fields.
