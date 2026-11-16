# Cai Test 1 — results and access investigation

Reported 2026-11-16; all five returned files pass container and payload checksums.

| Test | Result | Scope |
|---|---|---|
| Chapter 2 | Pass | Opening battle works, then completes into free time |
| Chapter 4 | Blocked | Opening runs; objective and Adventure Journal inaccessible |
| Chapter 9 | Pass | Opening task and subsequent progression work; multiple facilities, including Arena, become available |
| CUI-01–04 | Pass, user reported | Route-specific controls, staging/history, checkpoint naming, Save and overwrite/backup behavior |

The Chapter 2 return protocol uses the first capture at the opening battle;
advancement is after that battle into free time. No later free-time story beat
was required for this round. Cai Chapters **2 and 9** are labelled Game-tested
for this short-session scope; Chapter 4 stays Inferred with an explicit blocked
progression note. No Cai Obelisk acceptance or full-campaign coverage is claimed.

| Capture | Clock | Live sequence | Context |
|---|---|---|---|
| Chapter 2 opening | 1449-01-29 12:00 | `782e790823b2c9a1` | `12 02`, battle |
| Chapter 2 advancement | 1449-02-03 12:00 | `d642b68c21a0fab0` | `12 05` |
| Chapter 4 blocked | 1449-03-01 15:00 | `d63bb68c219adbe2` | `12 05` |
| Chapter 9 opening | 1449-09-03 15:00 | `d631b68c2192877f` | `12 05` |
| Chapter 9 advancement | 1449-09-11 13:00 | `d631b68c2192877a` | `12 05` |

Header/GameUserData route, part, chapter and sequence agree; all remain Cai
Part 1. Battle inspection uses the supported header/flag structures without
assuming free-time unit gear offsets. Story editing continues to refuse battle
sources. Original inputs and the accepted Leda baseline remain unchanged.

## Chapter 4 observations

The return lacks all five Adventure Journal section unlocks. Its journal-wide
blocking flag is absent, so merely clearing that block is a no-op. The quest-list
unlock occurs earlier in Cai's timeline (`0x34b8`); the other four section
unlocks occur during Chapter 3. They are independent of tutorial-seen flags.

The first Chapter 4 hub objective targets Gabriel; the subsequent objectives
target Castor and Bertrand. The data includes a Chapter 4 event in the arena
underground area (A50). This does not establish that the Arena spectating
service or Training is a prerequisite for reaching that objective.

The user also tried enabling all previously exposed switches without success.
Those edits are not present in the returned Chapter 4 Auto, so that experiment
is recorded from the report rather than inferred from this capture.

## What changed during Chapter 9

The game added Training, Practice, both Dagsion area-access switches, the
first-free-time progression flag and numerous service unlocks between the two
captures. Journal section unlocks remain absent in both. Multiple changes
occurred together; Arena availability cannot be assigned to a single flag from
this comparison.

Primary data defines `Arena` and `Training` as separate facility operations.
The normal arena receptionist checks `Arena` access. Both schedules are closed
00:00–06:00; this does not explain the Chapter 4 return at 15:00. The recovered
Training flag is `機能開放_訓練所`; no independent Arena saved flag has been
established. `機能開放_稽古` (Practice) is a separate Cai Chapter 4 permission,
but its precise UI action and any Arena relationship remain unconfirmed.

`Chapter.bin` grants Cai's Practice/lower-area flags at Chapter 4 free time and
Training/upper-area flags at Chapter 5 free time. An early Chapter 4 objective
therefore must not be declared dependent on Training solely because it is
under the arena. [Test 2](testing-functions-cai-test2.md) isolates the candidate
prerequisites without changing the live story beat or date.

Optional private regressions use `FEFW_CAI1_RETURN_DIR`. No captures or game
data are committed to Git.
