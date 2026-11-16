# Story progression — Leda Part 1

Player → Story progression… offers chapter starts **4–12** after the requested
five-point warning. Chapters **4 and 9** passed opening, correct location and
next-story-beat tests from the accepted Chapter 9 baseline, with the reported
roster/facility/travel state preserved. Chapters **5–8 and 10–12 remain Inferred**
and await [Test 4](testing-story-start-test4.md). Chapters 1–3 are deferred.

See [Test 3 results](test-results-story-test3.md) for the accepted short-session
scope. This is not a full save reconstruction or a long-term compatibility claim.
Other routes/parts, battle saves and unsupported or inconsistent layouts remain
read-only. The editor checks actual save contents, not filenames or party members.

## Using the editor

1. Open a disposable, supported Leda Part 1 free-time or chapter-start save.
2. Turn off route mirroring, then click Story progression… on Player.
3. Read the warning and back up the whole save folder into a fresh directory.
4. Continue to the chapter list. Each target carries its evidence label.
5. Apply stages the chapter start/date on the selected save. Ctrl+S writes it;
   Ctrl+Z/Ctrl+Y undo/redo the full change. Numbered backups remain available.
6. In the game, use Continue/Auto to test the new entry, then let its opening run.

Cancellation changes nothing. Reapplying an identical staged entry is a no-op.
Changing chapters after staging another entry is supported. Undo is confined to
its loaded save object; it cannot overwrite another slot or a reloaded object.

The warning title remains **CAUTION - UNEXPECTED CONSEQUENCES POSSIBLE**. It
retains the user's points about Leda Part 1, no previous unlock/unit grants,
limited testing, the Obelisk Chamber and a fresh-directory backup. The Obelisk
point is immediately above backup. The evidence note identifies Chapters 4/9
as tested and the other targets as inferred, and mentions clock/restart reset.

## What is changed

`story_start.edited` reproduces the successful **Test 3 D** setup. Its Chapter
4/9 payloads and serialized files match the delivered D candidates exactly.
Removing HubSeq brought no observed improvement, so it is retained.

| Saved component | Chapter-start edit |
|---|---|
| Header, GameUserData and outer summary | Target chapter and chapter-entry sequence |
| GameUserData v23 body+58, u64 | Separate resume identifier: `d8588d186b3f9502` → `a2f3e9a7ff461708` |
| Header state bytes, block+20/+21 | Observed chapter-start context `10 0b` |
| Header and GameSchedule clocks | Selected title-row date/time, retaining the source year |
| Remaining GameSchedule / Calendar cache | Empty checkpoint form, retaining known version markers |
| Eight internal restart slots | Validated Header/Data blobs cleared; the game rebuilds a target checkpoint during entry |
| Outer raw+48..56 | State/clock mirrored from the current payload during serialization, including after Undo |

All current flag maps, units and unique unit numbers, inventories, currencies,
Boons, Deeds, supports, facilities and fast-travel registrations are preserved
by the edit. Hub/location, world-map and conversation records are also retained;
the game's chapter scripts establish the new live scene. Those scripts may
apply chapter-specific restrictions or changes. Chapter 4's temporary fast-travel
restriction was reported as expected story behavior.

The D profile includes all the date, schedule and restart preparation from
Test 2 C. The tests isolate the additional resume identifier against that setup;
they do **not** establish that the identifier alone is sufficient on an otherwise
untouched save. Exact runtime enum/type names are still unrecovered.

## Target dates and evidence

| Chapter | Entry date/time | Short-session evidence |
|---|---|---|
| 4 | March 1, 08:00 | Game-tested opening/location/next beat |
| 5 | April 6, 12:00 | Inferred; pending |
| 6 | May 8, 12:00 | Inferred; pending |
| 7 | May 28, 20:00 | Inferred; pending |
| 8 | June 29, 11:00 | Inferred; pending |
| 9 | July 10, 18:00 | Game-tested opening/location/next battle |
| 10 | September 28, 02:00 | Inferred; pending |
| 11 | October 16, 12:00 | Inferred; pending |
| 12 | November 7, 12:00 | Inferred; pending |

The opening can advance the clock: Chapter 9 settles on July 12; Chapter 4's
returned opening saves are March 1 at noon. These entry dates come from title
rows in `Timeline_Part1_Led.bin`, SHA-256
`8fd921c3dd2ca18af17fa54f22fd3b99fadbaffdacfcc28f8ef377435caab5d5`.
The game data is not bundled or required at runtime. Reproduce the read-only
report with `python research/story_timeline_report.py /path/to/GameData`.

Chapter sequence hashes remain the independently matching Chapter 1/2 FNV-1
suffix pattern, with prefix state `fde8dadc5dfc1118` and suffix `<chapter>_1`.
Chapter 9's entry is `b79bcc2aad7433e5`. The full symbolic key is unrecovered;
real Chapter 4/9 progression now supplies behavioral evidence for those targets.

## External chapter files and the Obelisk Chamber

The editor only changes the selected save; it does not synthesize, overwrite or
remove external `Chapter_Led_` files. The user observed that the skip tests did
not create new chapter files, except `Chapter_Led_1_1` during the Chapter 1 test.
Internal restart snapshots were rebuilt in successful Test 3 returns despite
this absence of newly created external files. These are distinct observations.

**Hypothesis, not confirmed:** external chapter-save creation happens at the
previous chapter's completion/boundary. An unrecovered action type 84 immediately
precedes title rows for Chapters 2–12; Chapter 1 has a different lead-in. This is
consistent with a boundary operation skipped by direct title entry, but it does
not prove type 84 writes files or establish the exact trigger. Keep the Obelisk
warning and investigate a natural boundary before adding checkpoint creation.

## Guards and history

The engine requires a unique Header (220 bytes, marker 15), GameUserData v23,
agreeing route/part/chapter/sequence, and the recognized free-time or checkpoint
resume/state pair. GameSchedule and Calendar sizes/versions, matching valid
clocks and all eight restart members/blobs/checksums are checked before mutation.
Unknown and battle states are refused; refusal does not create an Undo entry.

Restart editing uses the existing pointer-relocation engine. Every unrelated
root object and all other GameUserData bytes must match after pointer
normalization. Serialization derives chapter, sequence, state and clock mirrors
from the current payload so Undo after saving restores the complete summary.

Historical diagnostics remain reproducible: [Test 1](testing-story-progression.md),
[Test 2](testing-story-entry-test2.md), [Test 3](testing-story-resume-test3.md).
Their original sequence-only/probe functions are retained for research; the UI
uses `story_start`, never the failed selector-only writer.
