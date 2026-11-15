# Notable Deeds Test 1: implementation validation

Branch: `feature/notable-deeds`, based on accepted Polish Test 2 commit
`61334982534ed962bb10ff50f72f9580b08c59fc`. The delivered archive's `BUILD.txt`
records its exact new source commit and CI run. **Game acceptance for this
new page is pending [DEED-01–10](testing-notable-deeds.md).**

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

## Automated checks

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

## Native GUI check

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

## Remaining acceptance gate

Direct threshold edits and a natural 74 → 75 training action are separate
cases. The player will check progress, when completion refreshes, exactly one
10-shard reward, stored 2 → 4, persistence, and no duplicate claim. Decreasing
a claimed total and adding an omitted counter also need game observations.
Other activities/routes/chapters/versions remain outside this first acceptance
run. The editor will not guess visibility flags if completion does not refresh.
