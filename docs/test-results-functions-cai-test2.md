# Functions / Cai Test 2 — results

Reported 2026-11-16. All four returned Autos validate their container and
payload checksums and remain Cai Part 1 Chapter 4.

| Case | Player result | Save evidence |
|---|---|---|
| C2-04A: Journal | Journal accessible; quest agrees with HUD; progression blocked | Five section flags remain 1; journal-wide block absent |
| C2-04B: Journal + Training/Practice | Same result | Journal, Training and Practice choices retained |
| C2-04C: Journal + first-free-time prerequisite | Same result | Journal choices and first-free-time flag retained |
| C2-04D: C + upper/lower area access | Same result | Journal, prerequisite and both area flags retained |
| FUN-UI01–04 | All passed, user reported | Earlier automated UI checks remain recorded in Test 2 |
| C2-09T / C2-09P | Not performed; deferred by user | No Arena isolation evidence added |

Every return stores clock **1449-03-01 15:00**, context `12 05`, and live story
sequence **`d63bb68c219adbe2`**, matching the blocked source. The three unit
numbers remain **4, 6 and 7**. Every exposed Functions switch matches its
prepared case; the game did not remove those candidate permissions.

The Journal/quest-list combination has a reported game pass. The five section
flags were enabled together, and the blocking flag was already absent, so this
does not isolate each section or establish the effect of removing a live block.
Individual controls retain their existing evidence labels. None of these
combinations resolves the Chapter 4 objective; no Arena dependency is proven.

The next test follows the user's proposal: prepare Chapter 3 from the successful
Chapter 2 advancement, then play naturally into Chapter 4. A newly captured
Chapter 4 arrival/checkpoint can provide progression and scene state missing
from the direct skip. This remains a hypothesis until compared with returns.
See [Cai Test 3](testing-story-cai-test3.md). No additional Arena play is needed.

Optional checks use `FEFW_CAI2_RETURN_DIR` and `FEFW_CAI2_SENT_DIR`. Private saves
are retained outside Git and original inputs are not changed.
