# Boons of Salvation: reference catalogue and mapping status

**Boons Test 1** adds a narrowly scoped on/off control for an **already-owned
EXP +10% Boon**. Select **Increased Exp, tier 1**, then **Turn on** or **Turn
off**. Only the state-changing button is enabled. These actions change memory;
Save writes the selected slot, Undo/Redo restores the state. Turn off route
mirroring. Other tiers and Boons remain read-only.

The catalogue contains 81 reference tiers in 31 groups, costs and clear-count
fields. **Increased Exp** and **Weapons Discount** now use screenshot-confirmed
wording. Other names are descriptive translations. English/descriptive and
original Japanese search all remain available. Reads as is the catalogue group
identifier, not a claimed symbolic save key. Reference values are not current
bonuses. Weapons Discount's first-tier row reports its purchase-associated raw
record; it does not infer activation or a working price reduction.

## Editing boundary and byte layout

The live shared-map locator requires two known anchors, unique keys and
expected GameUserData ancestry. No map number or fixed save offset is used.
The player resource header must also be recognised. EXP editing is available
only when `3b6429de = 1` and `6447f467` is absent or 1; absent/zero/unknown
ownership and other disable values remain read-only. This state shape matches
the captured +10% Boon; it does not decode later tiers.

* **Off:** add `6447f467 = 1` with the map's compact encoding.
* **On:** remove `6447f467`; do not replace it with zero.
* Already at the requested state: preserve all bytes and do not add an undo entry.
* Every other record, including `3b6429de` and `5bfcaa34`, remains unchanged.
  No Karma, claim, tier, eligibility, global-file or other-slot write is made.

The existing object-tree replacement relocates pointers when the map resizes;
serialization updates checksums. Unknown records and their compact/wide
encodings are preserved. The UI refuses actions with route mirroring enabled,
validates the current payload before adding undo history, and refreshes status
and buttons after edits, Undo/Redo and reload.

The existing EXP +10% toggle is **accepted on the reported Leda Chapter 9
setup**. Editor-generated Off/On states persist in game, and a one-kill/retreat
comparison gives Leda +16 EXP Off versus +17 On. The sample supports an effect
but does not establish a universal rounding rule. See the
[acceptance report](test-results-boon-editing-2026-11-15.md) for controlled
starting states, incidental gameplay changes and coverage limits.

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

The EXP disable marker has an isolated off/on comparison, but EXP purchase
semantics, higher tiers, stacking and cross-file synchronization remain unknown.
BEDIT-06 now supplies an independent Weapons Discount disable candidate:
`ddb8d06b = 1` in Off, absent in On, while `5bfcaa34 = 1` and Karma 410 remain
unchanged. Its W06-before file is unpurchased (Karma 710), so the 300-Karma
decrease is the purchase. The original shop-price test was blocked by Armorer
access. A later On/Off/On comparison at the accessible shop shows 10% lower
listed prices in both On states: 300 → 270, 500 → 450, 1,500 → 1,350 and
2,000 → 1,800. One final On save preserves the purchase marker and Karma 410
with no disable marker; the two intermediate states have screenshots only.
See the [price follow-up](test-results-boon-editing-2026-11-15.md#shop-price-follow-up).
Keep Weapons Discount read-only pending its own implementation and editor
acceptance. Its exact symbolic key, later tiers and fractional-price rounding
remain unknown. Do not generalise the EXP toggle to other Boons.

The requested return to the 15 read-only Deeds counters is tracked in
[deeds-follow-up.md](deeds-follow-up.md), starting with the three enemy counters.

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
