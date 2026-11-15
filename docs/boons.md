# Boons of Salvation: levels, activation and evidence

**Boons Test 4** corrects the eight skill-EXP aliases implicated in Test 3's
partial bulk-unlock failure. Brawling and Black-Magic tier 1 level/Off keys
match isolated game captures. The player now confirms **all Boons are maximum
and On, with save/load persistence**. Bulk-max game acceptance has passed on
the reported setup; this does not verify every intermediate tier or effect. The [investigation](boon-key-investigation.md) records the evidence and
why no general string-length limit is applied.

All **31 Boons / 81 listed tiers** remain editable in the
selected save. Select a row and **Set selected tier**, or **Set all to max**
to grant the maximum tier of every group, including groups hidden by search.
**Remove Boon** removes its owned level. Tier edits preserve the independent
On/Off switch; select the currently owned tier to **Turn on / Turn off**.
Save writes changes. Each action, including the full bulk edit, is one
Undo/Redo step. Route mirroring must be off. **Flags is the far-right tab.**

The Evidence column distinguishes **Game-tested** tiers (EXP 1 and Weapons
Discount 1/2), **Save-verified** purchase/toggle mappings (Brawling and
Black-Magic tier 1), and **Inferred** mappings. Save verification does not
claim that those editor changes or battle effects have been accepted in game. Weapons Discount 20% worked and
persisted before its normal progression requirement: Wooden Sword 240 On /
300 Off, Bronze Sword 400 On / 500 Off. This supports broad tier editing using
the shared key pattern; it does not verify every other group's gameplay effect.
See the [WD20 results and Test 3 validation](test-results-boon-levels-2026-11-15.md)
and [usage guide](testing-boon-levels.md).

**Increased Exp** and **Weapons Discount** have screenshot-confirmed names.
Other labels are descriptive translations. Reads as keeps the original group
identifier. Value, Game cost and Required clears come from Reward.bin. These
purchase requirements are separate from ownership and activation; the save's
eligibility source has not been decoded, so no Locked/Unlocked value is invented.
The editor spends no Karma, grants no refund and changes no progression.

## Save mapping and editing boundary

The shared-map locator requires unchanged anchors, unique keys, expected
GameUserData ancestry and a recognized resource header. No fixed map index or
save offset is used. Groups are allowlisted from the catalogue.

| Field | Mapping | Evidence |
|---|---|---|
| Owned level | low 32 bits of FNV-1 64 of UTF-8 `因果報酬_レベル_` + save-key name | Names reproduce EXP `3b6429de` and Weapons `5bfcaa34`; Weapons 1 → 2 gives 10% → 20% in game |
| Disable marker | Continue low-32-bit FNV-1 state `a21ab2b4` over the UTF-8 save-key name | Independently reproduces EXP `6447f467` and Weapons `ddb8d06b`; original prefix text is unknown |
| On | Disable marker absent | Captured EXP tier 1 and Weapons tiers 1/2 |
| Off | Disable marker 1 | Captured EXP tier 1 and Weapons tiers 1/2 |

Eight skill groups use explicit save-key aliases: 格闘→格, 黒魔法→黒,
白魔法→白, 歩兵→歩, 騎兵→騎, 重装→重, 飛行→飛 and 指揮→指,
after 技能経験. The first two are capture-verified; the other six were inferred
and now have player acceptance for maximum-tier On state and persistence.
Other groups retain their full catalogue names. A general truncation rule has
not been established, including for blessing-cost Boons.

The same level prefix and disable hash-state are **extrapolated** where no
independent capture exists. All 62 generated keys are distinct. These are inferred mappings,
not recovered executable logic. Lower rows say Below tier N; only the owned
row displays On/Off. There is one owned level per group, not independent
ownership of each displayed row.

* Valid levels are absent/0 (not owned), or 1 through that group's listed maximum.
  Level 0 requests remove an owned record; already-absent or stored-zero no-ops
  preserve their original bytes. Out-of-range levels are preserved and refused.
* Off writes only disable value 1; On removes that marker. Unknown disable
  values are preserved and prevent edits to that group. A switch requires an
  owned tier, including when level and activation are requested atomically.
* Tier changes and removal preserve On/Off markers. Re-adding a previously Off
  Boon therefore keeps it Off. Set all to max preserves all switches, too.
* Every requested group is validated before mutation. One unknown group aborts
  a bulk edit; unrelated valid groups can still be edited individually.
* Incorrect Test 3 full-name skill records are ignored for ownership and
  preserved as unrelated records; no old maximum is silently migrated. Explicit
  tier edits or bulk max write the corrected keys.
* Unselected records, compact/wide encodings, currency, claims and progression
  are preserved. No-op requests preserve every byte and add no undo entry.
* A changed map is rebuilt once, with pointer relocation and serialization
  checksums handled by the existing object-tree writer. The UI revalidates the
  current payload, refuses mirroring, and refreshes after edits and Undo/Redo.

The earlier first-tier helper functions remain for reproducing historical tests;
the new UI uses the catalogue-scoped writer. The accepted EXP battle comparison
remains +16 Off / +17 On, without establishing a universal rounding formula.
The [Test 2 report](test-results-weapon-boon-2026-11-15.md) retains the earlier
10% editor acceptance and numbered-backup evidence.

## What was known when Research 1 shipped

* The user manually claimed rewards and purchased/activated EXP +10%. The
  working save contains shared-map hash `3b6429de` with raw value **1**.
* This was a combined-action comparison. The symbolic key, relationship to
  purchase versus activation, and possible storage in other save files are
  still unknown. The tab labels the record **EXP-associated**, not Owned/Active.
* The earlier guessed `因果報酬_経験値` (`7178d8f9`) write failed in game and was
  discarded. It is not used by this implementation or offered as a preset.
* The reference data's first EXP tier has value 10, listed cost 500, and clear
  count 0. The user's working EXP +10% confirms that first visible effect.
  Later tiers and other effects still need controlled game evidence.
* B0 and the supplied post-DEED-05 claim save both contain candidate value 1;
  their Karma balances are 710 and 720 respectively. These reads do not isolate
  how the Boon was acquired, nor prove the other Boon states.

The first [numbered capture guide](testing-boons.md) isolates an existing EXP
activation control, if one exists, and one weapon-discount purchase on a
separate baseline copy. A missing control must be recorded rather than assumed.
Effects and stacking need a subsequent round after the save mapping is known.

## Research 1 capture results — 2026-11-15

The player has completed the [first capture round](test-results-boons-2026-11-15.md#player-results-and-controlled-save-comparisons).
The six supplied individual save containers establish:

| Observed operation | Live shared-map change | Karma |
|---|---|---|
| Existing Increased Exp 10% off | Add `6447f467 = 1`; `3b6429de` remains 1 | 710 unchanged |
| Existing Increased Exp 10% on | Remove `6447f467`; `3b6429de` remains 1 | 710 unchanged |
| Buy Weapons Discount 10%, immediately active | Add `5bfcaa34 = 1` | 710 → 410 |
| Reload after purchase | `5bfcaa34 = 1` persists | 410 unchanged |

Thus EXP has a separate disable marker; its older candidate record is not
sufficient to indicate whether the effect is active. Exact symbolic keys,
higher-tier encodings, weapon-discount disable state, cross-file propagation
and measured gameplay effects were still unknown at this Research 1 stage.
BEDIT results below supersede the EXP-effect and discount-disable gaps. These results do not establish
EXP purchase semantics. The Weapons Discount capture combines purchase and
automatic activation, so its added record is described as purchase-associated.

Screenshots confirm **Increased Exp** and **Weapons Discount** as group
wording. The left-hand 20% locked rows show the next tier; the right-hand
10% status is the owned tier. Keep those separate when designing the UI.
Research 1's published catalogue labels and conservative inspector are
unchanged by this documentation update.

All six containers pass checksum checks and preserve the other parsed
feature data recorded in the report. A separate unidentified map-4 flag
appears on the post-purchase reload; do not treat it as a Boon flag. Full
folder synchronization and actual EXP/shop-price effects were not tested.

## Reference format

The supplied `Reward.bin` has multiple sections. The Boon section descriptors
are at `0xac10` through `0xacf0`; the 81 rows are 64 bytes each at
`0xad10` through `0xc14f`. These are offsets in the supplied **game-data file**,
not offsets to patch in a save. Strings use the table's 32-byte pointer base.

| Row field | Offset | Type | Meaning from table |
|---|---|---|---|
| Group identifier | +8 | u64 string pointer | First row names a group; subsequent unnamed rows continue it |
| Item name | +32 | u64 string pointer | Message identity |
| Reward name | +40 | u64 string pointer | Display-format message identity |
| Help | +48 | u64 string pointer | Help message identity |
| Effect | +56 | u8 | Effect code |
| Operation | +57 | u8 | Operation code; preserved in catalogue |
| Value | +58 | u8 | Reference effect value, not current player state |
| Clear count | +59 | u8 | Requirement field; what counts as a clear still needs game confirmation |
| Karma value | +60 | u16 little-endian | Listed price; incremental versus cumulative tier costs need observation |

`boon_catalog.json` contains these factual values and concise descriptive
labels, without game binaries or help-text dumps. Tier numbers are one-based
presentation indexes within each group, not decoded save values. Operation
codes are retained for research; the UI shows the raw reference value so an
unverified interpretation is not turned into an effective current bonus.

## Remaining research

[WD20-01–03](testing-weapon-discount-20.md) passed with screenshots and two
returned game saves. The 20% owned status and prices persist while the next
30% offer remains Locked. Only the intended level and activation records differ
from the accepted baseline's parsed flags. The test changes no progression.

General editing is now implemented at the user's request. Effects, stacking,
later tiers outside those listed as Game-tested, fractional-price rounding and
full-folder synchronization remain unverified. Normal purchase accounting and
the save-side source of clear-count eligibility remain outside this feature.
Unknown observed values are never normalized automatically.

The requested return to the 15 read-only Deeds counters is tracked in
[deeds-follow-up.md](deeds-follow-up.md).

## Catalogue

Each sequence below follows tier order. Names and clear requirements still
need in-game confirmation beyond the first EXP effect.

| Descriptive group | Reads as | Values | Listed costs | Clear counts |
|---|---|---|---|---|
| Experience | `経験値` | 10, 20, 30, 40, 50 | 500, 500, 1000, 1000, 1000 | 0, 1, 1, 2, 3 |
| Class experience | `兵種経験` | 1, 2 | 1000, 2000 | 1, 3 |
| Sword skill experience | `技能経験剣` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Lance skill experience | `技能経験槍` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Axe skill experience | `技能経験斧` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Bow skill experience | `技能経験弓` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Brawling skill experience | `技能経験格闘` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Black magic skill experience | `技能経験黒魔法` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| White magic skill experience | `技能経験白魔法` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Infantry skill experience | `技能経験歩兵` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Cavalry skill experience | `技能経験騎兵` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Armour skill experience | `技能経験重装` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Flying skill experience | `技能経験飛行` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Command skill experience | `技能経験指揮` | 1, 2, 3 | 300, 300, 300 | 0, 1, 2 |
| Weapon discount | `武器割引` | 10, 20, 30 | 300, 300, 300 | 0, 1, 2 |
| Item discount | `道具割引` | 10, 20, 30 | 300, 300, 300 | 0, 1, 2 |
| Gift discount | `贈答割引` | 10, 20, 30 | 300, 300, 300 | 0, 1, 2 |
| Room rental discount | `宿泊割引` | 20, 40 | 300, 300 | 1, 2 |
| Meal discount | `食事割引` | 20, 40 | 300, 300 | 1, 2 |
| Theatre discount | `観劇割引` | 20, 40 | 300, 300 | 1, 2 |
| Bath discount | `風呂割引` | 20, 40 | 300, 300 | 1, 2 |
| Blacksmith discount | `鍛冶割引` | 10, 20, 30 | 300, 300, 300 | 1, 2, 3 |
| Carriage discount | `馬車割引` | 20, 40 | 300, 300 | 1, 2 |
| Dungeon pursuit (effect unconfirmed) | `迷宮回避` | 1 | 300 | 3 |
| Dungeon materials | `迷宮素材` | 10, 20, 30 | 300, 300, 300 | 1, 2, 3 |
| Aurora blessing cost reduction | `加護消費_アウロラ` | 20, 50 | 300, 300 | 1, 3 |
| Mars blessing cost reduction | `加護消費_マーズ` | 20, 50 | 300, 300 | 1, 3 |
| Smyrnos blessing cost reduction | `加護消費_スミルノス` | 20, 50 | 300, 300 | 1, 3 |
| Jurah blessing cost reduction | `加護消費_ジュラ` | 20, 50 | 300, 300 | 1, 3 |
| Kalla blessing cost reduction | `加護消費_カーラ` | 20, 50 | 300, 300 | 1, 3 |
| Credna blessing cost reduction | `加護消費_クレール` | 20, 50 | 300, 300 | 1, 3 |

## Flags names

The Flags tab now names all 31 tier and 31 disable records in English. Tier
records retain their exact Japanese keys, including the eight abbreviated
skill aliases, in Reads As. The disable hashes are mapped but their original
prefix text is unrecovered; those Reads As cells remain empty. Descriptive
labels do not change hashes, values, evidence levels or Boon behavior.
