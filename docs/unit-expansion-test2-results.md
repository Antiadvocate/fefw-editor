# Expanded unit tests 2 — results, 17 November 2026

| Case | User-reported result | Qualification |
|---|---|---|
| X1 Cai | Pass, including a battle against enemy Cai | Cross-route same-character enemy encounter works in this case |
| S1 Hong Hua | Pass | Tested Leda Chapter 9 profile |
| S2 Troy | Pass | Tested Leda Chapter 9 profile |
| S3 Anna | Cannot deploy as Elephant Rider | Retest pending; do not enable this default yet |
| S4 Centurio | Pass | Tested Leda Chapter 9 profile |
| S5 Mars | Pass | Tested chosen class/profile, not a natural recruitment event |
| N1 Castor | Pass after switching to Chosen Lance | Supplied Halberd is not usable with his starting ranks |
| N2 Long | Pass | Tested Leda Chapter 9 profile |
| N3 Vandahl | Pass | Tested chosen class/profile |
| N4 Sothis | Deployed, but arrived without usable weapons | After giving Chosen Sword, Breidablik and Royal Sword appeared too; inventory behavior unresolved |

All 19 returned containers validate. All ten input Auto files match the supplied
kit exactly. Nine after-progress returns are battle-context 1202 saves; each
contains one exact target PID in the live pool. No Anna after-progress return
was supplied. The guarded free-time equipment/identity writer is not used on
the battle returns. These files corroborate presence and item-list changes;
control, action and other game checks are accepted from the user's report.

Castor's return contains Chosen Lance and Halberd. His source ranks include
lance rank 3 and no axe rank; the Halberd specifies lance and axe requirements
of 3. This explains the loadout mismatch. Use the user's tested Chosen Lance
for a future playable profile, or separately validate a basic lance. Do not
raise his ranks just to make the old weapon fit.

Sothis's input contains Fire; the return contains Chosen Sword, Breidablik and
Royal Sword, and no Fire. Her decoded mastery list is now empty. Her source
Person row has no starting class, growth list or unique-item grants. The
returned inventory change is real, but its trigger cannot be isolated from
these two endpoints. Do not label this profile a fully validated recruit or
automatically grant those extra weapons. Further investigation would need a
save immediately before and after the single inventory operation.

## Anna: class/deployment diagnosis and retest

The initial screenshot shows 8/9 deployment capacity used, Anna greyed out,
and no weapon equipped. The follow-up screenshot shows **2/9** after the user
removed all optional units, and Anna still cannot deploy. Insufficient remaining
capacity is ruled out for this failure. Blank attack/hit values alone do not
explain deployment.

| Class | Job deployment field | Job footprint field |
|---|---:|---:|
| Elephant Rider | 2 | 2 |
| Dismounted Elephant Rider | 2 | 1 |
| Soldier | 1 | 1 |

The deployment field is also 2 on many ordinary mounted and dismounted classes;
its meaning has not been decoded, so it is **not proven to be a two-slot cost**.
The elephant's larger footprint, map restrictions and class initialization
remain plausible causes. Anna's Person table explicitly
lists her mounted and dismounted classes. Its default-mount field is empty;
the Elephant Rider Job supplies a default elephant and class-exclusive attacks.
No claim is made that adding a mount record would fix this.

A0 is the unchanged original S3 save for comparison. Its capacity retest has
already failed at 2/9; do not ask the user to repeat it.

A1 uses Anna's own dismounted class. A2 uses Soldier to test
an ordinary single-tile infantry class. These saves change only Anna's current
class and registered-class list. Her identity, unit number, level, stats,
inventory, skills, recruitment flags and every other character are preserved.
Reversing those two edits restores the complete original payload exactly.

Anna remains restricted while testing. If A1/A2 works, adopt a clearly described
playable default after confirmation. If these reasonable approaches fail and
no supported fix emerges, remove her from the Add unit list as the user asked;
retain duplicate recognition for any existing Anna record. No main merge yet.
