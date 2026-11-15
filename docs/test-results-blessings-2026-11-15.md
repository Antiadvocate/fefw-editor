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

GitHub Actions [run 43705609197](https://github.com/Destorino5/fefw-editor/actions/runs/43705609197)
passed for implementation commit `ec3ce61dc49e9552675dbe1295d12131b49db431`:

| Platform | Python | Result |
|---|---|---|
| Ubuntu | 3.10 | PASS |
| Ubuntu | 3.12 | PASS |
| Windows | 3.10 | PASS |
| Windows | 3.12 | PASS |

Each public job runs the suite without the private fixture (31 tests passed,
2 skipped). The Test 1 archive's CI-result update changes documentation only;
the archive identifies both its source commit and the tested implementation commit.
No packaged executable was produced or tested for this milestone.

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

## Game acceptance: PASS on the reported setup

On 2026-11-15 the player reported **BLESS-01–08: Pass**, **BLESS-09: Nothing
noticeable in-game, EXP persisted on editor reload. Pass**, and
**BLESS-10&11: Pass**, following the [test guide](testing-blessings.md).
Evidence includes the baseline editor screenshot, six in-game screenshots,
and private case files `Auto (BLESS-03)` through `Auto (BLESS-09)`.

Tested source archive: **FEFW-Blessings-Test-1**, source commit
`74b10f04458bdb0fb2a16f339e9e86fb96ce8cef`; implementation commit
`ec3ce61dc49e9552675dbe1295d12131b49db431`. The archive contains the latter's
code plus the CI-report documentation update. Its upstream window version
still reads v1.3.7.

| Case | Test | Player result | Independently checked evidence |
|---|---|---|---|
| BLESS-01 | Baseline rows, labels and Divine Sand | PASS | Editor screenshot matches all seven B0 EXP values, selection bytes and Sand 100; Japanese keys render correctly |
| BLESS-02 | Preset, apply, undo/redo and export | PASS | Player report; also covered by the earlier native GUI smoke check |
| BLESS-03 | Mars EXP 61 | PASS | Screenshot shows level 2; supplied file retains EXP 61 |
| BLESS-04 | Credna EXP 41 | PASS | Screenshot shows level 2 and its first two effect descriptions; supplied file retains EXP 41 |
| BLESS-05 | Kalla EXP 51 | PASS | Screenshot shows level 2, reduced from B0's level 3; supplied file retains EXP 51 |
| BLESS-06 | Jurah EXP 61 | PASS | Screenshot shows the tested level-2 card; supplied file retains EXP 61 |
| BLESS-07 | Smyrnos EXP 61 | PASS | Screenshot shows the tested level-2 card; supplied file retains EXP 61 |
| BLESS-08 | Aurora EXP 51 | PASS | Screenshot shows the tested level-2 card; supplied file retains EXP 51 |
| BLESS-09 | Special record, EXP 1 | PASS for persistence | Player observed no noticeable in-game change; supplied file retains EXP 1 |
| BLESS-10 | Mirroring guard, invalid values and no-op | PASS | Player report |
| BLESS-11 | Regression checks | PASS | Player report; tutorial state independently matches B0 in all seven supplied case files |

All seven supplied files were read without modification. Each passes the
container checksum verification, contains exactly the seven recognized god
records, and retains the requested EXP for that case. In every file, **all
other gods' EXP, every stored selection byte, Divine Sand (100), and the full
tutorial hash/state mapping match B0**. These are checks of the supplied save
contents, not a claim that all save bytes are identical after playing or saving.
The Credna screenshot shows a temporary 3/4 selection, while its supplied file
has B0's selection bytes; the screenshot is level/UI evidence, not evidence of
a persistent selection change caused by the editor.

### Special record: Fortuna, previously labelled Photon

The original test build displayed **Photon** for `MIR_フォトナ`, full hash
`d2fdff3fa4a597ed`. The in-game screenshots label its effect **Fortuna's
Blessing Effect**, with no ordinary numbered blessing level. Current source
corrects the English display name to **Fortuna**. The key, hash, offsets,
EXP-writing behavior and disabled level presets are unchanged; this is not an
eighth god. BLESS-09 and earlier references to Photon refer to this same record.

EXP 1 persistence is confirmed for the reported test and supplied case file.
No noticeable in-game change was reported. In a follow-up on the same date,
the player set maximum stored EXP (65535, the editor's upper limit) and
reported nothing easily noticeable on the Blessings screen. This additional
observation is a player report; no corresponding save was supplied to
independently verify the maximum value or its persistence.

Neither observation proves the field is unused, that every value is harmless,
or that Fortuna has normal EXP-based levels. Keep the **Special / unknown**
preview and avoid claiming level 3 from the three zero-valued threshold fields.
The current UI text describes the reported screen behavior without promising
a gameplay effect.

### Acceptance scope and remaining limits

Reference environment: Bazzite 45 NVIDIA, KDE Plasma 6.8.2, Frameworks 6.31.0,
Qt 6.11.2, kernel `7.2.15-ogc1.1.fc45.x86_64`, Wayland, Ryzen 7 5800X3D /
32 GiB / RTX 5080, `fefw-recomp-0.1.5`, Leda Part I Chapter 9. Exact underlying
game data version and tester's Python environment remain unreported.

The milestone's defined acceptance cases are complete for this setup. Evidence
supports the six tested level-2 values, the Kalla decrease, all seven EXP
persistence checks, and the reported editor guards/regression checks. It does
not constitute a complete threshold-boundary sweep, a separate combat-effect
test of each blessing, broad tests of extreme EXP, other routes or save versions,
or a controlled investigation of automatic deed/ability recalculation. The only
maximum-EXP game observation is the Fortuna screen report above. No failure
or unexpected regression was reported. Private saves and screenshots have not
been added to the public repository.

The follow-up source changes are limited to the English Fortuna label, help
text and documentation. No save parser or write logic changed. The previously
delivered Test 1 archive remains the exact tested artifact; no repeat of the
game acceptance run is required for these text corrections.

The follow-up source passed `python -m unittest discover -s tests -q`
(31 public tests passed, 2 private-fixture tests skipped) and `git diff --check`.
