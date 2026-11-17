# Boons Test 2: existing Weapons Discount 10% on/off

**Accepted on 2026-11-15: WEDIT-01–07 all passed by player report.** Four
returned saves verify Off/On editing and persistence. Prices matched the
earlier screenshots by report; no new screenshots were taken. Backups reached
`.bak4`. See the [results and evidence limits](test-results-weapon-boon-2026-11-15.md).
No additional screenshots or repeat test round is required for this acceptance.

The procedure below is retained for reproduction. The earlier in-game Off/On
mapping and 10% listed-price comparison are complete. EXP editing is accepted;
do not repeat its battle test or the completed personal-save repairs.

## Setup

Extract **FEFW-Boons-Test-2.zip** into a fresh folder and launch that folder's
`editor.py` using the working Python environment. The header should show
**v1.3.9 · Boons Test 2**. No new dependencies are required.

Use a disposable copy of **Auto supplied in B0-01-Unit-Selection-Test-1.zip**,
the player's accepted baseline. Do not substitute the later Auto(2) test return.
Its SHA-256 is `8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663`.
On this baseline: Weapons Discount 10% On, Increased Exp 10% On, Karma 410,
Gold 1,523 and Renown 6,640. The Armorer is accessible. The editor ZIP does not
contain the private baseline.

Back up the save folder, close the game before editor saves, and turn off
**Also edit this route's other saves**. Open the actual slot the game will load.
Keep the accepted baseline unchanged. Select **Weapons Discount, tier 1**;
do not purchase the displayed next tier in game.

## Tests

| ID | Action | Expected result / evidence |
|---|---|---|
| **WEDIT-01 — Display and scope** | Open Boons, search `Weapons Discount`, select tier 1, then inspect tiers 2/3 and an unrelated Boon. | Tier 1 is On; Turn off enabled, Turn on disabled; Karma 410. Higher tiers/unrelated Boons have no enabled edit buttons. Increased Exp remains editable. |
| **WEDIT-02 — Editor Off** | Select Weapons Discount tier 1, Turn off, Save. Copy that edited slot as **WE02-off-edited** before launching the game. Load it, inspect the Boon and Armorer, then save/quit/reload and inspect again. Copy the final slot as **WE02-off-game**. | Owned 10% Boon is Off and stays Off. Wooden Sword costs **300** (or compare the same weapon from the earlier price table). Karma remains 410; no Boon/weapon purchase. Return an Off/menu-price screenshot. |
| **WEDIT-03 — Editor On** | Starting from WE02-off-game, close the game, reopen the slot in the editor, Turn on and Save. Copy as **WE03-on-edited**. Load, inspect Boon/price, save/quit/reload and copy as **WE03-on-game**. | On persists. Wooden Sword costs **270**; Karma stays 410. Return an On/menu-price screenshot. |
| **WEDIT-04 — Undo, redo and mirroring** | On a disposable editor copy, turn the weapon Boon Off, undo, redo, then undo back to On. Enable route mirroring and attempt Off. | States and buttons follow Off/On/Off/On. Mirrored action is refused without an edit. Turn mirroring off afterward. No game run required. |
| **WEDIT-05 — Independent EXP control** | In memory, switch EXP Off. Switch Weapons Discount Off and On while checking EXP. Undo all these changes afterward. | EXP stays Off during weapon edits; weapon state changes independently. Restore both to On. No EXP battle test needed. |
| **WEDIT-06 — Numbered backups** | Inspect backups created by WEDIT-02/03. In a fresh test folder the first editor save creates Auto.bak; the next changed pre-save disk state creates Auto.bak1. | Original .bak is retained; later backups get increasing numbers. Existing backups are not overwritten or renamed. A state identical to the newest backup may be skipped. With existing numbered backups, expect the next highest number instead. |
| **WEDIT-07 — Brief regression check** | Reopen the final saved slot in the editor and check Boons, the nine-unit roster, currency, Deeds and travel menus. | No unexpected state changes. No repeat of the full B0 battle/gate suites is requested. |

The original requested return was the seven results, **four actual slot files**
named above, and Off/On price screenshots. The accepted return supplies all
four files and reported passes, using the earlier price screenshots as the
visual reference. Its final On capture is named **W03-on-game** (without the E).
For future reproduction, distinguish the editor's output from the game's save
and report any blocked check explicitly; do not infer gameplay from checksums.

```text
WEDIT-01:
WEDIT-02: Off after load/reload; weapon and price; Karma:
WEDIT-03: On after load/reload; weapon and price; Karma:
WEDIT-04:
WEDIT-05:
WEDIT-06: backup filenames observed:
WEDIT-07:
Additional gameplay/actions or changes from the baseline:
```

## Upstream changes included

Merged `Antiadvocate/fefw-editor` main at
`7157e6c771bf19bbe49b53f36e2c936d33f403b0` (v1.3.9): numbered backups and the
preceding weapon-mastery multi-selection fix. Automated checks cover backing
up intervening on-disk saves, duplicate suppression, numbering gaps, old .bak
preservation, backup failures and selected-row mastery edits.
