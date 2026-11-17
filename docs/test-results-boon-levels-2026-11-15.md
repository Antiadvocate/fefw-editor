# WD20 acceptance and Boons Test 3 validation

Historical report. The subsequent [Test 4 investigation and validation](test-results-boon-skill-keys-2026-11-15.md)
records isolated Brawling/Black-Magic captures and corrected skill aliases.

## Subsequent Test 3 game failure

The player reports Set all to max only partly worked. Screenshots show EXP 50%,
Sword/Spear/Axe/Bow +3 and Weapons/Items/Gifts discounts 30%, while Brawling,
Black-Magic, White-Magic, Infantry, Rider, Heavy, Flier and Authority EXP remain
at +0 and offer their first tier for 300. This is a failed general mapping,
not accepted all-group editing. These are menu observations, not independent
measurements of every effect. No Test 3 edited or game-resaved slot accompanied
this report. See the [investigation](boon-key-investigation.md).

The local and CI results below remain valid structural checks. They did not
test the new keys against independent game captures and therefore did not catch
this defect. WD20's isolated acceptance is unaffected.

Date: 2026-11-15. **WD20-01–03 passed**, with four screenshots and two returned
game saves. At the player's request the editor now exposes all 31 Boons / 81
tiers using the common level and activation-key patterns. Broader gameplay
effects remain inferred; this report does not call every group game-tested.

## Weapons Discount 20% evidence

| Case | Result | Evidence |
|---|---|---|
| WD20-01 | Pass | Screenshot shows owned **20% On**, with next offer **Weapons Discount 30% Locked**; initial prices are Wooden Sword **240**, Bronze Sword **400** |
| WD20-02 | Pass | Off prices are **300 / 500**; WD20-off-game retains level 2 and disable marker 1 |
| WD20-03 | Pass | Reloaded On prices return to **240 / 400**; WD20-on-reloaded retains level 2 with the disable marker absent; player confirms the full procedure worked |

The two returned containers pass checksum and object-tree validation. Their
EXP state remains level 1 On; Gold 1,523, Renown 6,640 and Karma 410 match the
accepted baseline. Other parsed flags, Deeds, tutorials, fast travel and
blessings match it. Unit numbers remain 47, 48, 1, 2, 3, 4, 5, 6, 7 in the
same roster order. The repaired gate/shop flags and stables state are preserved.
Relative to the supplied level-2 probe, Off adds only ddb8d06b = 1 in the
parsed flag maps; On has no parsed flag differences.

| Private evidence file | Bytes | SHA-256 |
|---|---:|---|
| WD20-off-game | 49,483 | ae17a646774e4b79ca6a555155b0d0d99f72dee9d2ba778a4c72cf6b01c85473 |
| WD20-on-reloaded | 49,941 | f843407afc7449a4e3ffc76a4f9fed06f7faa5840b760081f5d36ab8199bdd12 |

The experiment changed no progression, so this 20% effect works before the
baseline's normal purchase requirement. The next Locked offer and current
owned bonus are distinct. This does not identify the save's eligibility field
or prove that every Boon ignores every prerequisite.

The reference baseline remains **Auto from B0-01-Unit-Selection-Test-1.zip**,
SHA-256 8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663.
No later capture is silently promoted to baseline. No personal saves,
screenshots or game binaries are committed to GitHub or the editor package.

## General editor behavior

Test 3 adds setting/removing levels, On/Off at the owned tier and Set all to
max. It uses catalogue maxima, preserves currency and progression, requires
selected-save editing, and refuses unknown states before mutation. Bulk max
includes hidden search rows, preserves all activation markers and is one
undo step. Existing Off states therefore remain Off until explicitly enabled.
Flags is now last in the tab order.

Level names use 因果報酬_レベル_ plus the catalogue group. The disable prefix's
text is still unknown; its low-32-bit FNV state a21ab2b4 independently
reproduces the captured EXP and Weapons keys. Applying these patterns to the
other 29 groups is an extrapolation. Evidence labels keep this visible.

## Automated and native-interface checks

**All 111 tests passed locally with every private fixture supplied**: 94 public
and 17 opt-in private tests. The private inputs are skipped in public CI.
New checks cover all 81 tiers, all 62 distinct keys, independent switches,
single/bulk removal and maxima, stable request ordering, compact/wide records,
stored-zero and other byte-exact no-ops, atomic refusal, malformed map/header
gating, preservation of unrelated records and normalized outside-map bytes,
current-payload revalidation, and one-step bulk Undo/Redo.

Private checks verify the WD20 return, then serialize and reopen all maxima
from the accepted baseline and both WD20 captures. Output checksums and exact
intended payload plus checksum refresh must match. Existing switches, Karma,
unrelated payload content and source files are preserved.

The real Tk application passed tier/remove/On/Off button checks, exact matching
of a baseline-to-20% edit with the accepted probe, save/reopen in both states,
original and numbered backups, all-group max from a filtered search, bulk
Undo/Redo and save/reopen, mirroring refusal and unchanged Karma. The source
baseline remained byte-identical. Dark 1240×800 and light 1000×640 layouts were
inspected for English controls; Flags was visible at the far right in both.
The container's Japanese/symbol font rendering is not an application-language
acceptance check; private GUI screenshots are not published.

To reproduce the full suite, set FEFW_TEST_SAVE to original B0,
FEFW_WEAPONS_TEST_SAVE to the accepted B0-01 Auto, and FEFW_BOON_CAPTURE_DIR,
FEFW_BEDIT_CAPTURE_DIR, FEFW_WEDIT_CAPTURE_DIR and FEFW_WD20_CAPTURE_DIR
to the corresponding private capture directories. Run:
python -m unittest discover -s tests -v

## Limits

Remaining groups and untested higher tiers are editable but not individually
game-validated. Unknown symbolic disable names, save-side purchase eligibility,
effect stacking, fractional-price rounding and cross-file synchronization remain
unresolved. No progression-unlock, automatic purchase cost or refund is claimed.
Use [the Test 3 guide](testing-boon-levels.md) for the controls and evidence labels.
