# Notable Deeds Test 1: acceptance guide

The header must say **Notable Deeds Test 1**. `BUILD.txt` identifies the source
commit and CI run. Extract to a fresh folder and launch its `editor.py` using
your already-working environment; there are no new dependencies.

Use **Leda Part I Chapter 9 / fefw-recomp-0.1.5** and the accepted B0 baseline.
Keep B0 untouched. Start each in-game case from a separate disposable copy.
Close the game before editing and the editor before loading in game. Keep
route mirroring off. Retain the exact edited slot and the game's written slot,
including its name if different. Do not carry a test save into normal play.

This build edits counters only. Completion and claim states are deliberately
preserved. **DEED-04 is an observation gate**: we need to learn whether loading
alone refreshes completion. Do not add state flags manually if it does not.
Claim only the named reward during DEED-05, never Claim all. If unrelated deeds
also complete, record them separately. Stop a case if the save fails to load,
progress changes unexpectedly or rewards can be claimed twice.

## Editor checks

| Case | Steps and expected result |
|---|---|
| **DEED-01** Baseline and labels | Open B0. Expect 350 milestones, 47 counters, 32 editable, 79 claimed, 0 stored complete-unclaimed. Training total 65, foes 281, gifts 35, base-shop spending 39,235, ore 61, hours 17. Record actual differences if your baseline differs. Search each English label; search a displayed Japanese key and hash too. Flags should use English descriptions with Japanese in Reads as. Capture the baseline and selected training detail. |
| **DEED-02** Input, history, save | Select Training target 75. Use selected target fills 75 but creates no unsaved change. Apply changes the total and related rows, retaining claim states. Undo returns 65; Redo returns 75. Save/Reload retains 75. Reject `-1`, `1.5`, `abc`, and 101 with no edit/history change. Reapplying 75 is a no-op. Turn mirroring on and attempt 74: refuse with no change; turn it off again. If mirroring is unavailable for one slot, mark that substep BLOCKED (single slot). |
| **DEED-03** Read-only and layout | Select Hours played, a skill-level counter, a blessing-level counter, a support-conversation counter and a translated enemy category. All inputs/buttons disabled with reasons shown. Inspect the new tab at normal and minimum window sizes, horizontal/vertical scrollbars in both themes, and Ctrl+F. No clipping of the form or missing last tab. |

## In-game checks

### DEED-04 — Does direct completion refresh on load?

Fresh B0 copy: change **Training sessions 65 → 75**, Save/Reload. The 75 tier
should say **reached**, while its claim state stays **Not stored** in the
editor. Record Karma Shards before the edit in the game baseline.

Load the edited slot and open Notable Deeds before performing an activity.
Record the training progress, whether the 75 reward is offered, and Karma
Shards. **Do not claim it in this case.** Save/quit and reopen the game's slot
in the editor. Record the counter and the 75-tier claim state. If the reward
is offered, expect unclaimed state 2 and unchanged Karma Shards. If not, report
**COUNTER PERSISTED / COMPLETION NOT REFRESHED** with the actual state and
screenshots. This is useful evidence; do not guess a workaround.

Keep `Auto (DEED-04 edited)` and `Auto (DEED-04 game saved)`.

### DEED-05 — Natural threshold crossing and one reward claim

Fresh B0 copy: change **Training sessions to 74**, Save/Reload, then load in
game. Perform **one normal training session**. Check whether progress becomes
75 and the 75 milestone offers its **10 Karma Shards** reward. Other already
claimed training tiers must stay claimed. Record the result even if the game
behaves differently.

If the reward is offered, save before claiming, record the Karma balance, and
claim **only the 75-training reward**. Expect **exactly +10**, state **Claimed
(4)**, and no second claim available. Save/quit/load again, check balance and
claim status, then reopen the game's save in the editor. Training should be
75 and the 75 tier Claimed (4). If multiple rewards became available, do not
claim those; name them in the report. If a direct-completion reward from
DEED-04 was offered, that result is separate from this fresh-copy case.

Keep `Auto (DEED-05 edited)`, `Auto (DEED-05 before claim)` and
`Auto (DEED-05 after claim)`, with before/after reward screenshots.

### DEED-06 — Reducing progress does not reset claimed rewards

Fresh B0 copy: change **Training sessions 65 → 40**, Save/Reload. Claimed
10/20/30/40/50 milestones stay Claimed (4) in the editor. Load and inspect;
record the game's actual progress and claim behavior. Do not claim anything.
Save/quit/reopen and check whether 40 persisted or the game recalculated it.
No previously claimed reward should become claimable again. Retain before and
after files if it does, and stop using that test copy.

### DEED-07 — Representative counter families

Use a **fresh B0 copy for each row**, one edit only. Save/Reload, load in game,
inspect the relevant deed, then save/quit/reopen in the editor. Do not perform
an activity or claim rewards. These values stay below the next target, so no
new completion is expected. Report stored persistence and visible progress
separately; capture any mismatch.

| Subcase | Activity | B0 total → test total | Next target |
|---|---|---|---|
| A | Foes defeated in battle | 281 → 299 | 300 |
| B | Gifts given | 35 → 39 | 40 |
| C | Gold spent at shops in bases | 39,235 → 49,999 | 50,000 |
| D | Pieces of ore obtained | 61 → 99 | 100 |

Keep each edited and game-saved pair, labelled DEED-07A through DEED-07D.
Other editable activities still require broader testing; this is a first pass.

### DEED-08 — Previously omitted zero counter

Fresh B0 copy: select **Gambits used**. Expect current total **0 (not stored)**.
Apply 0: no unsaved change. Set it to **1**, Save/Reload. Load in game and inspect
the deed if listed; record **NOT LISTED** if hidden. Save/quit/reopen and check
whether 1 persists or returns to missing/zero. No reward should be granted.
Keep the edited and game-saved pair. Do not unlock other features to reveal it.

## Preservation and polish

* **DEED-09:** On a game-saved result above, check the chapter/route, roster,
  tutorials, travel list, blessing EXP/audiences/selection, Divine Sand and
  active 10% EXP Boon against that case's baseline. Karma remains unchanged
  except the explicit +10 claim in DEED-05. Natural training costs or gains
  belong to DEED-05 and should be reported separately. No editor change should
  affect other save slots. Check no-op save/reload and reopening the original B0.
* **DEED-10:** First-audience controls no longer say Experimental. Fast travel
  shows **Effect unknown** for Aurora's private room, Aurora's garden and
  Salamis Guesthouse; Yu Phas Temple says **Travel tested** and the footer
  retains its Chapter 9 entry caveat. This is a label check only; no repeat of
  AUD/FTX game tests. Both themes' scrollbars should retain the accepted polish.

## Report template

```text
Build / commit (BUILD.txt):
Environment changes from Bazzite 45 / Leda Ch9 / recomp 0.1.5:
Baseline / edited slot / game-written slot:
DEED-01:
DEED-02: (input, undo/redo, save/reload, mirroring)
DEED-03:
DEED-04: counter / game progress / reward offered? / saved claim state / Karma
DEED-05: counter after training / reward offered? / Karma before → after / state / no repeat claim
DEED-06: progress / claim behavior / persistence
DEED-07A:
DEED-07B:
DEED-07C:
DEED-07D:
DEED-08: shown or hidden / counter persistence
DEED-09:
DEED-10:
Unexpected changes / screenshots / save pairs:
```

PASS, FAIL and BLOCKED are valid outcomes. For DEED-04/08, an accurately
recorded lack of visible effect is useful research rather than a reason to
alter extra flags. The next build will follow the evidence from these cases.
