# New units — Test 1

This test adds character creation, duplicate protection and editable unit
numbers. It includes the current tutorial-category correction. No chapter
retesting is needed; the checks below concern units and identity only.

## Before testing

Use a separate copy of the save folder with the game closed. Each test case
contains an independent `Auto`; install one case at a time. Keep the original
folder and its other slots. Start the included editor as usual using
`python editor.py` from its `editor` folder. Backups are made when the editor
saves, and the kit's two control saves provide the unchanged inputs.

| Case | Baseline and change | Main check |
|---|---|---|
| U1 — Cai additions | Cai Chapter 4: adds Buccar, Sirocco, Catania and Olympia at level 1, numbers 38–41 | Deploy all four and an original party member together; check the old identity-collision pattern |
| U2 — Leda addition | Original Leda Chapter 9: adds Guzran at level 1, number 49 | New unit appears, can equip/use a weapon and survives save/load |
| U3 — Leda renumber | Same Leda control: Buccar 48→49 and Sirocco 1→50; all other numbers and unit progress retained | Buccar/Catania and Sirocco/Olympia each remain independent after changing existing IDs |

## Game checks

For each case, load the save and check the roster, class, level and equipment.
New units may need a weapon from the convoy. At the next practical battle:

1. Deploy the relevant units together. Select each separately and verify its
   portrait, stats and highlighted tile belong to it.
2. Move each unit, then cancel. It must return to its own tile without selecting,
   moving or changing another unit. Pay particular attention to
   **Catania/Buccar** and **Olympia/Sirocco** in U1 and U3.
3. Complete an action/attack with a new unit and, when practical, gain a level.
   Check equipped skills, HP and growth behave plausibly. Class-derived mount
   behavior and natural starting loadouts are not yet confirmed.
4. Save in game, reload and repeat selection/movement. Return that save as
   `Auto-after-progress` inside the case folder, with brief observations.

If an added character later reaches its normal recruitment event, check that
the event progresses and leaves only one copy. This is a separate long-term
check; do not replay a whole route just for it now. Initial acceptance will not
claim later recruitment events are proven.

## Editor checks

- Open a control save. Check **Unit #** is visible and **Add unit…** can be
  searched by character/class. Existing party members and restricted entries
  cannot be added. Choose an absent enabled candidate and confirm its preview.
- Add it, then try again: the second copy must be refused. Undo, Redo, Save and
  reopen; its number and defaults should persist. Original units retain theirs.
- Change its number to one already used by another unit: refuse without a
  change. Use a free number: apply, Undo/Redo and reopen after saving.
- On a disposable copy, set that character's **Recruited** flag to zero in
  Flags. Add unit should offer **Restore recruitment**, keeping the same record,
  number, stats and inventory. Undo/Redo should also work. This only tests the
  flag restoration, not revival or every reason a character might be hidden.
- **Copy unit in…** refuses a character already in the destination. An absent
  character without attached mounts/battalions receives a new number.
- With route mirroring enabled, unit identity actions are refused. They should
  also refuse a battle/checkpoint save or unmapped mount-affinity data.

The kit contains data-derived candidates, not a claim that every catalogue
character works on every route. Report any load failure, missing unit, unusual
stats/skills, movement collision or save/reload change before using it on your
main playthrough.
