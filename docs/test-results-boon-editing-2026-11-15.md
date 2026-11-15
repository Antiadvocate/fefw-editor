# Boons Test 1 — implementation and player acceptance

This report records Test 1 and its price follow-up. The new Weapons Discount
editor control is covered by [Boons Test 2](test-results-weapon-boon-2026-11-15.md).

Date: 2026-11-15. The **existing EXP +10% on/off control is accepted on the
reported Leda Part I Chapter 9 / fefw-recomp-0.1.5 setup**. BEDIT-01–04 and
07 have player-reported passes; the returned saves verify Off/On persistence,
and BEDIT-05 records Leda gaining 16 EXP Off versus 17 On. This is one tested
action, not a general proof of the rounding formula or other tiers.

**BEDIT-06 has captured toggle mapping and a confirmed 10% listed-price
reduction in the follow-up On/Off/On shop comparison.** Weapons Discount
remains read-only; no discount editor control was tested. The player also
reported problems with the separately reconstructed B0 save.
Those restoration problems are not established editor defects, and their repair
notes are kept outside this repository. Relevant test conditions are recorded below.

Tested editor source: `052331e635708204d86dab781784cbcbdf0b8ed1`
(Boons Test 1). Research 1's original game captures remain in the
[earlier report](test-results-boons-2026-11-15.md).

## Scope

Only the observed existing EXP +10% state can be switched Off/On. Off adds
shared record `6447f467 = 1`; On removes it. The ownership-associated record
`3b6429de` must already be 1. Its value, currency and every unrelated record
are preserved. Other tiers, unknown values, purchases and other Boon edits
remain unavailable. The two screenshot-confirmed group names are displayed,
with original descriptive and Japanese searches retained.

## Original candidate automated checks

**81 tests passed locally with the private fixtures supplied:** 75 public
checks and six optional private tests. Without private fixtures, the suite
discovers 81 tests, passes 75 and skips six. No private save or game binary is
included in the repository or source ZIP.

The new public tests cover:

- Repeated off/on changes, preserving currency, ownership, other records and
  their byte encodings, plus normalized bytes outside the resized map.
- Missing/zero/unknown ownership, unknown disable states, invalid requests,
  sparse/ambiguous/duplicate maps, wrong ancestry and unrecognized headers.
- Byte-identical no-ops, including an existing wide disable marker; stored
  zero remains distinct from absence and cannot be silently normalized.
- Real page-handler edits, undo/redo, current-payload validation after cache
  replacement, disabled higher-tier/other-Boon selections, mirroring refusal
  and no history/dirty entry for a rejected or unchanged action.
- Search by screenshot-confirmed, descriptive and Japanese group names.

The existing five private regression tests also passed for Tutorials,
Blessings, audiences, Fast travel and all 32 editable Deeds counters.

## Six-capture validation

The new optional private test reads B02-EXP-before/off/on,
B03-purchase-before/after and B04-reloaded. For each of the six files it
writes each requested EXP state to a temporary file, then reloads it.
All twelve outputs pass header/payload checksum verification.

Before serialization, only the disable record and object-tree relocation
change. After save/reload, the resulting shared-map values exactly match the
original map with just that marker added/removed. Every other shared record,
Karma, tutorials, travel, Deeds progress/claims, all seven blessing EXP and
selection values, and Divine Sand are preserved. Original input bytes remain
untouched. These are structural checks, not proof of a game bonus.

## Native interface validation

The running editor was checked using a disposable copy of B02-EXP-before:

- Dark theme at 1240×800 and light theme at the 1000×640 minimum: table,
  horizontal scrollbar, selected details and action buttons fit.
- Selecting the first EXP tier enables only the state-changing action;
  selecting tier 2 disables both actions.
- Off, Undo to On and Redo to Off refresh the displayed state and buttons.
- Save followed by Reload retains Off and Karma 710. The output independently
  reloads with valid checksums and the expected marker.
- Enabling route mirroring blocks the action with a warning and leaves the
  saved state unchanged. Mirroring was disabled after the check.
- Searching `Weapons Discount` returns the three reference tiers without
  edits; first-tier purchase observation and higher-tier mapping are separate.

This desktop's existing font setup does not render Japanese/some Unicode
glyphs correctly. Japanese search is covered by the automated checks; the
player should check appearance in their own environment as before.

## Player results and returned captures

| Case | Outcome | Evidence and limits |
|---|---|---|
| BEDIT-01 | PASS, player reported | Display, search and selection checks accepted. |
| BEDIT-02 | PASS, player reported and save verified | `E02-off-edited` → `B02-off-game` retains `6447f467 = 1`; screenshot shows Off, owned 10%, next 20% locked, Karma 710. |
| BEDIT-03 | PASS, player reported and save verified | `B03-on-edited` → `B03-on-game` retains absence of `6447f467`; screenshot shows On, owned 10%, Karma 710. |
| BEDIT-04 | PASS, player reported | Undo/redo and the single-slot/mirroring guard accepted; no extra capture requested. |
| BEDIT-05 | PASS for the supplied EXP comparison | Leda only, one kill then retreat, reported by the player. Saves independently confirm +16 Off / +17 On at level 20. See control limits below. |
| BEDIT-06 | Research captured; price effect BLOCKED | Before is **unpurchased**, not an On baseline. On/Off are after purchase. Independent disable candidate isolated; actual Armorer price comparison unavailable. |
| BEDIT-07 | PASS, player reported and parsed regression checked | Tutorials, travel, Deeds, blessings, Gold/Renown/Karma match B0 across the menu-only Off/On captures. |

The returned `B02-off-game`, `B03-on-edited` and `B03-on-game` names correspond
to the guide's E02/E03 checkpoints. Filename variation is not a failure.
The original in-game slot filename was not restated; these labels identify
the returned containers, not game slot names. No new OS/route/version was
reported, so scope remains the previously reported setup.

All **12** returned containers (including B0) pass header and payload checksum
verification. Every file has Gold 1523, Renown 6640, Divine Sand 100 and identical
blessing EXP/selection values. The four menu-only captures preserve all named
flag values except the requested EXP disable marker. Normal save-session data
outside those parsed features can differ; whole game-resaved files are not
claimed to be byte-identical.

The `B02-off-game` → `B03-on-edited` decompressed payload exactly matches the
editor's On operation followed by its normal embedded-checksum refresh.
This independently links that supplied editor output to the intended write.

## BEDIT-05: measured EXP effect

| Branch | Raw EXP before → after | Level | EXP into level before → after | Screenshot Next before → after | Gain |
|---|---|---|---|---|---|
| Off | 1970 → 1986 | 20 → 20 | 70 → 86 | 30 → 14 | **16** |
| On | 1970 → 1987 | 20 → 20 | 70 → 87 | 30 → 13 | **17** |

Leda's person ID is `45e9244b`. The two before payloads match exactly after
applying the EXP On operation to the Off input and refreshing embedded
checksums. Their parsed unit states, class and starting inventory agree.
The disable marker remains 1 throughout Off and absent throughout On;
the EXP ownership-associated record remains 1 and Karma remains 710.

The before screenshot shows Hunter's Bow equipped; both after screenshots show
Zanbato. Both runs reorder the same first two inventory entries and increase
the same sword/infantry mastery values by 3 (628 → 631 and 385 → 388).
The enemy-defeat counter rises 281 → 282 in each run, and the evasion counter
rises 183 → 184. These observations support the reported comparable action.
The exact enemy identity and award calculation are not independently established
by these files. The measured +1 EXP is consistent with the +10% Boon after
integer handling; this one sample does **not** prove a universal rounding rule.

The player's Hugo Stronghold dialogue and feast prompt occurred during this
interval, so these are not isolated story-event captures. They do not justify
attributing every changed flag to the Boon.

### Named flag changes during each B05 run

Map numbers below are observed enumeration indices in these files, not safe
fixed locators for editing. Both runs have the following changes, except the
unit-list count noted explicitly:

| Map | Hash / identity | Before | After | Interpretation |
|---|---|---|---|---|
| 0 | `3c6b4ee1` / `拠点_所在_ダグシオンA1` | 1 | absent | Dagsion location record removed |
| 0 | `bcd41adb` / `拠点_所在_ダグシオン全エリア` | 1 | absent | Dagsion location record removed |
| 0 | `a2347320` / `記録_GMAP_歩数` | 2 | 10 | World-map step counter |
| 0 | `4cceb98e` | absent | 1 | **Unnamed; meaning unknown** |
| 0 | `f363a597` | absent | 1 | **Unnamed; meaning unknown** |
| 6 | `b5182f01` / `記録_部隊表_回数` | absent | Off: 2; On: 1 | Unit-list use counter; runs differ here |
| 9 | `50126cb8` / `実績_敵撃破数` | 281 | 282 | Enemy defeats |
| 9 | `6614ae03` / `実績_回避回数` | 183 | 184 | Evasions |

These are all value/presence differences found in the parsed named maps for
each before/after pair. They are not an exhaustive decode of the other save
blocks. Tutorials, travel and blessings are unchanged during both runs.

### Feast records already set before the prompt

| Hash / identity | B0 | Both B05 before files | Both B05 after files |
|---|---|---|---|
| `f0c779ce` / `機能開放_饗宴` | 1 | 1 | 1 |
| `3bb4016e` / `TUTO_饗宴` | 2 | 2 | 2 |
| `730acddc` / `実績_饗宴回数` | 5 | 5 | 5 |

The known feast feature-unlock flag did **not** change. Its presence, the
tutorial record and the historical feast counter do not establish that all
event/dialogue dependencies are consistent. The two unnamed additions above
cannot be called Hugo or feast flags from this combined interval. Further
event-specific captures are a separate save-restoration investigation.

## BEDIT-06: Weapons Discount research

| File | Karma | Purchase-associated `5bfcaa34` | Disable candidate `ddb8d06b` |
|---|---|---|---|
| W06-before | 710 | absent | absent |
| W06-on | 410 | 1 | absent |
| W06-off | 410 | 1 | 1 |

The player explicitly identifies W06-before as the **unpurchased B0 baseline**.
The 300-Karma reduction belongs to the purchase, not to an On/Off toggle.
Before → On adds only `5bfcaa34 = 1` among parsed named flags; On versus Off
differs only by `ddb8d06b = 1` there. Both post-purchase states preserve ownership,
Karma 410 and the existing EXP On state. Tutorials, Deeds, travel and blessings
also agree across this triplet. Thus `ddb8d06b` is a captured independent
Weapons Discount disable candidate; exact symbolic identity and higher tiers
remain unknown. Dedicated W06 On/Off screenshots were not included in this return;
state association comes from the player's named captures and report.

The Armorer was inaccessible in the original baseline, so the original
weapon-price comparison was blocked. The following return resolves that
specific evidence gap. Weapons Discount editing remains unavailable.

### Shop-price follow-up

Later on 2026-11-15, after separate personal-save restoration made the Armorer
accessible, the player completed the three On/Off/On price checks. Screenshots
`B0-02-on1.png`, `B0-02-off.png` and `B0-02-on2.png` show:

| Weapon | On 1 | Off | On 2 |
|---|---:|---:|---:|
| Wooden Sword | 270 | 300 | 270 |
| Bronze Sword | 450 | 500 | 450 |
| Iron Sword | 1,350 | 1,500 | 1,350 |
| Iron Sword+1 | 1,800 | 2,000 | 1,800 |
| Wooden Spear | 270 | 300 | 270 |
| Bronze Spear | 450 | 500 | 450 |
| Iron Spear | 1,350 | 1,500 | 1,350 |
| Iron Spear+1 | 1,800 | 2,000 | 1,800 |
| Javelin | 1,350 | 1,500 | 1,350 |
| Javelin+1 | 1,800 | 2,000 | 1,800 |
| Wooden Axe | 270 | 300 | 270 |

Every displayed On price is exactly 90% of the matching Off price, and both
On captures agree. This verifies the listed-price effect of the purchased
10% Boon on this setup. These prices do not exercise fractional rounding;
no completed purchase or transaction deduction was tested.

The player returned **one save after all three tests**, `After-02-tests`.
Its container checksums are valid, `5bfcaa34 = 1`, `ddb8d06b` is absent, and
Karma remains 410. This is the expected final On shape. There are no separate
intermediate saves from this round, so intermediate save/reload persistence
is not independently established by it. The earlier W06 triplet remains the
evidence for the stored Off/On marker association.

The accepted private baseline and remaining restoration work are tracked
outside this repository. Neither this price evidence nor that baseline
acceptance establishes a defect in the editor or validates an unimplemented
Weapons Discount editing control.

## Acceptance cleanup validation

The cleanup removes stale gameplay-pending wording from the EXP control and
updates the read-only Weapons Discount explanation. No edit scope is expanded.
Four optional read-only capture tests reproduce the returned persistence,
EXP gains, weapon-toggle mapping and unchanged feast records. The original
synthetic safety tests remain in place. With all three private fixture variables
set, **85 tests pass**; public CI discovers 85, passes 75 and skips 10 private
tests. Use:

```sh
FEFW_TEST_SAVE=/path/to/B0 \
FEFW_BOON_CAPTURE_DIR=/path/to/research-captures \
FEFW_BEDIT_CAPTURE_DIR=/path/to/bedit-captures \
python -m unittest discover -s tests -v
```

Inputs are read only. Original Research 1 fixtures and BEDIT fixtures may share
one folder. Save files, screenshots, video and game binaries are excluded from
the repository. The existing downloadable Boons Test 1 remains the tested
candidate; this acceptance cleanup does not require another gameplay run.

## Private input fingerprints

SHA-256 identifies the exact returned containers without publishing their bytes.

| Capture | Bytes | SHA-256 |
|---|---:|---|
| B0 | 41052 | `1f2823df224b4f27d416951ff3b386c8760649243e99d306276f46cc9c009d7c` |
| E02-off-edited | 40985 | `24632c8ea28d851c60cbce87958f388cccb930c76c5aa44a4a65ca8b168560b2` |
| B02-off-game | 45629 | `4fe9efe7f68860cde26e0fe974be1f235134f806c2a4c2887eb1471b07dcfb07` |
| B03-on-edited | 41073 | `02a6640b117cbe5ce1f4c45c0e58f1d4aad2292e0dab5235cf2b876cef9aa202` |
| B03-on-game | 48253 | `323552234fbb6904a12afdeca9216572df134be099ae8db902bf02d2d6694400` |
| B05-off-before-XP | 45628 | `bec56283ab7a4d830b70ebdb95265d3204846cd44a4bcf4b86f3fd869eaaf691` |
| B05-off-after-xp | 63276 | `b9649de19f6dbc1530fde3768d2f0d78b69768b91576578c9c7e755def77e31d` |
| B05-on-before-xp | 41052 | `1f2823df224b4f27d416951ff3b386c8760649243e99d306276f46cc9c009d7c` |
| B05-on-after-xp | 64627 | `5f71121af53faae47fe55177eeb359e093c75c566a3802d8b8a73f3cb6fc436e` |
| W06-before | 41052 | `1f2823df224b4f27d416951ff3b386c8760649243e99d306276f46cc9c009d7c` |
| W06-off | 45532 | `c11ea633c23f5d089dc15f308ef54c5a102d3f5a45994c9cdffe958852b415aa` |
| W06-on | 45626 | `6a24805d24373b550162d133675bcda445287ea9b26fdc9374eb0627450c708d` |
| After-02-tests | 47342 | `fdfee0c4ef5a30fbb3f9370d3d89805d38152a1ee4e3a7db5bd293bed9f2681f` |
