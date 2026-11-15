# Test 3 bulk-unlock failure: key-length investigation

Date: 2026-11-15. Status: **game failure confirmed; exact replacement keys
not yet established**. No corrected build or accepted bulk unlock is claimed.

## Independent evidence

The player supplied two game screenshots after using Set all to max. They
show a consistent split, even though the editor reads all written values back
as maximum. The catalogue group names exactly match the supplied Reward.bin
strings; the first check found no transcription error.

| Screenshot observation | Groups | Generated level-key UTF-8 length |
|---|---|---|
| Received / maximum shown | EXP 50%; Sword, Spear, Axe, Bow +3; Weapons, Items, Gifts discounts 30% | 32, 35 or 38 bytes |
| First tier still offered for 300 / status +0 | Brawling, Black-Magic, White-Magic, Infantry, Rider, Heavy, Flier, Authority EXP | 41 or 44 bytes |

These observations confirm menu state, not every gameplay effect. Other groups
are outside the two screenshots. No Test 3 edited or game-resaved slot was
attached, so actual post-load stored records cannot yet be compared.

## Hypothesis, not a patch

The known prefix is 23 UTF-8 bytes. Every failed displayed group produces a
longer key than every displayed success. A fixed-size buffer or name-length
limit in the game's dynamic key construction is therefore a useful hypothesis.
The cutoff, handling of partial UTF-8 characters, and whether activation keys
use the same rule remain unknown. A 39- or 40-byte limit is not yet proven.

For Brawling, the present full key hashes to ad9326cb. Hashing the first 39
bytes would give acca4eb2; the first 40 bytes would give 9bc3b8e1. These are
diagnostic candidates only and must not be shipped as verified fixes. The six
blessing-cost group keys are also long (45–51 bytes), but their failure was not
shown and should not be stated as an observed result.

The synthetic tests checked the same inferred key derivation on both sides of
a write/read round trip. They establish serialization and preservation, not
that the game's lookup uses that derivation. The next regression fixture must
use an independently captured game key for a failed long-name group.

## Minimal controlled capture

Use a disposable copy of the current Test 3 game state. Keep the accepted
baseline separately. Close the game before copying each slot, make no other
purchases or progress changes, and return:

1. **BK-before**: save in game before buying any of the missing Boons.
2. **BK-purchased-on**: buy **Increased Brawling Exp +1** in game for 300 Karma,
   confirm its active state, then save and quit.
3. **BK-off**: reload, turn that same Brawling Boon Off in game, save and quit.

No screenshots or repeat battle tests are needed for this comparison. The
first pair isolates the game-written level key and purchase accounting; the
second isolates the activation key. The existing incorrect Test 3 records,
if retained, also help identify a narrowly scoped migration for affected saves.
Do not rerun bulk max between these captures.

## Correction gate

Compare all maps and resource changes in the returned captures. Establish the
actual level and disable identities independently, then test any inferred
length rule against both and the existing short-name captures. Apply any
format rule only to the relevant Boon key construction; do not truncate the
editor's general identifier hash function. Preserve unknown records and avoid
silently interpreting stale Test 3 values as recognized game ownership.

The accepted EXP and Weapons Discount tests remain accepted. Test 3's general
bulk acceptance is failed until this mapping defect is resolved and checked
against the game.
