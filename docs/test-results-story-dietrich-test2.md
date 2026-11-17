# Dietrich Test 2 results — 17 November 2026

The player reports every A case passed except Chapter 2. Chapter 2 passed only
with C, the unchanged native checkpoint. Chapter 7's arrival was saved **after
teaching Esmerelda**, then the next story checkpoint was tested and passed.

| Case | Result | Scope established |
|---|---|---|
| 02A | Failed | Removing rescue dialogue history alone is insufficient |
| 02B | Failed | Adding the two HubData-list resets is also insufficient |
| 02C | Passed | Native Chapter 2 works; this does not fix an advanced save replay |
| 05A | Passed | Removing the upper movement restriction allows certification after training |
| 06A | Passed | Removing the lower restriction allows port/Trading Company progress with the player's three function unlocks and existing Shopping Street travel flag |
| 07A | Passed | One secret permission permits teaching Esmerelda; the following story checkpoint also passes |

05B, 06B and 07B were not needed/reported. Do not treat them as additional
passes. In particular, 06A does **not** show that its existing function unlocks
were unnecessary. No extra recruit or Soldier class change was needed for 07A.

Together with Test 1, Chapters **1 and 3–12** passed the reported short-session
checks. All Test 1 UI checks retain acceptance. Chapter 2 replay remains blocked;
Chapter 1's transition can still encounter that block. Obelisk use and full-route
progression remain untested.

## Returned-save evidence

The ten actual files in `testing-story-dietrich-test2-test-saves-return.zip`
pass container/payload checksum and Header/GameUserData/outer-summary checks.
The 02C arrival is byte-identical to the original native Chapter 2 checkpoint.
Its progression save has the rescue history record and reaches sequence
`e2e7a46c9f3deb7d`; the failed replay remains `e2e7a46c9f3deb7e`.

05A advances from `e2d6a46c9f2f782e` to `424543f0f58e7cd9` (event mode 12 04).
06A advances from `e2d9646c9f314102` to `423b03f0f585bb94` (event mode 12 04).
07A's post-teaching arrival is `e2dd646c9f352a38`, May 30 at 12:00; Esmerelda's
learned/all and arts-known lists contain `SID_秘伝・不動貫槍` / `6b28dad1`
(Hidden Windpierce). The progression return reaches `f265bd1ec355eaf6`, June 15
at 13:00, battle mode 12 02. These event/battle contexts are valid saves but
remain read-only for story editing; they are not corruption.

## Automatic chapter preparation

Exact chapter targets now apply these bounded prerequisites:

| Target | Store | Change |
|---|---|---|
| 5 | Progression `4ad575a2` | Remove `行動範囲制限_上層` / `89dc5a51` |
| 6 | Progression `4ad575a2` | Remove `行動範囲制限_下層` / `8386d712`; preserve the upper restriction |
| 6 | General `972fa7ee` | Enable `機能開放_ダグシオン上層` / `948de8dd`, `機能開放_ダグシオン下層` / `9402533e`, `機能開放_ヴァンダル商会` / `a78e9de8` |
| 7 | Progression `4ad575a2` | Enable `使用許可_秘伝・風切投槍` / `d2cbe499` |

Party, classes, items, tutorials, dialogue history and other flags are preserved.
These are exact targets, not blanket unlocks for later chapters. Unknown target
encodings, duplicate keys and ambiguous/missing stores are refused atomically.
Native early checkpoints use the already-established flag-group structure.

The Chapter 7 export from the original Chapter 4 source is **byte-identical**
to accepted 07A. Chapters 5/6 had repairs applied after their opening, so the
integrated chapter-start paths still need the focused Test 3 checks. Chapter 6
preparation does not add Shopping Street fast travel; walking to the objective
is what the regression checks. No automatic Chapter 2 repair is applied.

## Chapter 2: next evidence-led probes

Compared with its native checkpoint, the successful rescue return adds two
records to sibling store `06c136c7`: `be852456 = 1` (narrow) and
`370344f7 = 80202012` (wide). Both are already present in the failed replay.
Their original names and exact runtime meanings remain unrecovered. The
association makes them useful diagnostic candidates; it does not prove which
record suppresses the proximity event or that either causes the block.

[Test 3](testing-story-dietrich-test3.md) clears the boolean alone, then combines
it with rescue dialogue-history removal, then conditionally also removes that
single timestamp. Each probe resumes the same blocked objective and preserves
UnitPool and HubData byte-for-byte. No roster or recruitment edit is made.
The failed Test 2 history/cache resets remain historical diagnostics only.
