# Theodora Test 1 results — 17 November 2026

The player reports all chapter checks passed except the access blocks below,
and **all UI checks passed**. All 19 supplied saves validate container checksums,
live Header/GameUserData route/part/chapter/sequence and outer-summary/clock
mirrors. Unsupported event/battle resume contexts remain read-only for story
editing; they are valid game saves.

| Chapters | Reported result | Returned evidence |
| --- | --- | --- |
| 1, 3, 5, 7, 10–12 | Opening and next story event/battle passed | Arrival/progression pairs, with later sequence IDs |
| 2 | Opening leads straight into battle; accepted | One battle save, mode `12 02`; no second save required |
| 4 | Cannot pass the upper-city gate to the arena | Free-time arrival; middle movement restriction remains set |
| 6 | NPCs block the path to the Trading Company objective | Free-time arrival and screenshot; middle/lower/district restrictions remain set |
| 8 | Same NPC barrier | Free-time arrival; same three restrictions remain set |
| 9 | Cannot move from Troy's Shrine toward the objective | Event/map save, mode `12 04`; screenshot shows Fezzan Gate as the next location |

Chapter 1's existing-party replay passed. Do not carry the unresolved Dietrich
Chapter 2 failure over to Theodora. No native-control tests were reported in
this round. Obelisk use and full-campaign progression remain untested.

The returned ZIP SHA-256 is
`c5359e14148b94955b94cda34991d437a592f768a7d47fb0a8e0e391a812f0c2`.
Private files and screenshots are not in Git. The test kit contains the full
return-validation report; the repair builder fingerprints its four inputs.

## City access evidence

In `Timeline_Part1_Seo.bin` (SHA-256
`964da5cf80e6b5385c9bb8c21e706b201b1f6154aa62c26b600970dd852a6741`),
Chapter 3 adds lower, district and middle movement restrictions at `0x28e8`,
`0x29c0`, `0x2a98`. The timeline clears middle at `0x38f0` before Chapter 4,
district at `0x3d28` during Chapter 4, and lower at `0x6248` during Chapter 5.
Later middle/lower restrictions are cleared again before Chapter 7 at
`0x8408`/`0x84e0`. Direct entry from the Chapter 3 Auto skips those earlier
clear operations.

Typed `HubDispos/Hub_000.bin` rows establish:

- `0x2fdef0`, upper-to-middle entrance: requires the middle movement restriction
  to be absent, with additional chapter-specific restrictions.
- `0x2fe0e0`, middle-to-lower entrance: checks the lower movement restriction.
- `0x5450`–`0x5ae0`, soldiers/merchants around the district passage: check
  district restriction OR `富裕区と商業区の通路木箱表示` (crate display).
- `0x2fe3c8`, invisible wall: checks district restriction and chapter-specific
  alternatives. The separate crate and relevant chapter-specific flags have
  no stored record in the blocked 6/8 returns.

The Chapter 4 probe clears only middle. The Chapter 6/8 probes clear the three
earlier movement restrictions. Chapter 8 already has the three relevant general
function unlocks; Chapter 6 does not. A conditional Chapter 6 fallback adds
those unlocks only if the primary walking-access test still lacks service access.
These repairs remain unaccepted until tested in game.

## World-map evidence and limits

Troy's Shrine, Junction 374 and Wandering Wood retain state **2**, secondary
**3**, visited **1** from the original source. Chapter 8 normally executes
`スポットオン(迷いの森-トロイアの祠)` at timeline `0xa418`; direct Chapter 9 entry skips
that row. The first probe sets only these three state bytes to **3 (Shown)**.
State 2's general meaning remains unresolved; this is a bounded repair candidate.

The road graph also has 32 hidden points along the shortest connected route
from that exit to Fezzan Gate. A conditional second probe shows that 37-node
path (35 state bytes change in total). It is a visibility diagnostic, not a
reconstruction of the exact natural campaign map. Both probes preserve visits,
secondary bytes, record tails, gate/dungeon/story flags, clock, objective and
party. No gate completion, dungeon clearance or objective bypass is granted.
Later encounters or access conditions may still require normal progression.
