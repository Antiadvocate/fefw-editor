# New units — expanded tests 2

**Results received:** see [Test 2 results and Anna retest](unit-expansion-test2-results.md).
The original instructions and profiles below are retained for provenance.

These are ten independent pre-edited saves, each adding ONE unit to the same
old Leda Chapter 9 baseline. Use the existing restoration-fix editor if needed;
there is no new editor build to install and no need to enable restricted rows.
Only the experimental save has the added character. Main has not been merged.

## Install and return

Close the game, keep your original save folder, and install one case's Auto
at a time into a disposable copy. Keep its companion files/other slots. The
00-Control-Leda Auto is byte-for-byte unchanged. Every case deliberately uses
the same free unit number because the cases are separate; do not combine them.
Load the named case before each test, rather than continuing the previous case.

For each case:

1. Check load, roster, portrait/model, class, HP, inventory and skills.
2. Save and reload. If saving is unavailable at arrival, continue to the next
   opportunity; do not count that alone as a failure.
3. Deploy the added character with Leda and an original party member. Select,
   move/cancel, then act/attack. Check ownership and animations. Gain EXP/a
   level if practical. For Cai, also verify Leda remains the route protagonist
   and the next story objective progresses normally.
4. Save/reload after combat and repeat selection. Return Auto-after-progress
   under the case folder, or describe precisely where it failed. A load crash,
   missing model, undeployable unit or broken action is useful evidence; skip
   that case and restore the control. Do not spend time repairing it manually.

Suggested order: X1, S1–S4, N1–N3, S5, then N4. Sothis is the least supported
profile and may fail even to load. Deployment, progression and save/reload
should be reported separately; a roster appearance alone is not a full pass.

## Cases and default choices

All units start at level 1 with zero earned stat gains and a fresh unit number.
High ranks on special characters come from their own tables; they are not a
claim about their natural recruitment level. No mounts/battalions are explicitly
created, and no story, support, facility or class-unlock flags are granted.
The normal generator's conditional and forced/scripted skill grants remain
excluded; the game may derive additional character/class effects itself.
For NPCs, recruitment/met flag names are inferred from their exact PID, not
proof of real recruitment events. No flag is added merely to advance a quest.

| Case | Character | Class / HP | Default evidence and guesses |
|---|---|---|---|
| X1-Cai | Cai | No class / 27 | Ordinary catalogue defaults; cross-route protagonist test. |
| S1-Hong-Hua | Hong Hua | Ovate / 26 | Own recovered defaults; special-character source flags. |
| S2-Troy | Troy | War Monk / 30 | Own recovered defaults; special-character source flags. |
| S3-Anna | Anna | Elephant Rider / 22 | Own class/HP/ranks; guessed Bronze Spear loadout. No explicit mount. |
| S4-Centurio | Centurio | Dreadnought / 27 | Own recovered defaults; different special-character source flags. |
| N1-Castor | Castor | Guardian / 25 | Own Guardian/25 HP/ranks/items; serial zero, excluded by current filter. |
| N2-Long | Long | Pugilist / 24 | Own Pugilist/24 HP/ranks/items; serial zero, excluded by current filter. |
| N3-Vandahl | Vandahl | Pugilist / 26 | Pugilist selected from his class progression; own 26 HP/ranks, guessed Bronze Gauntlets loadout. |
| S5-Mars | Mars | The Blade / 30 | The Blade selected from his class progression; own 30 HP/ranks, guessed Bronze Sword loadout. |
| N4-Sothis | Sothis | Shaman / 25 | Placeholder-like base row: guessed Shaman, 25 HP, first black-magic/infantry ranks and Fire. |

## What this establishes

A pass establishes this profile on this baseline, not all routes or later
natural recruitment. In particular, Cai's story identity may still affect a
later scripted event. Sothis's guessed class/stats are a playability experiment,
not recovered canonical defaults. The production Add unit list stays unchanged
until results establish which entries should be exposed and how to label them.

See [the catalogue audit](unit-catalogue-coverage.md) for the full enabled/restricted list and omitted base
identities. catalogue-audit.json and all-person-records.csv preserve the audit;
test-saves/manifest.json records exact profiles, hashes and validation evidence.
