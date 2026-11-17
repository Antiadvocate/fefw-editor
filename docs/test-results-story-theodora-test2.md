# Theodora Test 2 results — 17 November 2026

The player reports the chapter tests passed. The nine returned saves all pass
container checksums and live/outer route, part, chapter, sequence and clock
mirror checks. The four progression pairs have different story sequence IDs.
Event-context returns remain valid saves but are read-only for story edits.

| Case | Reported result | Accepted scope |
| --- | --- | --- |
| 04 | Arena access and progression pass | Clear middle movement restriction only |
| 06A | NPCs remain, but an alternate route is accessible and progression passes | Clear middle/lower/district restrictions together; preserve the NPC caveat |
| 06B | NPCs also remain; no progression return | Extra service unlocks are not needed for the accepted A route |
| 08 | NPC barrier disappears and progression passes | Combined middle/lower/district repair; no isolated district-switch claim |
| 09A | Chapter progression passes | Show Troy's Shrine, Junction 374 and Wandering Wood only |
| 09B | No result or returned save | Broad fallback is not accepted or applied |

Together with Test 1, **Theodora Part 1 Chapters 1–12 are accepted through the
reported short-session checkpoints**. Chapter 2 enters battle directly and
needs no second save. The prior Test 1 UI passes remain accepted. No result has
been separately reported for the new Test 2 Functions UI check.

## NPC barrier interpretation

The Chapter 6 and Chapter 8 arrival saves both have the three movement
restrictions absent. Chapter 6 still displays the people; Chapter 8 does not.
The Chapter 6 A arrival is 1449-03-22 08:00; Chapter 8 is 1449-06-01 12:00:05.
This comparison changes chapter, story phase, date and time together, so it
cannot isolate time gating. The player's suggestion is plausible but unproven.
Other story, NPC, crate-display or schedule conditions may apply. Do not add
clock changes, guessed flags or forced NPC removal based on these results.

## Integrated behavior

Chapter selection now applies the exact accepted repairs for 4/6/8/9, retaining
party, tutorials and unrelated flags/map points. Chapter 6 uses 06A; no 06B
service flags are added. Chapter 9 uses only 09A's three visibility bytes;
visited/secondary bytes and record tails remain unchanged. No gate, dungeon,
encounter or objective is marked complete. Reapplying is idempotent. The
chapter and repair share one Undo/Redo step and serialize together on Save.

Functions → Saved switches → Area access retains all four movement controls.
Middle movement is Unlock tested; lower and district rows retain combined-test
coverage and explicitly describe the Chapter 6 alternate route and Chapter 8
barrier removal. Enable removes the restriction; Disable restores it. Reverse
in-game Disable behavior is not established by these chapter tests.

Repairs were game-tested on arrival saves. Automated tests compare the
production repair writer byte-for-byte with the accepted Test 2 exports and
check integration into chapter entry, guarded layouts, history and roundtrip.
A separate game test of the newly automatic entry application has not been
reported. No repeat chapter round is requested. Obelisk use and long-term
progression remain untested.

## Returned evidence

| Pair | Arrival sequence | Progress sequence |
| --- | --- | --- |
| 04 | `6d9d8f2bb9d63986` | `6d9d8f2bb9d63985` |
| 06A | `6d964f2bb9cfae78` | `e6d0b54e09973fe6` |
| 08 | `6daa8f2bb9e0c421` | `e6d6f54e099c1877` |
| 09A | `e6daf54e09a0012d` | `e6daf54e09a0012f` |

Return archive SHA-256:
`7bf11dc2edd06b501d7c4ef5d080cc5d1f5070e50adcfe6ab0098aed1fd591cb`.
Private saves and screenshots are excluded from Git. Historical Test 1 and
Test 2 builders retain their original behavior for reproducibility.
