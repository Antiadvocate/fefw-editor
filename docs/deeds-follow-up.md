# Follow-up: the 15 originally read-only Notable Deeds counters

**All 47 counters are now editable at the player's request.** The 14 remaining
counters are labelled **Inferred**, following the successful Hours experiment.
This register tracks their evidence and dependencies; it no longer requires
another individual test before exposing each control.

[HOURS-01–03](testing-deed-hours.md) passed the 17 → 20 edit, completion and
20-Karma claim. Both [returned saves](test-results-deed-hours-2026-11-15.md)
corroborate the result. The other counter families may use different game
updaters. Their new labels state that counter-only editing is an assumption,
not evidence that the associated story, ranks or conversations have changed.

## Order and case register

| ID | Counter | Evidence question / status |
|---|---|---|
| DEED-R14 | Hours played | Passed: 17 → 20 persists across short play and reload; completion/claim and +20 Karma verified. Later real-hour updates untested. |
| DEED-R01 | Livestock defeated in battle | Inferred — Does an isolated counter edit persist, show the right category and refresh completion?|
| DEED-R02 | Golden or silver mummies defeated | Inferred — Same test, independently from livestock; English name is already confirmed|
| DEED-R03 | Giant foes defeated (provisional translation) | Inferred — Confirm the English enemy category first, then test its counter|
| DEED-R04 | Blessings raised to level 2 | Inferred — Is this a recorded event total or recomputed from current blessing EXP?|
| DEED-R05 | Blessings raised to maximum | Inferred — Same distinction at maximum level; avoid changing audience flags|
| DEED-R06 | Skill levels raised to C | Inferred — Does a counter-only edit survive reload and a normal rank-up?|
| DEED-R07 | Skill levels raised to B | Inferred — Check whether the growth-counter assumption holds at B|
| DEED-R08 | Skill levels raised to A | Inferred — Same question at A; label extrapolation as inferred|
| DEED-R09 | Skill levels raised to S | Inferred — Same question at S; label extrapolation as inferred|
| DEED-R10 | Skill levels raised to maximum | Inferred — Verify separately; confirm the in-game rank wording|
| DEED-R11 | C support conversations viewed | Inferred — Distinguish event count from individual viewed-conversation flags|
| DEED-R12 | B support conversations viewed | Inferred — Verify separately from C|
| DEED-R13 | A support conversations viewed | Inferred — Verify separately from C and B|
| DEED-R15 | Paralogues cleared | Inferred — Determine whether the game derives this from quest/story completion|

## Evidence and later experimental groups

For optional follow-up verification, use a fresh copy for one counter at a time. Record the original total,
milestone claim states and Karma balance. Prefer an unclaimed next milestone
so the first experiment does not reset an already claimed reward.

1. Capture a natural before/after action where practical, including the
   underlying progress (unit rank, blessing EXP, viewed conversation or quest).
2. In a dedicated test build, edit only that counter. Save and reload in the
   editor, load in game and inspect the deed before doing another activity.
3. Save in game and compare both the counter and underlying source fields.
   If possible, perform one relevant normal action and compare again to detect
   recalculation. Persistence alone does not prove completion or eligibility.
4. Test one offered reward independently: record its amount, accept it once,
   save/reload and verify no second claim. Preserve other claims and currency
   except that exact intended reward.
5. Document the tested result and its limits. If extending that result to a
   group of similar counters, mark the extension as an assumption and retain
   a way to identify game recalculation or missing completion. Keep known
   derived totals read-only when their underlying progress must be changed.

The accepted unclaim warning applies to every newly editable counter.
Unknown stored states and ambiguous layouts remain protected. Direct claim
writes and changes to underlying story/support progression remain outside
this counter-only workflow. The user authorized this inferred rollout and
merge; additional game evidence is useful follow-up, not a release blocker.
