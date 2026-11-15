# Follow-up: test the 15 read-only Notable Deeds counters

**Queued at the player's request, after the Boons milestone.** The existing
EXP Boon toggle is now accepted. This is a
separate second Deeds pass; the accepted 32-counter workflow stays accepted.
No controls are enabled by this plan. Do not run these cases yet: each needs
a specific disposable baseline and an individually reviewed test build.

**Player clarification (2026-11-15):** wait for that build before testing
counter edits. This register is the development backlog, not a checklist
to complete in the current read-only UI. Natural before/after gameplay
captures are optional research; none are requested during the Boons round.
The first dedicated build will expose the selected counters and provide
numbered instructions, then later batches will cover the remaining fields.

## Order and case register

| ID | Counter | Initial question |
|---|---|---|
| DEED-R01 | Livestock defeated in battle | Does an isolated counter edit persist, show the right category and refresh completion? |
| DEED-R02 | Golden or silver mummies defeated | Same test, independently from livestock; English name is already confirmed |
| DEED-R03 | Giant foes defeated (provisional translation) | Confirm the English enemy category first, then test its counter |
| DEED-R04 | Blessings raised to level 2 | Is this a recorded event total or recomputed from current blessing EXP? |
| DEED-R05 | Blessings raised to maximum | Same distinction at maximum level; avoid changing audience flags |
| DEED-R06 | Skill levels raised to C | Does a counter-only edit survive reload and a normal rank-up? |
| DEED-R07 | Skill levels raised to B | Verify separately; do not infer from C |
| DEED-R08 | Skill levels raised to A | Verify separately |
| DEED-R09 | Skill levels raised to S | Verify separately |
| DEED-R10 | Skill levels raised to maximum | Verify separately; confirm the in-game rank wording |
| DEED-R11 | C support conversations viewed | Distinguish event count from individual viewed-conversation flags |
| DEED-R12 | B support conversations viewed | Verify separately from C |
| DEED-R13 | A support conversations viewed | Verify separately from C and B |
| DEED-R14 | Hours played | Determine whether the game derives this from its underlying play-time fields |
| DEED-R15 | Paralogues cleared | Determine whether the game derives this from quest/story completion |

## Evidence required before enabling each counter

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
5. Document the counter-specific result, dependencies and limits. Enable only
   counters whose evidence supports an independent edit. Keep derived totals
   read-only when changing their source progress is required.

The accepted unclaim warning must apply to any newly editable counter. No
bulk unlock of these 15 counters, direct claim writes, or story/support flag
changes are part of this follow-up without separate evidence.
