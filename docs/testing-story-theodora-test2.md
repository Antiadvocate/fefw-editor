# Theodora story and Functions — Test 2

**Historical test guide:** chapter results are now recorded in
[Test 2 results](test-results-story-theodora-test2.md). Accepted repairs are
integrated into chapter selection. The original instructions below are retained
for provenance; no repeat chapter round is requested. The new Functions UI
check has no separately reported result.

Theodora Chapters **1–3, 5, 7 and 10–12** and all Test 1 UI checks are accepted.
Chapter 2's straight-to-battle transition is sufficient. This round only tests
the four blocked chapters and the newly exposed movement controls.

## Game tests

Close the game before replacing Auto. Keep your working save folder backed up
and use a disposable copy. Each case resumes your own blocked return; copy its
Auto independently. The chapter objective, clock and party are preserved.

| Order | Case | Action |
| --- | --- | --- |
| 1 | T2-04-Middle-gate | Try the upper-city gate, reach the arena objective and progress |
| 2 | T2-06A-City-passages | Walk past the NPC barrier and through any remaining city/port entrance; reach the Trading Company and progress |
| Conditional | T2-06B-Passages-and-functions | Only if 06A clears the paths but the required service/access is still missing; repeat from this independent Auto |
| 3 | T2-08-City-passages | Pass the NPC barrier and reach the next story event |
| 4 | T2-09A-Troy-exit | Try leaving Troy's Shrine through Wandering Wood; continue toward the Fezzan Gate objective |
| Conditional | T2-09B-Route-to-Fezzan | Only if 09A still cannot provide a usable route: shows the connected road path to Fezzan Gate; gates, dungeons and encounters retain their normal conditions |

Save `Auto-arrival` after loading and `Auto-after-progress` after the next
meaningful event/battle, where possible. Report both whether the original
block disappears and whether the objective progresses. If a new gate, dungeon
or encounter blocks Chapter 9 later, return that save and location. No need
to retest successful chapters, old UI checks or tutorial names.

## Functions controls

Open **Functions → Saved switches → Area access**. New rows:

- Dagsion upper-area movement
- Dagsion middle-area movement
- Dagsion lower-area / port movement
- Wealthy–commercial district passage

**Enable selected clears the corresponding restriction. Disable selected puts
it back.** These are separate from the existing upper/lower area access flags.
Vandahl Trading Company remains under Service. The row notes distinguish
Dietrich's tested scope from the pending Theodora repairs. Other story-specific
barriers remain separate.

One new UI check, on a disposable copy of the original blocked Chapter 4 Auto:
find **Dagsion middle-area movement**, Enable, Undo, Redo, Save and reload.
The row should remain Enabled after reload. Compare its in-game effect with
T2-04. Optionally Disable it on another disposable copy to check the reverse.
Neither operation changes the separate upper/lower area-unlock switches.

Theodora's ordinary chapter picker still reports the known blocks and does
not auto-apply these untested repairs. Map probes use existing World map data,
not Functions flags. Route mirroring must be off for Functions edits.

## Changes and verification

| Case | Change |
| --- | --- |
| 04 | Remove middle movement restriction only |
| 06A / 08 | Remove middle, lower and wealthy–commercial district movement restrictions |
| 06B | 06A plus upper/lower function access and Vandahl Trading Company |
| 09A | Three map state bytes set to Shown |
| 09B | 35 map state bytes set to Shown along a 37-node road path |

All probes preserve story/clock, party, tutorials, unrelated flags and root
objects. Map probes preserve every byte except their selected visibility
states; visited/secondary fields and record tails stay intact. Inputs are
fingerprinted and never overwritten. Export checks do not establish game
acceptance. See [Test 1 evidence](test-results-story-theodora-test1.md).

Reproduce with:

```bash
python research/theodora_retry_kit.py /private/Test1Returns /fresh/test-saves
```
