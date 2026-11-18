# Troubleshoot Progress

On **Player**, choose **Troubleshoot Progress**. It reads the selected save's
current character, part and chapter and checks the established prerequisites
for that exact context. Opening or closing the dialog changes nothing.

The table distinguishes missing unlocks from those already enabled. **Apply
suggested unlocks** stages only the missing prerequisites in that save; Save
writes them and Undo/Redo restores/reapplies them. It keeps the current story
checkpoint, date, restart snapshots, party and inventory. It does not restart
the chapter. Turn off editing other saves before applying a repair.

| Context | Known repair |
| --- | --- |
| Cai Part 1, Chapters 3–12 | Sewers entrance dialogue permission; still depends on the story phase |
| Dietrich Part 1, Chapter 5 | Upper-city movement for the certification objective |
| Dietrich Part 1, Chapter 6 | Lower movement, upper/lower area access and Vandahl Trading Company; retain the upper movement restriction |
| Dietrich Part 1, Chapter 7 | Hidden Windpierce teaching permission; teach an eligible recipient yourself |
| Theodora Part 1, Chapter 4 | Middle-city movement to the arena |
| Theodora Part 1, Chapters 6/8 | Middle/lower/district movement; Chapter 6 can require the alternate path around the NPC barrier |
| Theodora Part 1, Chapter 9 | Show Troy’s Shrine, Junction 374 and Wandering Wood; preserve visited state |
| All four routes, Part 2 Chapter 5 | Upper-city movement to Dagda’s temple |
| All four routes, Part 2 Chapter 6 | Middle-city movement to Dagda’s cauldron |

No earlier-chapter fixes are applied indiscriminately. Unsupported states are
read-only; unknown parts, including Part 3, have no guessed repairs. Dietrich
Part 1 Chapters 1/2 and Leda Part 1 Chapter 1 explain their unresolved replay
blocks. Already-enabled prerequisites do not guarantee an objective can progress.

When there is no actionable suggestion, the dialog offers the upstream
[issue tracker](https://github.com/Antiadvocate/fefw-editor/issues). It asks for
character, part, chapter, objective and the blocker, with a screenshot and an
optional save. Clicking opens the tracker; nothing is submitted automatically.

## Editor checks

1. Open a previously blocked free-time save. Check the detected character,
   part and chapter, the expected missing unlocks, and any already-enabled rows.
2. Close the dialog: no edits or history entry should be created.
3. Reopen and apply. Reopen again: the unlocks should now be enabled. Confirm
   the chapter, current story beat, date, units and inventory were retained.
4. Undo/Redo, then save and reopen. Confirm the unlock state follows the edit.
5. A different save slot must remain unchanged. With multi-save editing on,
   inspection works but Apply is disabled.
6. On the confirmed Theodora Part 2 Chapter 6 arrival, midtown access should
   already be enabled. The issue-tracker option is offered if still blocked.
7. With a chapter that has no known repair, check the explanation and issue
   link. There should be no enabled Apply action. Part 3 has no established fixes.

The underlying repair combinations have prior game evidence. This new dialog
and applying them at arbitrary later story beats still need user testing.
