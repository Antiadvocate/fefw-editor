# Boons Test 2 — Weapons Discount editor acceptance

Date: 2026-11-15. **WEDIT-01–07 all passed by player report; Weapons Discount
10% editing is accepted on the reported Leda Chapter 9 setup.** Four returned
saves corroborate Off/On editing, persistence and preservation. The player
reports prices matching the earlier screenshots and numbered backups through
`.bak4`; no new price screenshots or backup files were supplied.
The earlier in-game Off/On mapping and 10% listed-price effect are documented in the
[Test 1 follow-up](test-results-boon-editing-2026-11-15.md#shop-price-follow-up).

## Player results and returned saves

| Case | Result | Evidence |
|---|---|---|
| WEDIT-01 — Display and scope | Pass | Player report; tier gating also covered by automated and native-interface checks |
| WEDIT-02 — Editor Off | Pass | Edited and game-resaved Off captures retain disable marker 1 and Karma 410; player reports the earlier undiscounted prices after load/reload |
| WEDIT-03 — Editor On | Pass | Edited and game-resaved On captures omit the disable marker and retain Karma 410; player reports the earlier discounted prices after load/reload |
| WEDIT-04 — Undo, redo and mirroring | Pass | Player report; automated/native checks also passed |
| WEDIT-05 — Independent EXP control | Pass | Player report; independent toggles covered by automated checks; EXP is On in all four returned files |
| WEDIT-06 — Numbered backups | Pass | Player observed `.bak`, `.bak1`, `.bak2`, `.bak3`, `.bak4`; those backup files were not attached for content comparison |
| WEDIT-07 — Brief regression | Pass | Player report and save-content comparisons described below |

The price reference remains the earlier screenshots: Wooden Sword 300 Off /
270 On, Bronze Sword 500 / 450, Iron Sword 1,500 / 1,350 and the shown upgrades
2,000 / 1,800. This round's matching display is player-reported, not newly
screenshot-verified. Backup numbering is likewise player-reported; content
preservation is supported by the existing automated backup tests, not a byte
comparison of the player's `.bak` files.

Both editor-generated payloads exactly reproduce the requested toggle plus
embedded-checksum refresh: accepted baseline → WE02-off-edited (Off), then
WE02-off-game → WE03-on-edited (On). This full-payload comparison verifies
that the editor made only the intended change and required structural/checksum
updates. The game-resaved files are assessed by parsed contents, not claimed
to be byte-identical to their editor-generated inputs.

All four containers have valid checksums and parse as valid object trees.
Their purchase marker `5bfcaa34` remains 1. The two Off files hold
`ddb8d06b = 1`; both On files omit it. EXP ownership `3b6429de = 1` remains
present and EXP's disable marker is absent. Gold 1,523, Renown 6,640 and Karma
410 are unchanged. Apart from the weapon disable marker, all parsed flag maps
match the accepted baseline. Deeds, tutorials, fast-travel records and all
seven blessing records, including Divine Sand 100, also match.

The nine live unit numbers remain distinct and unchanged: Leda 47, Buccar 48,
Sirocco 1, Mu 2, Catania 3, Olympia 4, Loretta 5, Jasmine 6 and Io 7.
The Kalla gate (`3fdd2f30 = 1`) and ordinary Kalla temple (`b482d5dc = 1`)
remain present; shop restrictions `b9a0e16b` and `5e9748e0` remain absent, as
does the stables unlock `63fc6b22`. These are preservation checks on the
accepted save, not new personal-repair issues or a repeat battle test.

### Capture fingerprints

Private files are not published. The final On game return was received as
`W03-on-game`, without the E; its contents verify the intended On state.

| File | Bytes | SHA-256 |
|---|---:|---|
| WE02-off-edited | 41,154 | `5b2b513f415a448e1aa56b8bfdd9c5f22f3d76c74bf0c0bd530307e586676d05` |
| WE02-off-game | 48,636 | `147995c13f9d7c8e84a18eef34f93dab203f31018fedc0d0f0b6f6f725cf0889` |
| WE03-on-edited | 41,170 | `85447addce08cc1aafdb736a1a612ba056944752d02024abd3d8a6d6d724cbf4` |
| W03-on-game | 48,443 | `02757388228bd5227541ea65dc697e0f592b7be165a88eceeae386050aae3023` |

The accepted baseline remains **Auto supplied in B0-01-Unit-Selection-Test-1.zip**.
These returned test saves do not replace it. No further screenshots or gameplay
tests are required to accept this toggle.

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

The Test 2 implementation passed **99 tests locally with all private fixtures
supplied** before delivery. Acceptance cleanup adds two read-only private
capture checks: exact reproduction of the edited payloads and preservation
across all four returned saves. **All 101 tests passed locally with every
private fixture supplied** after cleanup. Public CI discovers 101 tests:
86 public tests and 15 opt-in private tests, skipped when their inputs are
unavailable. The synthetic coverage includes:

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
FEFW_WEDIT_CAPTURE_DIR=/path/to/wedit-captures \
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

## Coverage limits

[WEDIT-01–07](testing-weapon-boon.md) are complete for the reported setup.
Higher tiers, fractional-price rounding, purchases/refunds, other Boons and
full-folder state synchronization remain outside this build's evidence.
The cleanup removes the pending-acceptance note from the Weapons Discount
interface; it does not change either toggle writer or upstream backup behavior.
The tested Test 2 package remains usable.
