# Save-editing contribution roadmap and evidence

This records a staged contribution based on a Leda Part I Chapter 9 restoration.
**Tutorials and its English flag labels** are implemented and player-tested.
**Blessings EXP for all seven gods** is implemented and the BLESS-01–11
acceptance run passed on the reported Leda Chapter 9 setup; see
[the feature documentation](blessings.md), [test guide](testing-blessings.md)
and [test report](test-results-blessings-2026-11-15.md).
**Fast travel** now has a 16-destination tab and a visible **Open…** action;
its [game acceptance tests](testing-fast-travel.md) passed on the reported
Leda Chapter 9 setup. English names now match the supplied menu screenshots;
see the [evidence and coverage limits](test-results-fast-travel-2026-11-15.md).
Other sections below
are research notes and acceptance gates, not working UI features or
instructions to apply unverified offsets.

Evidence levels: **player-confirmed** means the observed restored save worked in
game; **structural** means supported by parsed data or a save comparison;
**candidate** means correlated but not isolated. A passing byte test does not
turn a candidate into a confirmed game feature. The tutorial acceptance run
passed on Bazzite 45 with `fefw-recomp-0.1.5`, Leda Chapter 9; see
[the test report](test-results-2026-11-15.md) for evidence and coverage limits.
The game data version was not separately reported.

## Delivery order

| Stage | Feature | Implementation boundary | Game acceptance test |
|---|---|---|---|
| 1 | Tutorials and known English names | Selected save only; preserve Japanese keys and unknown records | [TUT-01–07](testing.md) |
| 2 | Blessings | All seven EXP fields; six data-derived level previews; Fortuna special | [BLESS-01–11](testing-blessings.md) passed; see coverage limits in the report |
| 3 | Fast travel and Open button | 16 scoped Dagsion flags; confirmed English names; selected save only | [OPEN-01–02 and FT-01–08](testing-fast-travel.md) passed on Leda Chapter 9 |
| 4 | Notable deeds | Separate counter, completion and claim state | One incomplete, one complete-unclaimed and one claimed deed; verify rewards once |
| 5 | Boons | Confirm ownership and activation storage before enabling writes | Controlled purchase/activation diff, effect check and persistence |
| 6 | Story | Read-only summary first; narrowly validated Leda transitions only | Load scene, advance to battle, finish/save/reload with no missing facilities |

Each stage needs its own guide, technical layout, limitations and reproducible
test report before being called game-tested. Other routes are not covered by
the Leda restoration. Avoid “unlock everything” presets and arbitrary story
chapter writes until their dependencies are understood.

## Blessings

The restoration of Mars level 1 and Kalla level 3 was player-confirmed. The
observed live `GameUserData` child is an 88-byte object, including its pointer.
It was child 6 in the reference file; **child number is not a stable locator**.

| Offset relative to observed object | Observed content |
|---|---|
| +4 | Version byte 2 |
| +5 | u32 Divine Sand |
| +9 | Record count 7 |
| +10 | Seven 11-byte records: u64 MIR hash, u8 selected, u16 EXP |

Observed order: Fortuna (labelled Photon in Test 1), Mars, Credna, Kalla, Jurah,
Smyrnos, Aurora. Preserve
selection and sand unless explicitly edited by a future separately validated
control. Mars, Jurah and Smyrnos thresholds in data are 25/60/120; Kalla and
Aurora 20/50/100; Credna 15/40/80. Fortuna has zero-valued threshold fields and
no established EXP progression. The reference used Mars EXP 25 and Kalla EXP
100. All seven are editable. The six ordinary gods each displayed level 2 at
the tested EXP (Mars/Jurah/Smyrnos 61, Credna 41, Kalla/Aurora 51); the supplied
case files retain those values. Kalla's decrease from level 3 also worked.
Fortuna EXP 1 persisted, with no noticeable in-game change reported. The player
also reported no noticeable Blessings-screen change at maximum stored EXP
(65535); that follow-up value and its persistence have not been independently
checked from a supplied save. Full
threshold-boundary sweeps, other routes/versions and Fortuna's field semantics
remain unverified; these results do not establish that every EXP value is safe.

Audience/access flags, including `初めてマーズと話した` and
`初めてカーラと話した`, are separate from blessing EXP. Increasing EXP alone is
not evidence that a god has been met or its menu unlocked.

## Fast travel and facilities

The restored destination list was player-confirmed. World map shown/visited
bytes do not determine fast travel availability. Reconstruct the destination
catalogue from the recorded destination flags and verify each against the
in-game list; similarly named NPC/location flags are not interchangeable.
The new [Fast travel page](fast-travel.md) implements those 16 exact scoped keys,
value 1 or record removal. It identifies the live flag-group map structurally,
preserves other records and refuses sparse/ambiguous saves. All English labels
are confirmed against the player's game-menu screenshots. Automated
remove/restore round-trips pass for all 16 in the private B0 reference.
The player reported OPEN-01–02 and FT-01–08 passed: individual game removal,
restoration, travel and persistence covered Port, Kalla's Temple and Stables.
The private FT-03/04 files independently confirm Port absent then restored,
all other destination records preserved, and stable-facility unlock absent.
The other 13 entries have no isolated game edit/arrival test yet.

The exam proctor, drinks vendor and Perform quest tab also worked after the
restoration. These could become small facility controls once their precise
dependencies are documented and tested independently. Stables were intentionally
left locked in the reference save; a future preset must not unlock them as a
side effect. Inventories remain outside this contribution's requested scope.

## Notable deeds

The player confirmed progress values, then manually claimed the completed
deeds and supplied a new save. Comparing that save established:

| Meaning | Observed representation | Confidence |
|---|---|---|
| Progress | `実績_<counter>` records | Player-confirmed restoration of the supplied counters |
| Complete, reward not claimed | Milestone state value **2** | Player-confirmed |
| Reward claimed | Milestone state value **4** | 79 state transitions in supplied before/after saves |
| Milestone names | `実績状態_<group>`, then `_1`, `_2`, etc. | Structural; map each tier explicitly |

The counter map's enumerated index shifted between saves. Do not hard-code list
8 or 9. Missing zero counters are not necessarily malformed. Many guessed
display flags were discarded by the game; they should not be recreated merely
because their names look plausible.

A claim-state edit is not proven to award currency or update every dependency.
The future UI must separate “complete but unclaimed” from “claimed”, and must
not silently grant Karma Shards twice. In this combined reference sequence,
390 + 820 deed rewards − 500 for EXP +10% = 710 Karma Shards. That arithmetic
supports the observation but is not an isolated reward-system test.

Some counters may be derived or recalculated. The visible played-hours counter
is not proof of a safe way to edit elapsed play time. Record the observed
counter, displayed threshold and claim state separately for every mapped deed.

## Boons of Salvation

The first attempt to write `因果報酬_経験値` (`7178d8f9`) did **not** unlock the
boon; the game discarded that record. It must not be used as a working preset.
After manually claiming deeds and purchasing/activating Increased EXP 10%, the
player's working save gained `3b6429de = 1` in the shared flag map (then map 6).
That is a **candidate**, since several actions occurred between the two saves.
Its symbolic name and ownership-versus-activation semantics remain unknown.

Data lists the EXP +10% reward at a cost of 500. Before implementing writes,
obtain a disposable save immediately before purchase, one immediately after
purchase, and one after any separate activation action, with no other claims
or changes between them. Confirm the effect in a repeatable EXP comparison and
save/reload. Preserve the already working reference boon; do not repeat the
failed attempt on it. Other tiers need separate evidence.

## Story progress

A Chapter 2 base was reconstructed into Leda Chapter 9, and the player loaded
the scene, reached the Chapter 9 fight and continued. This confirms that
specific restoration, not a general chapter selector. Header chapter/route,
timeline, schedule, quests and facility availability can all need to agree.
Changing only a chapter number can produce the right label with the wrong
scene or roster.

Start with a read-only summary and evidence-backed Leda checkpoints. Keep other
routes read-only until paired saves and gameplay tests establish transitions.
Do not present an arbitrary skip as safe merely because the container parses.

## Other candidates and known limits

* **Met characters:** `面識` flags are distinct from support points and roster
  membership. Non-party support-list visibility still needs a controlled test.
* **Leda's unique abilities:** earlier attempts were not confirmed correct;
  retain this as unresolved, not a completed feature.
* **English names:** preserve exact original keys in Reads as. Add official
  names supported by screenshots/data; keep uncertain translations labelled
  as uncertain. Stage 1 covers 115 tutorial names; stage 3 adds the 16
  screenshot-confirmed English destination names.

No personal save, screenshots containing personal data, or game binary belongs
in the public test fixtures. Use small synthetic payloads for CI and record
private game-test outcomes separately.
