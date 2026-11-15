# Follow-up: the 15 originally read-only Notable Deeds counters

**Hours Played passed**, following the player's requested first experiment
after Boons. [HOURS-01–03](testing-deed-hours.md) tested DEED-R14 using a
17 → 20-hour counter edit. Both returned saves confirm persistence, completion
and the 20-Karma claim; see the [evidence](test-results-deed-hours-2026-11-15.md).
The supplied Test 1 build still labels Hours Experimental. The other 14 remain
read-only, and the accepted claimed-reward warning remains intact.

The user then wants to consider other game-wide counter Deeds using the Hours
result as a working assumption. The successful Hours test informs the next
experimental group, but is not proof that event totals, ranks, conversations,
blessings and story-derived totals share an updater. Label such extrapolation
as inferred and confirm representative game behavior before broad acceptance.

Recommended next group: the three enemy totals, which can build on the
existing ordinary/undead/beast counter workflow and this Hours result. Mark
newly exposed counters as inferred until their own evidence is available.
Then consider skill/blessing growth and support conversation totals, with
paralogues last because of their story relationship. Do not request individual
natural captures for all fields as a prerequisite to a labelled experiment.

## Order and case register

| ID | Counter | Initial question |
|---|---|---|
| DEED-R14 | Hours played | Passed: 17 → 20 persists across short play and reload; completion/claim and +20 Karma verified. Later real-hour updates untested. |
| DEED-R01 | Livestock defeated in battle | Does an isolated counter edit persist, show the right category and refresh completion? |
| DEED-R02 | Golden or silver mummies defeated | Same test, independently from livestock; English name is already confirmed |
| DEED-R03 | Giant foes defeated (provisional translation) | Confirm the English enemy category first, then test its counter |
| DEED-R04 | Blessings raised to level 2 | Is this a recorded event total or recomputed from current blessing EXP? |
| DEED-R05 | Blessings raised to maximum | Same distinction at maximum level; avoid changing audience flags |
| DEED-R06 | Skill levels raised to C | Does a counter-only edit survive reload and a normal rank-up? |
| DEED-R07 | Skill levels raised to B | Check whether the growth-counter assumption holds at B |
| DEED-R08 | Skill levels raised to A | Same question at A; label extrapolation as inferred |
| DEED-R09 | Skill levels raised to S | Same question at S; label extrapolation as inferred |
| DEED-R10 | Skill levels raised to maximum | Verify separately; confirm the in-game rank wording |
| DEED-R11 | C support conversations viewed | Distinguish event count from individual viewed-conversation flags |
| DEED-R12 | B support conversations viewed | Verify separately from C |
| DEED-R13 | A support conversations viewed | Verify separately from C and B |
| DEED-R15 | Paralogues cleared | Determine whether the game derives this from quest/story completion |

## Evidence and later experimental groups

Use a fresh copy for one counter at a time. Record the original total,
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

The accepted unclaim warning must apply to any newly editable counter. The
next build may expose an explicitly scoped inferred group; this acceptance
update enables no further fields. Direct claim writes and changes to the
underlying story/support progression are outside this counter-only workflow.
