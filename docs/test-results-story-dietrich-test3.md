# Dietrich Test 3 acceptance and unavailable chapters — 17 November 2026

The player reports that all three Chapter 2 diagnostics failed. Direct entry
for Chapters 5 and 6 passed. The supported Dietrich Part 1 selection is now
**Chapters 3–12**, all backed by the reported opening/next-story-step checks.

Chapters 1 and 2 are unavailable as chapter-entry targets. Chapter 1's battle
and transition previously passed, but it leads directly into the unresolved
Chapter 2 rescue block. Keeping it selectable would lead players into the same
known failure. The unchanged native Chapter 2 control passed in Test 2; that
is not evidence that replaying Chapter 2 from an advanced save is repaired.

## Returned evidence

All seven files in `FEFW-Dietrich-Story-Test-3-test-saves-return.zip` pass
container/payload checksums and Header/GameUserData/outer-summary mirrors,
including the saved clock. The original uploaded archive remains unchanged.

| Case | Player result | Returned evidence |
|---|---|---|
| D3-02A | Failed | Candidate boolean absent; rescue history retained; sequence remains `e2e7a46c9f3deb7e` |
| D3-02B | Failed | Boolean and rescue history absent; same blocked sequence |
| D3-02C | Failed | Boolean, rescue history and timestamp absent; same blocked sequence |
| D3-05 | Passed | Direct entry advances from `e2d6a46c9f2f782d` to `424543f0f58e7cd9` |
| D3-06 | Passed | Direct entry advances from `e2d9646c9f314102` to `423b03f0f585bb94` |

The intended edits persisted in all three Chapter 2 returns. Their failure is
not explained by the game silently restoring the candidate records. This
rules out those precise removal sets as sufficient repairs; it does not prove
that the candidate records are irrelevant in every context.

The Chapter 5 and 6 progression returns use valid event context `12 04`.
Story editing keeps those event resumes read-only; they are not corrupt.
Chapter 6 retains its intentional upper movement restriction and the three
function unlocks; the lower restriction is absent. Its original test input
added no Shopping Street fast-travel flag. The integrated entry paths for
5/6 are now accepted, replacing their previous pending labels.

## Selection and safeguards

- Dietrich offers only Chapters 3–12. Both the UI action and production entry
  API refuse 1/2 with the reason; a stale pending chapter-file request is also
  rejected before saving. The picker automatically selects Chapter 3 when
  the loaded save is Chapter 1 or 2.
- Existing native Chapter 1/2 saves still load and validate normally. They may
  be used as sources for a supported target. They are not deleted or rewritten
  merely because these destinations are unavailable.
- Chapter 5 removes the upper movement restriction; Chapter 6 removes the
  lower restriction and enables upper/lower access plus Vandahl Trading Company;
  Chapter 7 adds its accepted secret-teaching permission. Party and tutorials
  remain preserved. No new Chapter 2 flag or recruitment edits are applied.
- Leda and Cai selections are unchanged. Theodora remains read-only.
- Historical research builders retain the original Chapter 1/2 dates and
  sequence paths to reproduce the old test cases. These are not offered by
  the production selector.

## Remaining research

Party/recruitment state is a plausible untested difference between the working
native control and an advanced replay. Other trigger state may also be involved.
Neither has been isolated sufficiently to justify a production reset or unit
removal. Do not describe Esmerelda's presence as the confirmed cause.

Further work would benefit from inspecting the trigger implementation or a
controlled natural before/after capture around the rescue, to identify the
exact state it consumes. Investigation is parked; no more blind flag resets or
player tests are requested for this milestone.

All earlier UI and Chapter 3–12 checks retain acceptance. Obelisk use and
full-campaign progression remain untested. This change does not merge to main.
