# Weapons Discount 20%: locked-tier experiment

**Accepted on 2026-11-15.** WD20-01–03 passed. Screenshots show owned 20% On
and Wooden/Bronze Sword prices 240/400, 300/500 Off, and 240/400 again On.
The two returned saves retain level 2 and the expected activation marker,
Karma 410 and other parsed flags. See the [results](test-results-boon-levels-2026-11-15.md).
The procedure below records the completed experiment; no repeat is requested.
The accepted baseline remains the supplied B0-01 Auto.

## Question and candidate

Can the second Weapons Discount tier apply and persist when the save has not
met its normal purchase requirement? The baseline's menu showed Weapons
Discount 20% locked. The reference table lists values 10/20/30, clear counts
0/1/2 and cost 300 for each tier. This experiment changes only the observed
weapon purchase-associated marker `5bfcaa34` from **1 to 2**. It does not pay
300 Karma or alter the progression that originally locked the next tier.
Value 2 representing tier 2 is the hypothesis under test, not an established
encoding. It is not a test of purchasing the upgrade normally.

Two hash-matching candidate names support that hypothesis:

| Observed record | Candidate name | Hash |
|---|---|---|
| EXP ownership / level | `因果報酬_レベル_経験値` | `3b6429de` |
| Weapons ownership / level | `因果報酬_レベル_武器割引` | `5bfcaa34` |

Both match the editor's existing identifier hash function (low 32 bits of
FNV-1 64 over UTF-8). The common prefix means “causality reward / level”. These
names were derived by hash matching, not recovered from executable code.
They do not establish the separate disable keys, tier semantics in every
group, or the save field that controls purchase eligibility.

## Run the test

1. Close the game and keep a backup of the save folder. Extract
   **Weapons-Discount-20-Test-1.zip** and use its **Auto** in the same save slot
   as the previous tests. It starts from Auto in the accepted
   **B0-01-Unit-Selection-Test-1.zip**, with Gold 1,523, Renown 6,640, Karma 410
   and EXP 10% On.
2. Check the three cases below. Use the **in-game** Boon switch for Off/On.
   The Test 2 editor used for this experiment treated level 2 as
   **Unknown / read-only**; Test 3 now supports it. That old message did not mean the game rejected it.
3. Return the two named game-saved files and the results. Screenshots of the
   Boon status and shop prices are useful because this is a new tier. Avoid
   buying an upgrade or weapon during the comparison.

| ID | Check | Expected if the hypothesis works |
|---|---|---|
| **WD20-01 — Load and effect** | Load the supplied Auto. Inspect Weapons Discount's owned **Status** value and On/Off indicator, the next offer and its Locked text, then the Armorer's prices. | Status **20% On**, Wooden Sword **240**, Bronze Sword **400**, Karma **410**. Record the actual next offer/lock text; the left-hand offer may advance to 30% while the right-hand owned value is 20%. |
| **WD20-02 — Disable** | Turn Weapons Discount Off in game, check the same prices, save and quit. Copy the slot as **WD20-off-game**. | Owned status remains 20%, switch Off; Wooden Sword **300**, Bronze Sword **500**. Karma remains 410. |
| **WD20-03 — Enable and persist** | Reload the Off save and confirm its state. Turn On in game, save, quit and reload. Recheck the Boon and prices, then copy the slot as **WD20-on-reloaded**. | Off persisted before enabling; final status **20% On**, prices **240 / 400**, Karma **410**. |

If the game refuses the file, shows 10%, removes the state, or displays a
different price, report that result. If it still loads, keep a game-resaved
copy even when the hypothesis fails; the normalization is useful evidence.
There is no need to repeat battles, unit-selection, gate or backup tests.
Restore the accepted baseline after the experiment unless you explicitly
choose to adopt this candidate later.

```text
WD20-01: owned status / On-Off / next offer and lock text / prices / Karma:
WD20-02: owned status / prices / Karma:
WD20-03: Off after first reload / final status / prices / Karma:
Anything unexpected:
```

## Local validation and reproduction

The generator requires the exact accepted source, SHA-256
`8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663`.
It changes one compact live flag value, preserves every other payload byte
before checksum refresh, and checks the serialized output against that exact
expected payload. It also verifies checksums, the object tree, all other flags,
unit data and nine distinct unit numbers, currency, Deeds, tutorials, travel,
blessings and the untouched source. The output directory must be new.

Generation passed all these checks. The resulting Auto is 39,549 bytes with
SHA-256 `b332d2914943ae6f95a0a6d003eac534bf3b05bf6031065f58c53871a8b7dfcd`.
Exactly one payload byte changes at the located live value (offset 3,870 in
this source); embedded snapshots require no changes. Wrong-source and
existing-output attempts both refuse without writing. The 10 existing Boon
catalogue/EXP regression tests also pass. These are local structural checks,
not evidence of a working 20% gameplay effect.

```sh
python research/weapon_discount_tier_probe.py \
  --input /path/to/accepted-B0-01/Auto \
  --output /path/to/new-test-directory
```

The private ZIP contains Auto, this guide and a generated changes.json with
the output fingerprint and validation results. Personal save bytes are not
published to GitHub.

## Implementation after this result

The pass supports Weapons Discount tier 2 without changing its normal purchase
eligibility. Boons Test 3 now exposes catalogue-bounded levels and switches for
all groups using the shared hash pattern, with the untested mappings labelled
Inferred. The game's eligibility source remains unknown; no Locked/Unlocked
column is inferred from a stored level or catalogue clear requirement. See
[the current format](boons.md) and [usage guide](testing-boon-levels.md).
