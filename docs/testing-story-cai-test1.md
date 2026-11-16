# Cai story progression — Test 1

This kit uses your supplied native Cai Auto from Part 1 Chapter 2. It contains
three independent candidates and an unchanged control. No Route_Kai is required
or created. The original Cai source, natural chapter checkpoints and accepted
Leda baseline remain unchanged.

## Prepared game tests

Back up the full game save folder into a fresh directory. Close the game before
replacing Auto. Install one candidate's Auto at a time, use Continue/Auto and
let the opening run. Keep your existing Chapter_Kai_1_* files in place; these
prepared candidates do not replace them. Do not chain one candidate's result
into another test.

| Test | Target | Entry clock before the opening |
|---|---|---|
| CAI1-02 | Chapter 2 | January 25, 1449, 11:00 |
| CAI1-04 | Chapter 4 | March 1, 1449, 12:00 |
| CAI1-09 | Chapter 9 | September 3, 1449, 12:00 |

For each:

1. Confirm the opening runs and Cai appears at the correct starting location.
   Note music, movement/control or objective problems.
2. Check the current date, HUD/journal objective and deadline where available.
   The opening may advance the clock from the entry time shown above.
3. Follow the objective or wait until the **next main story beat or battle**.
   No need to finish the whole chapter.
4. Check save/reload where practical. Note roster and facility differences;
   these candidates retain your current three-unit roster and existing flags,
   but chapter scripts can apply their own restrictions/changes. Missing later
   recruits or unlocks are expected unless the game grants them itself.
5. Return Auto after the opening and a separate Auto-after-advancement where
   possible. If blocked, return the closest save and describe the stopping point.

All three targets are **Inferred** until your results. Natural Chapter 2's ID
and clock support the mapping; they do not prove that replaying its entry with
the later Auto state is harmless. Chapter 1 and other Cai targets are deferred.

## Editor checks on a disposable copy

- **CUI-01:** open the control Auto. Story progression identifies Cai Part 1,
  offers only Chapters 2/4/9, labels all Inferred, and explicitly says Cai edits
  and chapter files are not game-tested. Flags remains furthest right.
- **CUI-02:** select Chapter 4, Apply, Undo and Redo. Disk files remain unchanged
  until Save. Save/reopen shows Cai Chapter 4; its original Auto backup is kept.
- **CUI-03:** on another disposable control copy, select Chapter 2 and check
  Create a chapter start file using this state. Apply queues Chapter_Kai_1_2.
  Save creates it; if an existing copy is present, No cancels the whole Save and
  Yes backs it up first (.bak, then numbered backups). No Chapter_Led or Route_Kai
  file should be created. Reload/discard removes an unsaved request.
- **CUI-04:** open a Leda copy: it still offers 2–12 as Game-tested and hides
  Chapter 1. Other routes, other parts, battle and unsupported states remain
  read-only. Changing slots then Undo must not modify the other slot.

No additional Obelisk unlock or whole-route switch is needed for this first
round. If you already have access and choose to test an editor-created Cai
checkpoint through the Obelisk, record that as an extra result and return the
created Chapter_Kai file plus a game-resaved Auto. It is separate from ordinary
Continue/Auto acceptance.

## Route_Kai observation

Its exact natural creation trigger has not been established. It may be written
when retaining a route as play moves elsewhere, but this is only a hypothesis.
Note if it appears naturally during these tests; there is no need to force that
transition. Its absence does not prevent any test in this guide.
