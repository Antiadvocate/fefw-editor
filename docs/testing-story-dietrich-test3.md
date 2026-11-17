# Dietrich Story Test 3

Test 2 accepted Chapters 5, 6 and 7 with their A fixes. Chapter 7 also passed
teaching Esmerelda and its following story checkpoint. Chapter 2's native C
control passed; its replay repairs A/B failed.

## Test order

Use each case independently, with the game closed when replacing Auto. Keep
working saves separate from these disposable cases.

1. **D3-02A-Event-candidate:** Resume the blocked village save. Step away from
   Esmerelda and approach her again. Check whether the scene triggers and the
   objective advances. If it passes, skip 02B and 02C.
2. **D3-02B-Event-and-history:** Only if 02A fails. Repeat the same approach test.
   If it passes, skip 02C.
3. **D3-02C-Event-time-fallback:** Only if both earlier cases fail. Repeat the same
   test. This is a diagnostic, not an established Chapter 2 fix.
4. **D3-05-Direct-entry:** Start the chapter, train at the arena, then test the
   certification objective. This checks the fix when applied at chapter entry.
5. **D3-06-Direct-entry:** Start the chapter, follow the Trading Company marker,
   and check the port doors and next story step. No manual edits or fast travel
   should be needed for this walking-access test.

Save `Auto` on arrival and `Auto-after-progress` after the next meaningful
story step, where saving is available. Return those files with pass/fail notes.
If blocked, the blocked Auto and a short description are sufficient. No repeat
of Chapter 7, other accepted chapters, tutorial names or the full UI checklist
is needed. All UI checks from Test 1 remain accepted.

## What changes

| Case | Changes beyond its source |
|---|---|
| 02A | Remove only unnamed `06c136c7:be852456` (value 1) |
| 02B | 02A plus remove rescue dialogue history `b631f2c1:81e4a23a` |
| 02C | 02B plus remove unnamed `06c136c7:370344f7` (value 80202012) |
| 05 | Ordinary chapter entry plus upper movement-restriction removal |
| 06 | Ordinary chapter entry plus lower movement-restriction removal and three function switches: upper/lower Dagsion access and Vandahl Trading Company |

The Chapter 2 keys appeared in the successful native rescue return. Their
meanings are **unconfirmed**, so they are never changed by ordinary chapter
selection. All three diagnostics keep the current objective, party, tutorial
list and HubData. Esmerelda is neither removed nor given a new class.

Chapter 6 preserves the intentional upper movement restriction and does not
add a Shopping Street fast-travel destination. Test 2's successful 06A retained
that travel flag from the player's manual edits, so Test 3 checks walking access
from the original source without it.

The packaged editor incorporates the Chapter 5–7 prerequisites and reports
Chapter 2 as blocked. Chapters 5/6 are labelled repair-passed, integrated-entry
pending. Chapter 7 matches the accepted 07A export byte-for-byte.

## Reproduce and verify

Use `research/dietrich_test3_kit.py RETURNS1 RETURNS2 TEST1 OUTPUT` with the exact
private Test 1 returns, Test 2 returns and delivered Test 1 kit. Inputs are
fingerprinted; output must be fresh. Exports verify checksums, summary mirrors,
reopen equality, exact flag deltas, unchanged source files, and byte-identical
party records. The manifest identifies each source and output by SHA-256.

Private saves, screenshots and game binaries must not be committed to Git.
