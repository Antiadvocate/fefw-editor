# Milestone 2 validation record — 2026-11-15

Candidate: `feature/blessings-exp` / **FEFW-Blessings-Test-1**. Use the archive's
`BUILD.txt` or Git commit to identify the exact source. The displayed upstream
version is unchanged. This report accompanies the implementation it describes.

## Automated checks

Local interpreter: Python 3.12.14, Linux. Command, from the repository:

```sh
FEFW_TEST_SAVE='/private/path/to/Auto' python -m unittest discover -s tests -v
```

Result: **33 tests passed**, including both opt-in private-save tests. Without
the private fixture, 31 public tests run and 2 are skipped. The private B0 was
read only; output and restored variants were confined to temporary directories.

Coverage includes full-width identities, shifted/reordered records, all seven
EXP writes, 0/1/120/65535 storage boundaries, invalid requests, malformed and
ambiguous layouts, preservation of unknown selection/trailing bytes, and
ignoring signatures embedded in unrelated content. Exact payload comparisons
permit changes only within the requested two-byte EXP fields.

The display-free page harness checks apply, undo/redo, refreshed save state,
mirroring refusal, invalid input, single-selection enforcement and no-ops.
The private-save regression serializes edits to all seven gods, verifies
checksums after reopening, checks tutorial preservation and restores the
original blessing table. Existing tutorial regression tests also pass.

The initial private run exposed a second object containing embedded older god
records. The locator now requires a non-struct direct child and hashes at
record positions, rather than an arbitrary hash search. A synthetic regression
covers embedded signatures. This correction is included in the passing run.

The GitHub workflow defines Python 3.10/3.12 on Linux and Windows. Its latest
run should be inspected for this branch; prior Tutorials CI success is not
evidence for the new candidate. No packaged executable was produced or tested
for this milestone.

## Native GUI smoke check

Opened the actual Tk interface using Python 3.12 / Tk 9 with a disposable B0
copy. Verified:

* New Blessings tab fits the editor window and lists all seven gods.
* Baseline EXP, selection bytes and Divine Sand match the reference.
* Mars level-2 preset fills 60 while the stored row remains 25 until Apply.
* Apply changes Mars to 60 / preview 2; undo restores 25 / preview 1; redo
  restores 60 / preview 2.
* Ctrl+S and Reload retain Mars 60; the other six rows remain unchanged.
* Photon remains editable but displays Special / unknown, with disabled level
  presets. No level-3-at-zero assertion is made.

Japanese glyphs and some existing non-ASCII UI punctuation were rendered
incorrectly by this test desktop's font/locale environment, including on the
pre-existing tabs. The text source is UTF-8; the tester's earlier Bazzite
screenshots rendered Japanese correctly. Check Reads as on Bazzite in BLESS-01.
This smoke check does not run the game or validate blessing effects.

## Game acceptance: pending

**BLESS-01–11 have not yet been reported by the player for this build.**
The [guide](testing-blessings.md) tests each of the seven gods separately.
Prior restored-save evidence confirms Mars level 1 at EXP 25 and Kalla level 3
at EXP 100; it does not validate Credna, Jurah, Smyrnos, Aurora or Photon,
lowering a level, or persistence of every new edit.

Reference environment: Bazzite 45 NVIDIA, KDE Plasma 6.8.2, Wayland,
Ryzen 7 5800X3D / 32 GiB / RTX 5080, `fefw-recomp-0.1.5`, Leda Part I
Chapter 9. Exact game data version and tester's Python environment remain
unreported. Other routes, other save versions, Photon gameplay semantics and
automatic deed/ability recalculation are not accepted by this report.
