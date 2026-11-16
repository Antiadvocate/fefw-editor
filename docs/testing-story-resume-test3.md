# Story resume — Test 3

These are diagnostic copies, not accepted fixes or a new baseline. Test 2
failed to start chapters correctly. Test 3 checks a separate resume identifier
that the earlier tests did not change, followed by an optional removal of the
empty HubSeq save object. The editor's chapter action remains paused.

## Cases

| Order | Target | Change beyond its Test 2 C setup |
|---|---|---|
| ST3-09D-Resume-id | Chapter 9 | Replace the separate free-time resume identifier with the value observed in working chapter-start checkpoints. |
| ST3-09E-No-HubSeq | Chapter 9 | D plus remove the empty HubSeq root object, which is absent from the natural checkpoints. |
| ST3-04D-Resume-id | Chapter 4 | The same single-identifier change for Chapter 4. |
| ST3-04E-No-HubSeq | Chapter 4 | The same optional HubSeq removal for Chapter 4. |

All four independently start from the accepted B0-01 Auto. As in Test 2 C,
Chapter 9 is set to July 10 at 18:00 and Chapter 4 to March 1 at 08:00; schedule
and Calendar caches are cleared, and restart slots are empty. Those shared
changes are not new evidence of a fix. D isolates the additional 8-byte
identifier; E tests whether the serialized hub sequence also matters.

Current units and their unique unit numbers, facilities/fast travel, currency,
Boons, Deeds, supports, inventory and all flag maps are preserved by the edits.
Hub/location, active conversation and world-map records also remain from the
current baseline. The game may alter state while executing a chapter opening;
compare availability and roster after entry. No external chapter file is
created, modified or included in this kit.

## Player checks

1. Back up the entire save folder into a fresh directory, then close the game.
2. Install just one case's Auto and load **Continue / Auto**. Keep the other
   files as in Test 2; do not invoke Restart to obtain the initial result.
3. Test **09D → 09E → 04D → 04E** separately, closing the game between files.
4. Record whether the chapter opening runs or the game resumes old free time,
   the location/date, HUD and journal objectives, and remaining turns.
5. Check that the roster and facilities have not reverted to the old checkpoint.
   Note any changes; scripted chapter-specific restrictions are still possible.
6. If entry looks correct, check that the next main story beat happens. A
   blocked result can be stopped early; do not spend time trying unrelated flags.
7. Return one game-resaved Auto per case after the initial checks. If it hangs
   or cannot save, report that result instead. Restart is a secondary check only
   after a successful initial entry; keep an extra after-restart save separately
   named if you test it.

The untouched `00-Control/Auto` is for comparison, not a new baseline. The
included editor remains paused for chapter edits; prepared saves need no
editor action. Other previously accepted editor features remain available.

## Interpretation and reproducibility

- D works: the separate resume identifier is implicated; check preservation and
  restart behavior before selecting an implementation.
- E improves on D: the retained serialized hub sequence also matters.
- Chapter 9 works but Chapter 4 does not: entry is still chapter-specific.
- Neither works: preserve the failed records and investigate the live script,
  hub and conversation state. Avoid importing an entire older checkpoint just
  to make the chapter run, because that reverts accepted progress.

`research/story_resume_probe.py` builds these cases from the fingerprinted
private baseline into a fresh directory. It checks the source route, v23
layout, known free-time identifier, checksums, and outer/live agreement.
The HubSeq removal requires the exact observed empty object and a contiguous
root table, relocates retained objects, and checks normalized equality.
Every current flag map is preserved; D/E change only their declared fields
beyond Test 2 C. Reopened file integrity is not proof of in-game compatibility.
