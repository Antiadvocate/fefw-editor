# New units Test 1 returns and recruitment restoration fix

## Reported game results, 17 November 2026

| Case | Accepted scope | Still untested |
|---|---|---|
| U1 | User reports pass for Buccar, Sirocco and Catania, then Olympia deployed separately in the same save | Broader deployment combinations |
| U2 | User reports pass for Guzran | Later natural recruitment interactions |
| U3 | User reports pass for renumbered Sirocco and, as a substitute for Buccar, Catania retaining player control after renumbering in that chapter | Buccar himself was not retested because he leaves for story reasons |
| Editor | All requested checks passed, including the corrected R0/R1 restoration retest | No remaining check in this focused editor test set |

All six returned containers have valid checksums. The three input Auto files
match the supplied kit exactly. U1's return is a battle save containing Buccar
and Sirocco at level 3, with gained stats; the user reports a prior sewer dungeon.
Catania is present at level 1; Olympia is absent from that deployed roster.
U2 is free-time and retains Guzran at number 49 with a carried weapon. U3 is a
battle save containing Sirocco and no Buccar, consistent with the reported
story departure. The battle gear/number layout is outside the current identity
reader, so those two returns do not independently verify the stored number.
The user-reported behavior and the decoded save evidence are recorded separately.

In a follow-up on 17 November 2026, the user confirmed Olympia passes when
deployed separately in that save, and Catania retains player control after her
number is changed in the same chapter. Catania is accepted as the substitute
for Buccar's renumbering case. These are user-reported passes without new return
files; the original capture facts above remain unchanged. Together with the
editor retest below, this completes the planned functional checks.

No returned file contains Benditz. None is identified as the disposable Flags
test save, so this does not establish whether that particular editor test had
an existing Benditz record.

## Why the screenshot was misleading

| Exact Reads As | Meaning for this feature | Corrected Name |
|---|---|---|
| `加入_ベンディッツ` | Main recovered recruitment flag used by Add/Restore | Recruited: Benditz |
| `加入_SC11_06_ベンディッツ` | A different scenario record | Recruited: Benditz (alternate record) |
| `加入_Venditz` | Older English-key alias, not a recovered Person identity | Recruited: Benditz (unverified alias) |

The screenshot shows the last two keys. The actual primary key previously
retained its Japanese label, so searching for Benditz omitted it. The shared
label overlay now translates all catalogue primary recruitment/met keys and
distinguishes known alternate records and unverified legacy aliases. All
52,013 existing flag hashes/keys remain unchanged; 853 labels are corrected.
Unverified aliases are not promoted into canonical unit identities.

Restore requires an existing, supported unit record and its main recruitment
flag at zero/absent. Zero flags alone do not create such a record. The Add unit
preview now names its exact recruitment key and explicitly says when no record
exists to restore.

## Separate Flags value-edit defect

Reproducing the requested UI path found that Set value replaced the entire
containing list with one flag's bytes. Existing unit-restoration tests had
constructed the zero flag directly and therefore missed this UI defect.
The supplied screenshot does not by itself establish that this happened to the
user's disposable save.

The corrected writer updates only the selected value. When an integer needs
the wide encoding, it preserves the whole list, header, order, neighbors and
padding while expanding that one field. Values no longer wrap modulo 256.
Missing/duplicate flags, stale list selection and invalid integers are refused.
No-ops do not create history. Set value now has Undo/Redo and requires route
mirroring to be off so its history covers the whole edit.

Regression tests exercise the real Flags method followed by Restore, preserving
every other flag and the entire unit record. They also cover alternate keys,
zero flags with no unit, wide promotion/reduction, English search/Reads As,
invalid inputs, no-ops and Undo/Redo. Use this corrected build for further
manual flag-value edits.

Validation: 278 tests, 223 passed and 55 unavailable historical-fixture skips.
The private R0/R1 pair differs by exactly the one recruitment value in its
decoded payload. Both saved containers validate, and the actual Flags controller
plus Restore/Undo/Redo returns the complete payload to its original state.

## Focused editor retest

**Passed:** on 17 November 2026 the user confirmed "Both checks pass" for R1
and R0 below. This accepts the corrected restoration and Flags value-edit
workflow, including the requested Undo/Redo and Save/reopen checks. No new
returned files accompanied this confirmation; it is user-reported acceptance.
The later Olympia and Catania game checks are recorded above.

The correction package includes `R0-Benditz-Recruited/Auto` and
`R1-Restore-Benditz/Auto`, based on the returned U2 free-time save. They contain
the same added Benditz record, number 50. Only the main recruitment flag differs
(1 in R0, 0 in R1). This is an editor check; no game load/battle is required.

1. Open R1 with route mirroring off. Add unit → Benditz should offer **Restore
   recruitment**. Restore it, Undo, Redo, Save and reopen. The existing number,
   level, stats and inventory must be preserved; there must still be one Benditz.
2. In R0, search Flags for Benditz and choose the row whose Reads As is exactly
   `加入_ベンディッツ`. Set it to 0. The rest of the flag list must remain visible.
   Add unit should now offer Restore; check Undo/Redo for the flag change too.

The planned functional checks are complete, with Catania covering the remaining
renumbering case in place of Buccar. No repeat of the accepted checks is needed.
This does not establish Buccar's own renumbered deployment, later natural
recruitment or every catalogue/route combination; those are outside this
completed test set.
