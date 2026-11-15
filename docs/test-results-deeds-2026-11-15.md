# Notable Deeds: implementation validation and player acceptance

Branch: `feature/notable-deeds`, based on accepted Polish Test 2 commit
`61334982534ed962bb10ff50f72f9580b08c59fc`. The delivered archive's `BUILD.txt`
records its exact source commit and CI run. **The first player acceptance run
is complete; DEED-06 required the Test 2 confirmation.** Only [DEED-11–14](testing-notable-deeds.md)
remain pending. The Test 1 implementation checks below are retained as history.

## Scope

* 350 mapped milestones, 47 counters, 32 editable activity totals and 15
  read-only counters. One counter per action; no bulk completion preset.
* Claim state, reward amount and progress shown separately. Counter-only
  writes do not set state 2/4, change Karma Shards or touch the working Boon.
* 397 descriptive English Flags labels; exact Japanese keys remain Reads as.
* Accepted audience/travel features lose Experimental labels. The three
  hidden destinations say Effect unknown; Yu Phas Temple says Travel tested,
  retaining its Chapter 9 walking-entry restriction. Original 16 locator
  anchors are now explicit metadata, independent of presentation labels.
* POL-04/05 reported passed by the player; earlier AUD/FTX coverage limits
  remain documented rather than expanded by the label changes.

## Test 1 automated checks

`python -m unittest discover -s tests -q`: **59 passed**, five optional private
fixture checks skipped (64 discovered). With the private accepted B0 fixture,
**all 64 passed**. The fixture is read, never overwritten or distributed.

New synthetic checks cover:

* Every catalogue identity/hash, tier ordering, targets/rewards, edit policy
  and conflict-safe English label overlay.
* Reordered maps, missing zero counters, structural ancestry, insufficient
  anchors, duplicate keys and multiple candidate maps.
* One counter's short/wide encoding, promotion at 254 → 255, preservation of
  existing wide encoding, no-ops, absent-zero no-ops and adding a missing total.
* Exact preservation of all other records, including state 2, state 4 and
  unknown values, plus other blocks after pointer normalization.
* Invalid values, out-of-range totals, derived counters, unknown claim states,
  negative stored totals and attempts to write a claim hash.
* Real GUI commit-handler wiring: undo/redo, cache invalidation, dirty selected
  slot, mirroring refusal, read-only/invalid/no-op actions without history.
* Additional travel flags still cannot replace original map-identification
  anchors after removing Experimental metadata.

The added private test edits every one of the **32 editable counters** to its
last mapped target using a fresh B0 copy each time, serializes to a temporary
file and rereads it. Checksums verify, target totals persist and all other
map records retain their exact bytes. Tutorials, travel, audiences, blessing
EXP/selection/Sand also remain identical. The rest of the payload is compared
before serialization after normalizing relocatable pointers; serialization's
normal checksum updates are verified separately. This is a structural test,
not evidence that every last-tier reward is available in game.

The accepted fixture displays 39 stored counters, eight omitted zero counters
and 79 mapped claimed states. The earlier restored pre-claim fixture has 79
states at 2. These observations support the separate status display; they do
not establish that raising only a counter triggers completion on loading.

## Test 1 native GUI check

On a disposable copy in the test desktop, verified:

* Header identity, 350/47/32 totals and 79 claimed states.
* Ctrl+F search for Training, selecting its 75 tier, filling the target,
  Apply 65 → 75, related-row refresh, and unchanged Not stored state for 75.
* Undo to 65, Redo to 75, Save and Reload. Independent file reread confirms
  training 75 and valid checksums in the disposable GUI save.
* Hours played shows 17, read-only reason and disabled input/action buttons.
* Dark/light themes, themed horizontal scrolling to the hash column, and
  readable controls at 1240×800 and the approximately 1000×640 minimum size.
* Fast travel's three-unknown summary and Aurora's hidden rows marked Effect
  unknown. The last tab remains accessible in the compact layout.

The test desktop has pre-existing non-ASCII font/rendering problems. Japanese
keys are retained as Unicode in source and the labels pass identity tests;
user-side rendering still needs DEED-01/03 on Bazzite. Native UI checks do not
substitute for loading and claiming in the game.

## Original Test 1 acceptance gate (results below)

Direct threshold edits and a natural 74 → 75 training action are separate
cases. The player will check progress, when completion refreshes, exactly one
10-shard reward, stored 2 → 4, persistence, and no duplicate claim. Decreasing
a claimed total and adding an omitted counter also need game observations.
Other activities/routes/chapters/versions remain outside this first acceptance
run. The editor will not guess visibility flags if completion does not refresh.

## Player acceptance and supplied saves

The player reported **DEED-01–05, DEED-07A–D and DEED-08–10 passed** on the
same Leda Chapter 9 setup. DEED-06 exposed a real game-side claim reset and
requires the confirmation added in Notable Deeds Test 2. It is not recorded
as a preservation pass. No DEED-07 saves were retained; those four results
remain player-reported rather than independently compared.

All **nine supplied save files** verify without checksum errors. The following
comparisons use the live mapped counter/state records, not map indexes:

| Case | Supplied edit / before | Game-saved / after | Finding |
|---|---|---|---|
| DEED-04 | Training 75; 75-tier state absent; Karma 710 | Training 75; state 2; Karma 710 | Direct counter edit became complete-unclaimed during the reported load/menu check |
| DEED-05, training | Training 74; 75-tier state absent | Training 75; state 2 | One normal training action crossed the threshold |
| DEED-05, claim | Training 75; state 2; Karma 710 | Training 75; state 4; Karma 720 | Exactly +10 shards and 2 → 4; screenshots show Accept before and greyed claimed row after |
| DEED-06 | Training 40; 50-tier state 4; Karma 710 | Training 40; 50-tier state absent; Karma 710 | Game removed the 50-tier claim; 10/20/30/40 claims remain 4; screenshot shows incomplete 40/50 |
| DEED-08 | Gambits 1 | Gambits 1 | Counter persists, all mapped deed states unchanged; screenshot shows 1/10 |

Each pair's deed-map differences are exactly those shown above. Other game
systems can change during play; this is not a claim that the complete files
are byte-identical. The working shared-map EXP Boon candidate remains 1 and
Divine Sand remains 100 in all nine files. The post-claim save has 80 claimed
mapped milestones; the lowered-training game save has 78, versus 79 in B0.
The player also reported no repeat claim in DEED-05 and the preservation checks
passed. Re-earning and claiming a reset DEED-06 reward was **not** separately
tested, so duplicate-reward behavior must not be inferred.

The DEED-08 screenshot also establishes the English enemy descriptions
**livestock** and **golden or silver mummies**, matching the stored counters
6 and 1 respectively. Their catalogue names are corrected; editing remains
read-only because an isolated edit test was not performed. Theatre visits
and rooms rented at inns now use clearer screenshot-supported descriptions.

These findings supersede Test 1's assumption that preserving a claim flag in
the editor was sufficient to preserve it after loading. The editor still
writes only progress, but **the game recalculates completion and can clear
claims below target**. Direct completion was observed for training at 75;
it is not proof of all 350 milestones' availability or refresh conditions.

## Notable Deeds Test 2 validation

A proposed effective edit is checked against **all** claimed tiers for that
activity. If the new total is below any claimed target, an OK/Cancel warning
uses the player's requested wording and lists affected targets. Cancel is
the default. Cancel/Escape/closing returns without changing the deed payload,
dirty state or undo history. OK applies the ordinary counter-only operation;
claim flags and currency are still preserved until the game acts on them.

Exactly meeting a claimed target, a decrease that still meets every claimed
target, a normal increase, no-op and invalid input do not prompt. A pre-existing
inconsistent claim is not silently ignored: if an edit still leaves its
target unmet, it prompts even when increasing progress.

Automated suite: **63 public tests passed**, five private-fixture tests skipped
(68 discovered). New checks cover multi-tier risk, strict target comparisons,
Cancel with no mutation/history, OK with claim preservation and undo/redo, and
no warning for safe/invalid/no-op actions. Binary mutation logic is unchanged
from Test 1; the nine supplied files were analysed read-only. Test 2's native
UI and CI outcome are recorded in the delivered archive's `BUILD.txt`.

Native Test 2 check on a disposable B0 copy at 1240×800: the dark-theme
warning displayed the exact requested wording, target 50 and readable
OK/Cancel buttons, with Cancel focused. Escape and the Cancel button both
left training 65 and the save clean. OK changed the total to 40 while the
50-tier still displayed Claimed (4); Undo restored 65. Automated tests
separately check no history entry on Cancel and Redo of the approved edit.

Only [DEED-11–14](testing-notable-deeds.md) are requested for this follow-up.
