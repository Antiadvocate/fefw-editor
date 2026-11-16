# Story progression — Leda and Cai Part 1

Player → Story progression… offers **Leda Part 1 Chapters 2–12**, all accepted
for the chapter opening and next main story beat. **Chapter 1 cannot be selected**:
its opening plays, but control resumes without music and reaching the objective
does not advance. The user chose to exclude it rather than prolong this round.

All Test 5 UI checks passed. Editor-created chapter files loaded and worked
through the Obelisk for **Chapters 8 and 9**. Other chapter files have not been
game-tested through the Obelisk; ordinary entry acceptance is a separate result.
See [Test 5 results](test-results-story-test5.md). Full-campaign behavior remains
untested.

**Cai Part 1** offers Chapters **1–12**. Chapters **1, 5–8 and 10–12** are
Inferred and awaiting the next game tests. Chapters 2/9 passed initial
progression tests; Chapter 3 was completed into Chapter 4. Enabling the missing
Sewers dialogue prerequisite fixed the Chapter 4 objective on that natural
return. Direct Chapter 4 entry with the automatic prerequisite remains to be
game-tested. Cai Obelisk use is untested.
See [Sewers results](test-results-sewers-functions.md).

For every supported Cai Chapter 3+ selection, the chapter action also enables
**Functions → Area access → Sewers access (Cai)**. Both changes share one
Undo/Redo step and are saved to Auto and any requested chapter file. Reapplying
a chapter restores the prerequisite if it was disabled. Selecting Chapter 2
does not remove it. Ordinary Save never enables it by itself.

Other routes/parts, battle saves and unsupported or inconsistent layouts remain
read-only. The editor checks actual save contents, not filenames or party members.

## Using the editor

1. Open a disposable, supported Leda or Cai Part 1 free-time or chapter-start save.
2. Turn off route mirroring, then click Story progression… on Player.
3. Read the warning and back up the whole save folder into a fresh directory.
4. Continue to the chapter list. Each target carries its evidence label.
5. Optionally check **Create a chapter start file using this state**. It queues
   `Chapter_Led_1_<chapter>` or `Chapter_Kai_1_<chapter>` beside the selected save,
   according to the actual route. Unchecked creates no file.
6. Apply stages the chapter/date and file request. Ctrl+Z/Ctrl+Y undo/redo both.
7. Save (Ctrl+S) writes the selected save and any requested chapter file. Existing
   chapter files require confirmation first. No cancels the whole Save and keeps
   the edits/request pending. Yes backs up the existing file before replacing it.
8. Use Continue/Auto for the normal entry; separately check Obelisk discovery
   and loading of the new chapter file. Let the chapter opening run.

Cancellation changes nothing. Reapplying an identical staged entry and checkbox choice is a no-op.
Changing chapters after staging another entry is supported. Undo is confined to
its loaded save object; it cannot overwrite another slot or a reloaded object.

The warning title remains **CAUTION - UNEXPECTED CONSEQUENCES POSSIBLE**. It
retains the user's points about Leda Part 1, no previous unlock/unit grants,
limited testing, the Obelisk Chamber and a fresh-directory backup. The Obelisk
point is immediately above backup. Warning text follows the loaded route: Leda
explains Chapter 1's exclusion and its tested scope; Cai explains the automatic Sewers exception, Chapter 3 acceptance, Chapter 4 conditional pass and untested Obelisk use. Changing route while either
dialog is open requires reopening it. The picker never chooses a different route.

## What is changed

`story_start.edited` reproduces the successful **Test 3 D** setup. Its Leda Chapter
4/9 payloads and serialized files match the delivered D candidates exactly.
Removing HubSeq brought no observed improvement, so it is retained. Cai uses
the same preparation mechanics with its own validated selector prefix and dates;
that structural agreement does not establish game compatibility.

| Saved component | Chapter-start edit |
|---|---|
| Header, GameUserData and outer summary | Target chapter and chapter-entry sequence |
| GameUserData v23 body+58, u64 | Separate resume identifier: `d8588d186b3f9502` → `a2f3e9a7ff461708` |
| Header state bytes, block+20/+21 | Observed chapter-start context `10 0b` |
| Header and GameSchedule clocks | Route-specific entry date/time: Leda Chapter 1 in 1444; all Cai entries and later Leda chapters in 1449 |
| Remaining GameSchedule / Calendar cache | Empty checkpoint form, retaining known version markers |
| Eight internal restart slots | Validated Header/Data blobs cleared; the game rebuilds a target checkpoint during entry |
| Outer raw+48..56 | State/clock mirrored from the current payload during serialization, including after Undo |

Apart from the Cai Chapter 3+ Sewers dialogue record, current flag maps, units and unique unit numbers, inventories, currencies,
Boons, Deeds, supports, facilities and fast-travel registrations are preserved
by the edit. Hub/location, world-map and conversation records are also retained;
the game's chapter scripts establish the new live scene. Those scripts may
apply chapter-specific restrictions or changes. Chapter 4's temporary fast-travel
restriction was reported as expected story behavior.

The D profile includes all the date, schedule and restart preparation from
Test 2 C. The tests isolate the additional resume identifier against that setup;
they do **not** establish that the identifier alone is sufficient on an otherwise
untouched save. Exact runtime enum/type names are still unrecovered.

## Leda target dates and evidence

| Chapter | Entry date/time | Short-session evidence |
|---|---|---|
| 1 | Historical probe: December 1, 1444, 12:00 | Failed first objective; unavailable |
| 2 | January 2, 1449, 12:00 | Game-tested opening/next beat |
| 3 | January 20, 1449, 20:00 | Game-tested opening/next battle |
| 4 | March 1, 1449, 08:00 | Game-tested opening/location/next beat |
| 5 | April 6, 1449, 12:00 | Game-tested opening/next beat |
| 6 | May 8, 1449, 12:00 | Game-tested opening/next beat |
| 7 | May 28, 1449, 20:00 | Game-tested opening/next battle |
| 8 | June 29, 1449, 11:00 | Game-tested opening/next beat |
| 9 | July 10, 1449, 18:00 | Game-tested opening/location/next battle |
| 10 | September 28, 1449, 02:00 | Game-tested opening/next battle |
| 11 | October 16, 1449, 12:00 | Game-tested opening/next battle |
| 12 | November 7, 1449, 12:00 | Game-tested opening/next battle |

The opening can advance the clock: Chapter 9 settles on July 12; Chapter 4's
returned opening saves are March 1 at noon. Chapter 1 inherits its title date, so its captured natural checkpoint supplies
December 1, 1444 at noon. Chapter 2 independently matches its natural checkpoint.
The other month/day/time values come from title rows in `Timeline_Part1_Led.bin`, SHA-256
`8fd921c3dd2ca18af17fa54f22fd3b99fadbaffdacfcc28f8ef377435caab5d5`.
The game data is not bundled or required at runtime. Reproduce the read-only
report with `python research/story_timeline_report.py /path/to/GameData`.

Chapter sequence hashes remain the independently matching Chapter 1/2 FNV-1
suffix pattern, with prefix state `fde8dadc5dfc1118` and suffix `<chapter>_1`.
Chapter 9's entry is `b79bcc2aad7433e5`. The full symbolic key is unrecovered;
real Chapter 2–12 progression now supplies behavioral evidence for those targets.

## External chapter files and the Obelisk Chamber

The checkbox defaults to off unless a file request is already pending for this
loaded slot. A request stores both route and chapter, so restoring another route
cannot silently redirect it to a different chapter filename. It targets only the selected chapter. Changing chapter replaces
the pending request; reapplying with the box unchecked removes it. No file is
written by checking, Apply, Undo or Redo. Reload/discard drops unsaved requests.

At Save, the requested file uses the current staged chapter-start payload,
including subsequent ordinary edits made before Save. It is serialized in the
same container format as natural chapter files. A stale request whose payload
is no longer the matching entry is refused; reapply the chapter start to proceed.

All target existence checks and overwrite confirmations happen before writes.
Targets with competing dirty edits or duplicate requests are refused. The target
is checked again before replacement. Existing bytes are preserved by the normal
backup policy: `.bak` is the original, then `.bak1`, `.bak2`, etc.; the highest
number is newest. A matching latest backup can be reused. Backup failure prevents
replacement. Files are written through a temporary file and replaced atomically.

After creation, the chapter slot appears in the editor's slot list. A completed
request is consumed, including its history metadata: Undo after Save can undo
the selected save's payload but never deletes or silently rewrites the external
file. Check the box and Apply again for an intentional new checkpoint write.
If the chapter write succeeds but the selected-slot write fails, the error is
reported; retry saves the remaining slot without repeating the checkpoint write.
This is per-file recovery, not a multi-file transaction.

Obelisk discovery and loading passed for **Chapters 8 and 9**. Other chapter
files remain untested in the Obelisk, including all Cai files. The checkbox supplies the named chapter file; it does not synthesize files for
other skipped chapters, unlock the Obelisk facility, or recreate past campaign
progress. Internal restart snapshots and external chapter files are distinct.
The user observed that skips had not created new external files except 1_1 in
the earlier Chapter 1 test, despite rebuilt internal snapshots.

**Hypothesis, not confirmed:** external chapter-save creation happens at the
previous chapter's completion/boundary. An unrecovered action type 84 immediately
precedes title rows for Chapters 2–12; Chapter 1 has a different lead-in. This is
consistent with a boundary operation skipped by direct title entry, but it does
not prove type 84 writes files or establish the exact trigger. Explicit editor
file creation does not establish the natural trigger.

## Guards and history

Cai dates, capture evidence and the Route_Kai observation are detailed in
[Cai preparation and Test 1](story-cai-research.md). Neither live editing nor
chapter-file creation requires a Route_* file. The editor does not create one.

The engine requires a unique Header (220 bytes, marker 15), GameUserData v23,
agreeing route/part/chapter/sequence for Leda or Cai Part 1, and the recognized free-time or checkpoint
resume/state pair. GameSchedule and Calendar sizes/versions, matching valid
clocks and all eight restart members/blobs/checksums are checked before mutation.
Unknown and battle states are refused before traversing their variable objects;
refusal does not create an Undo entry. The Chapter 2 progression capture uses
context `12 06`, whose full tree is unsupported, so it stays read-only for story
editing despite having valid container checksums. A decoder recursion failure
is reported as a save-layout error rather than escaping into the story UI.

Restart editing uses the existing pointer-relocation engine. Every unrelated
root object and all other GameUserData bytes must match after pointer
normalization. Serialization derives chapter, sequence, state and clock mirrors
from the current payload so Undo after saving restores the complete summary.

Historical diagnostics remain reproducible: [Test 1](testing-story-progression.md),
[Test 2](testing-story-entry-test2.md), [Test 3](testing-story-resume-test3.md).
Their original sequence-only/probe functions are retained for research; the UI
uses `story_start`, never the failed selector-only writer.

## Remaining Cai test targets

Cai Chapter 1 uses the native `Chapter_Kai_1_1` date, **1449-01-24 02:00**;
it must not inherit Leda's 1444 prologue year. The other newly exposed dates
come from Cai's chapter-title rows. The original Chapter 1 checkpoint has no
free-time flags yet; a full captured flag-group signature allows the Sewers
prerequisite and tutorial list to be located without weakening the general
Functions guard. All chapter selections remain atomic.

[The next test kit](testing-cai-tutorials-test5.md) uses the native Chapter 1
checkpoint for C5-01, the original Chapter 2 Auto for the direct C5-04 retry,
and the successful Sewers arrival for later chapters. Every case is independent.
