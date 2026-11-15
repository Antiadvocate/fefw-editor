# Boons Test 2 — Weapons Discount editor validation

Date: 2026-11-15. **Local implementation checks pass; player acceptance of
the new editor control is pending.** The earlier in-game Off/On mapping and
10% listed-price effect are already documented in the
[Test 1 follow-up](test-results-boon-editing-2026-11-15.md#shop-price-follow-up).
This build does not claim a new successful gameplay round.

## Resulting behavior

Weapons Discount tier 1 now displays On/Off and exposes the state-changing
button when purchase record `5bfcaa34` is exactly 1 and disable record
`ddb8d06b` is absent or 1. Off adds only `ddb8d06b = 1`; On removes it. An
unknown ownership/disable value, unpurchased Boon, ambiguous shared map or
unrecognized header is rejected without mutation. No-op requests preserve
all bytes and create no undo entry. EXP's separate marker is preserved.

The EXP control remains accepted. Other Boons, higher tiers, purchases,
refunds and eligibility edits remain unavailable. No private save, screenshot,
video or game binary is included in this repository or the editor package.

## Upstream merge

Merged `Antiadvocate/fefw-editor` main at
`7157e6c771bf19bbe49b53f36e2c936d33f403b0` without conflicts:

- v1.3.9 numbered backups: preserve `.bak`, then `.bak1`, `.bak2`, etc.,
  choosing one greater than the highest number present. Identical newest
  backup content is not duplicated. Backups remain outside slot discovery.
- The preceding v1.3.8 weapon-mastery multi-selection fix is included.

The upstream backup implementation is retained. Added regression tests
verify preservation of a game-written disk state between editor saves,
original and legacy `.bak` retention, numeric order/gaps, unrelated filenames,
duplicate suppression, backup-disabled behavior and refusing to overwrite
the slot when backup creation fails. A private integration check exercises
the real rank/EXP/remove handlers on two selected mastery rows and confirms
the unselected entries remain unchanged.

## Automated validation

**99 tests passed locally with all private fixtures supplied.** Public CI
discovers 99 tests: 86 public tests and 13 opt-in private tests skipped when
their inputs are unavailable. The new synthetic coverage includes:

- Repeated weapon Off/On changes, exact preservation of unrelated raw flag
  encodings and normalized bytes outside the shared map.
- Missing/zero/unknown ownership, unknown disable states, invalid requests,
  wide-marker no-ops, duplicate/sparse/ambiguous maps and wrong ancestry.
- Independent EXP/weapon toggles, including preservation of an unknown EXP
  disable value during an otherwise valid weapon edit.
- Actual page handlers, current-payload revalidation, Undo/Redo, mirroring
  refusal, higher/unrelated rows, no-op history and unknown-state gating.

The private tests compare the new writer against the controlled W06 On/Off
shared maps and reject W06-before, which is unpurchased. They serialize/reload
both directions on W06-on, W06-off and the accepted baseline: six outputs.
Each has valid checksums and the intended payload plus checksum refresh.
All unrelated flags and live unit numbers remain unchanged, including the
accepted baseline's nine distinct unit numbers and Kalla gate flag. The
outside-map comparison covers inventory, units, quests and other payload
contents; source files remain untouched. Real save calls also verify that
pre-save disk contents are retained in original/numbered backups.

```sh
FEFW_TEST_SAVE=/path/to/original-B0 \
FEFW_BOON_CAPTURE_DIR=/path/to/research-captures \
FEFW_BEDIT_CAPTURE_DIR=/path/to/bedit-captures \
FEFW_WEAPONS_TEST_SAVE=/path/to/accepted-B0-01/Auto \
python -m unittest discover -s tests -v
```

The accepted baseline fixture is the supplied `Auto` from
`B0-01-Unit-Selection-Test-1.zip`, SHA-256
`8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663`.
The later Auto(2) gameplay return is evidence, not the chosen baseline.

## Native interface validation

The actual Tk application was exercised on a disposable copy of the accepted
baseline. Button invocation, exact Undo/Redo restoration, Save/reopen in both
states, original `.bak` and later `.bak1`, mirroring refusal and higher-tier
gating passed. EXP stayed On and Karma stayed 410. Dark 1240×800 and light
1000×640 layouts were rendered and inspected for the English controls, state
labels and action area. Private screenshots are not published.

## Remaining acceptance

[WEDIT-01–07](testing-weapon-boon.md) check editor-generated Off/On states and
prices after game save/reload, independent EXP control, backups and a brief
menu regression. The expected Wooden Sword prices are 300 Off / 270 On with
Karma 410. Four captures distinguish edited files from game-resaved files.
No repeat of the accepted EXP battle comparison or personal-repair suites is
requested. Higher tiers, fractional-price rounding and full-folder state
synchronization remain outside this build's evidence.
