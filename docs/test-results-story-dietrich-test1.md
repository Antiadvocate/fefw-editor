# Dietrich Test 1 results — 17 November 2026

The player reports all UI checks passed. Chapter outcomes are scoped to the
opening and the tested progression step, not completion of the whole campaign.

| Chapters | Result |
| --- | --- |
| 1 | Battle and transition to Chapter 2 passed. No after-progress capture. Rewinding the Chapter 4 save to Chapter 1 also worked, then encountered the separate Chapter 2 rescue block. |
| 2 | Opening works; approaching bound Esmerelda does not trigger the rescue event. |
| 3, 4 | Opening and progression passed, with arrival/progression captures. |
| 5 | Arena training passed; the following certification objective has no working proctor marker. Enabling exams and upper-area access alone did not fix it. |
| 6 | Trading Company objective initially lacked a marker. Enabling both area functions and the company made it appear, but the doors remained blocked. |
| 7 | Reached Teach Secrets; selections unavailable. No opportunity to save, so no return. |
| 8–12 | Opening and progression passed, with arrival/progression captures. |

All **20 returned files** independently pass container/payload checksums.
Header, live GameUserData and outer route/part/chapter/sequence summaries agree.
Seven successful chapters have paired arrivals and later sequences. Chapter 5
advances from `e2d6a46c9f2f782d` to `e2d6a46c9f2f782e`, supporting the report that
training completed before the exam block. Chapter 6's edited return retains
`e2d9646c9f314102`: the edits did not skip the objective.

Valid battle/event modes (including `12 02`, `12 04`, `12 06`) remain read-only
for story editing. They are not corrupt saves. Chapter 1's return is still a
battle capture; its completed transition is player-reported.

## Investigation, not accepted repairs

### Chapter 2: retained rescue history

`HubDispos/Hub_002.bin`, row `0xe028`, group `イベントDIT_A1_1部2章`, labels
the proximity event `エスメラルダと接触`. It checks the Chapter 2 restriction,
uses `イベント範囲初回のみ` (first-time-only range event), and runs
`MID_EV12_002_m01`. The bound Esmerelda row is not a normal conversation prompt.
The returned save already has `MID_EV12_002_m01` (`81e4a23a`) recorded as 1 in
dialogue-history member `b631f2c1`. The native Chapter 2 checkpoint does not.

This supports a replay-history hypothesis, **not proof** that deleting the
scene's history resets the proximity event. A second, broader probe also clears
two structurally validated HubData state lists, containing 2 and 37 records.
Their exact roles are unrecovered; do not add this reset to production. Both
probes retain Esmerelda and the other units. The untouched native Chapter 2
checkpoint supplies an independent control if neither works.

### Chapters 5 and 6: restrictions are separate from function unlocks

The source Chapter 4 Auto retains these progression-store records (member
`4ad575a2`), each with value 1:

| Exact key | Hash | Data evidence |
| --- | --- | --- |
| `行動範囲制限_上層` | `89dc5a51` | Upper-area movement restriction. The normal Chapter 4 timeline clears it at `0x64d0`. |
| `行動範囲制限_下層` | `8386d712` | Lower-area movement restriction. The Chapter 5 timeline clears it at `0x7688`. |

Skipping these earlier steps preserves their restrictions. The Chapter 5
after-training return still has the upper restriction. The Chapter 6 return,
including the player's edited version, still has the lower restriction.
General-map function unlocks do not remove either record.

In `Hub_000.bin`, the middle-to-lower entrance at `0x2fe0e0` requires the lower
restriction to be absent. Its action is `RunAreaChange_A1(CenterToBottom)`.
This is a concrete port/lower-area gate condition; an independent general
"port access" function has not been established. The Chapter 6 timeline also
intentionally sets the upper restriction (`0xa778`), so the probe keeps it.

The Chapter 5 special proctor row (`0x2afaf0`, `キャラDIT_A1_1部5章`) checks
the active exam stage `拠点_ディートリヒ篇1部5章_行動制限4` and runs
`MID_LGV_1DIT_TG12_109_m01`. It differs from the ordinary `ClassExaminer`
facility row. Test removing the stale upper restriction first; service/area
unlocks are an independent fallback. Runtime access is still untested.

The Chapter 6 player edit adds the three stated general-map function records
and a Shopping Street fast-travel record. The first retry preserves all four.

### Chapter 7: test one secret before adding units

The Test 1 source retains Dietrich, Esmerelda and Fabio, all in the initial
class. Its available arts include Grounder/Bloodletting and Tempest Spear/Brute
Throw, but none of the `使用許可_秘伝…` permission flags are present.
This does **not** establish what the Chapter 7 tutorial added before the
screenshot: there is no return save for that moment.

`Skill.bin` defines `SID_秘伝・不動貫槍` (catalogue label Hidden Windpierce)
with required permission `使用許可_秘伝・風切投槍` (`d2cbe499`), a spear
requirement and a teaching cost of 50 `IID_魔響石` (Magic Echo Shards).
The screenshot shows 50 shards. Grounder and Bloodletting's rows have no
teaching material; ordinary arts should not be equated with these secrets.

The first probe supplies only that one permission. Try Esmerelda as the learner.
The fallback additionally changes her to Soldier, a spear class, at zero class
EXP. It preserves her level, mastery EXP, learned skills, items and identity.
Neither probe recruits a unit or teaches the art directly. Permission and class
eligibility remain hypotheses; a successful menu/progression test is required.

## Next test

[Dietrich Test 2](testing-story-dietrich-test2.md) includes four primary retries,
conditional fallbacks and a native control. Ordinary story editing still
preserves these flags/history/units. No experimental repair is automatic.
All eight probes validate exports, summaries, source immutability, unchanged
roster identities/tutorials and their allowlisted root changes. Game results
remain pending. Private inputs and game binaries are excluded from Git.
