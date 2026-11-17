# Story Test 3 — Chapter 4/9 passes, 2026-11-16

The player reported successful results for **09D, 09E, 04D and 04E**.
The selected implementation is **D**, which retains HubSeq. E's removal produced
no observed benefit. This accepts the tested short-session transition from the
current baseline, not every source state or long-term campaign behavior.

| Cases | Player result |
|---|---|
| 09D / 09E | Opening plays; correct chapter-start location; baseline roster, facilities and fast-travel spots look accurate. July 12, 204 turns to the first main match. Skipping ahead starts the expected story fight. |
| 04D / 04E | Opening plays; correct location. Roster, facilities and registered travel spots look accurate. Travel itself is temporarily unavailable as expected for the story. March 1; Register for the heroic games, no deadline. Visiting the objective triggers the cutscene and resumes at the correct next point. |

## Returned evidence

The ZIP contains twelve files: Auto, Auto-after-restart and
Auto-after-advancement for each D/E case. All pass container checksums and object
tree parsing. Sources were read without modification.

- The ten non-battle returns retain the current party's nine person identities
  and unique unit numbers. All twelve retain the catalogued facility switches;
  registered fast-travel destinations also match the baseline.
- Chapter 4 starts at noon March 1 with sequence `d1b35c2f1820fdad` and advances
  to `d1b35c2f1820fdae` at 19:00.
- Chapter 9 starts July 12 in free-time sequence `d1a25c2f18128a5b` and advances
  to battle sequence `a27302ce5e5e5a75` on September 1 at 12:30. Those battle
  captures are correctly refused as story-edit sources. Their battle unit-number
  representation is not promoted as a decoded roster layout here.
- Every return has an internal chapter-start Data snapshot for the correct
  target, including the current nine-unit roster. Additional advancement
  snapshots appear as expected in the returned data.
- The separately named after-restart files have the correct target chapter and
  preserved current party. This is structural evidence; the player did not
  separately narrate every visual check after Restart.

## Interpretation and adopted behavior

Test 2 C failed. Adding the separate resume identifier in D succeeded for both
chapters. Removing HubSeq in E added no demonstrated value. The engine therefore
uses D, retaining its full tested combination of entry sequence, resume identifier,
state bytes, entry clock, empty schedule/calendar cache and empty restart slots.
No component other than HubSeq removal is dropped without further evidence.

The UI offers Chapters 4–12 with **4/9 Game-tested** and **5–8/10–12 Inferred**.
Chapters 1–3 remain unavailable. Source route/part and layout guards remain,
including refusal for the supplied Chapter 9 battle captures. The next kit
contains seven independent remaining-chapter cases from the unchanged baseline.

## External chapter-save observation

The user reported no new `Chapter_Led_` files from these skips, except 1_1 during
the earlier Chapter 1 test. The proposed explanation is creation at completion
of the previous chapter. This is recorded as a **hypothesis**. The private
Timeline report finds unrecovered action type 84 directly before every title
row for Chapters 2–12; Chapter 1 is preceded by type 3 with argument `1部開始`.
Those data support a separate boundary action, but do not identify its function.

The Obelisk warning remains directly above the backup instruction. No external
chapter files are fabricated. A future natural chapter-boundary comparison is
needed before claiming the exact creation trigger or implementing that behavior.

## Validation

The actual editor engine reproduces the delivered Chapter 4/9 D files byte for
byte from the accepted baseline. Automated checks cover all nine targets,
unchanged flags and unrelated objects, invalid/battle/other-route refusal,
idempotence, Undo/Redo and state/date summary restoration after saving.

138 public tests passed (173 discovered, 35 private checks skipped). A separate
30-test story run passed with all relevant private captures supplied. Live GUI
checks passed for the five-point warning, evidence-labelled 4–12 picker, Apply,
Undo/Redo, save/reopen, numbered backups, complete outer-summary restoration,
Cai/battle refusal, slot isolation, dark/light layout and Flags last.

Private captures and GameData remain outside Git. The historical failed cases
retain their failure reports; these passes do not retrospectively validate them.
