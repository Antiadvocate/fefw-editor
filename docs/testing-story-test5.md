# Story progression — Test 5

Chapters 4–12 and the Test 4 UI checks passed. This round tests **Chapters 1–3**
and the new optional **chapter-start file for the Obelisk**. Both remain Inferred
until these game checks pass. Your accepted B0-01 baseline is unchanged.

## Prepared Chapter 1–3 saves

Back up your whole save folder to a fresh directory and close the game before
replacing any file. Install one case's Auto at a time and load Continue/Auto.
Each is independently made from the accepted baseline; do not chain the cases.
The 00-Control/Auto is an unchanged copy for comparison and editor tests.

| Case | Chapter | Entry clock before the opening runs |
|---|---|---|
| ST5-01 | 1 | December 1, 1444, 12:00 |
| ST5-02 | 2 | January 2, 1449, 12:00 |
| ST5-03 | 3 | January 20, 1449, 20:00 |

For each:

1. Confirm the opening plays and places Leda at the correct starting location.
2. Check the date and immediate objective where shown. Early chapters may have
   different UI/facility restrictions from the later town chapters.
3. Follow the immediate objective until the **next main story beat or battle**
   starts. No need to complete a whole chapter.
4. Save/reload where available. Note any roster or feature changes separately;
   the editor keeps current records, but the chapter script may change them.
5. Return an Auto after opening and an Auto-after-advancement if practical.
   If blocked, return the nearest save and describe where progression stopped.

These candidates use the successful full entry/resume setup. Chapter 1's
historical year comes from its natural checkpoint, and later targets explicitly
restore 1449. The title row alone did not provide Chapter 1's date. The new setup
is still untested at these early starts; earlier sequence-only failures do not
count as a pass or failure for this version.

## Editor and chapter-file checks

Use a **disposable copy** of 00-Control/Auto for these. Pick Chapter 9 (or 4) so
Obelisk testing uses an already verified opening. Close the game while editing.
The checkbox creates only the chosen chapter's file beside the selected save.

- **UI5-01 — labels and warning:** Player → Story progression… has Chapters 1–12;
  4–12 are Game-tested and 1–3 Inferred. The Obelisk bullet explains the checkbox,
  Save, confirmation and backup, immediately above the fresh-backup bullet.
- **UI5-02 — Save only:** select Chapter 9 and check **Create a chapter start file
  using this state**. Apply. The Player status names Chapter_Led_1_9 as pending,
  but neither Auto nor the chapter file changes on disk yet. Undo removes the
  request; Redo restores it. Reload/discard cancels it. Reapply to continue.
- **UI5-03 — new file:** in a disposable folder with no Chapter_Led_1_9, Save.
  It should write Auto and Chapter_Led_1_9, list the new slot and clear pending.
  No overwrite confirmation or chapter backup is needed for a new file.
- **UI5-04 — existing file:** keep a copy of that chapter file, make a visible
  ordinary edit such as Gold on the staged start, and explicitly check/Apply
  the same chapter again. Save should ask to replace Chapter_Led_1_9. Choose No:
  neither file changes and edits remain pending. Save again and choose Yes:
  the previous chapter bytes are backed up first. The first backup is .bak;
  later distinct versions become .bak1, .bak2, etc., without replacing .bak.
- **UI5-05 — unchecked:** on another disposable baseline copy, apply a chapter
  with the box unchecked and Save. No chapter file should be created or changed.
  Also verify Flags stays furthest right and Cai remains read-only if convenient.
- **OB5-01 — Obelisk discovery/load:** install the editor-created Chapter_Led_1_9
  in a backed-up game save folder with an Obelisk-accessible free-time save.
  Keep the working free-time Auto for accessing the chamber; the new chapter
  file contains the staged chapter-start state. Check that the chapter appears
  in the Obelisk and can be loaded. Confirm its opening, expected roster/state,
  and next main story beat. Do not assume the checkbox unlocks the Obelisk itself.

Please return the editor-created chapter file, a game-resaved Auto after loading
it through the Obelisk, and any progression return. If the file exists but the
chapter does not appear, report that separately from whether Continue/Auto works.
No need to repeat all Chapters 4–12. Chapter-file discovery/loading is the new
uncertainty; writing a valid file alone is not proof that the Obelisk uses it.

After a successful Save, Undo never deletes the external file. Another intentional
replacement needs checking the option and Applying again. Reopening the editor
has no queued file writes. Existing chapter files are never automatically copied
from another folder or used to replace the accepted baseline.
