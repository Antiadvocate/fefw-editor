# Save-editing contribution roadmap and evidence

This records a staged contribution based on a Leda Part I Chapter 9 restoration.
Only **Tutorials and its English flag labels** are implemented by this branch.
Other sections below are research notes and acceptance gates, not working UI
features or instructions to apply unverified offsets.

Evidence levels: **player-confirmed** means the observed restored save worked in
game; **structural** means supported by parsed data or a save comparison;
**candidate** means correlated but not isolated. A passing byte test does not
turn a candidate into a confirmed game feature. The reference game's exact
version and runtime should be recorded with the next testing report.

## Delivery order

| Stage | Feature | Implementation boundary | Game acceptance test |
|---|---|---|---|
| 1 | Tutorials and known English names | Selected save only; preserve Japanese keys and unknown records | [TUT-01–07](testing.md) |
| 2 | Blessings | EXP first; show derived level only for verified thresholds | Change one blessing, reload, inspect EXP/level and other blessings |
| 3 | Fast travel | Named destination flags, separate from map visibility | Add/remove one destination, travel, save/reload; check gates/map unchanged |
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

Observed order: Photon, Mars, Credna, Kalla, Jurah, Smyrnos, Aurora. Preserve
selection and sand unless explicitly edited by a future separately validated
control. Mars thresholds observed in data are 25/60/120; Kalla 20/50/100.
The reference used Mars EXP 25 and Kalla EXP 100. Other gods' level thresholds
need checking before a derived level is presented as authoritative.

Audience/access flags, including `初めてマーズと話した` and
`初めてカーラと話した`, are separate from blessing EXP. Increasing EXP alone is
not evidence that a god has been met or its menu unlocked.

## Fast travel and facilities

The restored destination list was player-confirmed. World map shown/visited
bytes do not determine fast travel availability. Reconstruct the destination
catalogue from the recorded destination flags and verify each against the
in-game list; similarly named NPC/location flags are not interchangeable.

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
  as uncertain. Stage 1 covers the 115 tutorial names only.

No personal save, screenshots containing personal data, or game binary belongs
in the public test fixtures. Use small synthetic payloads for CI and record
private game-test outcomes separately.
