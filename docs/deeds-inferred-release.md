# All Deed counters and main-merge cleanup

Date: 2026-11-15. The user authorized all remaining counters as **Inferred**
and requested merging into their main branch.

## Behavior

All **47 counters / 350 milestones** are available in Notable Deeds. The
14 newly enabled counters are labelled Inferred in the editing column and
explained in the selected-row note. The existing 32 counters stay available;
Hours Played retains its accepted 20-hour test and a note about untested
higher milestones and later natural hour updates.

| Newly enabled group | Counters |
|---|---:|
| Livestock, golden/silver mummies, giant foes | 3 |
| Skill growth to C, B, A, S and maximum | 5 |
| Blessing growth to level 2 and maximum | 2 |
| C, B and A support conversations viewed | 3 |
| Paralogues cleared | 1 |

Each edit changes only one Deed total. It does not grant Karma, write claim
states or change underlying quest completion, conversations, skills or
blessings. Bounds, unknown-state refusal, structural checks, the claimed-target
warning, Undo/Redo and mirroring refusal remain in place. Inferred does not
mean that each counter's game behavior or reward has been individually tested.

## Release presentation and standing merge rules

The header now shows the product and upstream v1.3.9 without test wording.
Flags remains rightmost. All known Deed progress/claim labels, tutorial names,
travel names, audience names, Boon tier/disable names and the identified shop,
Kalla gate and Stables names are applied consistently to the Flags catalogue.
English is shown in Name; original Japanese identifiers are shown in Reads As.
The unknown original Boon-disable prefix is not fabricated: those entries have
English descriptions but blank Reads As. Unknown flags retain their raw names
or hashes. No saved flag value changes as a result of this naming cleanup.

`flag_labels.py` provides the common overlays used by the running editor and
`build_flag_names.py`. `--refresh-labels` updates the shipped dictionary without
requiring a game dump, and `--check-labels` checks it without changing files.
CI runs that check. [AGENTS.md](../AGENTS.md) records the user's requirements
for this and every future merge into main.

## Validation and acceptance limits

All 128 local regressions passed: 107 public tests and 21 private-fixture
checks. Real Tk checks passed edits to all 14 inferred counters, claim
preservation, Undo/Redo, save/reopen, original backup, claim-risk cancellation
and mirroring refusal. The clean header, final Flags tab, English/Japanese/hash
searches and exact Reads As identifiers passed. Dark 1240x800 and light
1000x640 layouts were reviewed. The flag-label freshness check passed.

The new regressions exercise every inferred counter, ensuring other records,
claims and bytes outside the Deeds map are preserved; missing-zero/no-op
behavior, bounds and unknown-state refusal still hold. A support-counter UI
test covers claim-risk cancellation and Undo/Redo. Flags tests check all
catalogue overlays, captured Boon aliases, unrecovered-name handling, conflict
refusal, and English/Japanese/hash searches through the actual row renderer.

The [Hours acceptance](test-results-deed-hours-2026-11-15.md) remains the game
evidence for the new inference. This release does not claim additional game
passes. Private saves are not included in the repository or source package.
The accepted B0-01 baseline remains unchanged.
