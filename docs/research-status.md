# Save-editing contribution roadmap and evidence

This records a staged contribution based on a Leda Part I Chapter 9 restoration.

**All Deed counters enabled for main at the user's request.** The 14 formerly
restricted counters are labelled Inferred. Hours Played passed its 20-hour
completion, claim and reload checks; its [acceptance report](test-results-deed-hours-2026-11-15.md)
records the limits. See the [release scope](deeds-inferred-release.md).

Main merges now remove temporary header text and refresh English Flags names,
preserving Japanese originals in Reads As and Flags as the rightmost tab.
[AGENTS.md](../AGENTS.md) records these standing requirements.

**Tutorials and its English flag labels** are implemented and player-tested.
**Blessings EXP for all seven gods** is implemented and the BLESS-01–11
acceptance run passed on the reported Leda Chapter 9 setup; see
[the feature documentation](blessings.md), [test guide](testing-blessings.md)
and [test report](test-results-blessings-2026-11-15.md).
**Fast travel** now has a 16-destination tab and a visible **Open…** action;
its [game acceptance tests](testing-fast-travel.md) passed on the reported
Leda Chapter 9 setup. English names now match the supplied menu screenshots;
see the [evidence and coverage limits](test-results-fast-travel-2026-11-15.md).
**Polish Test 1** adds four experimental early-access destinations and six
first-audience controls. Fortuna has no audience condition. The player has
completed POL/FTX/AUD testing: audience controls have reported passes, all four
travel flags persist, and only Yu Phas Temple appeared at Chapter 9. See the
[evidence and limits](test-results-polish-2026-11-15.md#player-acceptance-and-supplied-saves).
**Polish Test 2** corrects that name and themes horizontal scrollbars; [POL-04–05](testing-polish.md) have now both passed.
**Notable Deeds Test 1** adds 350 mapped milestones, 32 editable activity
counters and 15 read-only counters. Claims and Karma Shards remain read-only;
[DEED-01–10](test-results-deeds-2026-11-15.md#player-acceptance-and-supplied-saves)
passed except DEED-06: the game cleared a claim after a decrease. Test 2 adds
a targeted OK/Cancel warning; [DEED-11–14](testing-notable-deeds.md) all passed.
The Notable Deeds milestone is accepted on the reported setup. Accepted audience/travel
controls lose Experimental labels; the three hidden destinations say Effect unknown.
**Boons Test 4** corrects eight skill-EXP save-key aliases after Test 3's
bulk unlock partly failed in game. Brawling and Black-Magic purchase/Off keys
are independently captured. The player now confirms all Boons are maximum
and On, with save/load persistence. See the
[investigation](boon-key-investigation.md) and [Test 4 report](test-results-boon-skill-keys-2026-11-15.md).
All 31 Boons / 81 tiers remain editable; EXP tier 1 and Weapons Discount tiers
1/2 have accepted game-effect evidence. **Bulk-max menu state and save/load
acceptance passed**; other gameplay effects and intermediate tiers remain
unmeasured. The B0-01 baseline is unchanged. Flags remains the rightmost tab.
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
| 4 | Notable deeds | 32 editable counters; 15 read-only; 350 milestones; claims/currency read-only | Training completion/+10 claim confirmed; decrease clears claims in game. [DEED-11–14](testing-notable-deeds.md) all passed; milestone accepted on the reported setup |
| 5 | Boons | All 31 groups / 81 tiers editable; broader mappings labelled Inferred | [BEDIT results](test-results-boon-editing-2026-11-15.md): +16 EXP Off / +17 On. [WEDIT-01–07 passed](test-results-weapon-boon-2026-11-15.md): discount Off/On persists in returned saves; player reports earlier 10% prices reproduced and backups through .bak4 |
| 6 | Story | Warning-gated Leda P1 starts 1–12; optional chapter file on Save with confirmation/backups | Chapters 4–12 passed [Tests 3](test-results-story-test3.md) and [4](test-results-story-test4.md). Chapters 1–3 and editor-created Obelisk files are Inferred; [Test 5](testing-story-test5.md) pending |

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

Audience/access flags are separate from blessing EXP. The exact keys include
`共有_行動_初めてマーズと話した` and `共有_行動_初めてカーラと話した`.
The six MIR audience-condition fields identify the new [audience controls](audiences.md).
Fortuna has an empty condition. Increasing EXP alone does not establish that a
god has been met or its menu unlocked. AUD-01–08 now have player-reported passes
on Leda Chapter 9. Mars has supplied Off/On screenshots and four save files:
portrait visibility differs, audience absence/1 persists, EXP stays 25 and
Divine Sand stays 100. His Off-after file stores selected=1 versus 0 before;
the On pair stays 0. The cause of that game-session change is not established.
The other five gods lack individual supplied evidence in this submission.

## Fast travel and facilities

The restored destination list was player-confirmed. World map shown/visited
bytes do not determine fast travel availability. Reconstruct the destination
catalogue from the recorded destination flags and verify each against the
in-game list; similarly named NPC/location flags are not interchangeable.
The [Fast travel page](fast-travel.md) implements those 16 exact scoped keys
plus four additional ones from the game data,
value 1 or record removal. It identifies the live flag-group map structurally,
preserves other records and refuses sparse/ambiguous saves. The original 16 English labels
are confirmed against the player's game-menu screenshots. Automated
remove/restore round-trips pass for all 16 in the private B0 reference.
The player reported OPEN-01–02 and FT-01–08 passed: individual game removal,
restoration, travel and persistence covered Port, Kalla's Temple and Stables.
The private FT-03/04 files independently confirm Port absent then restored,
all other destination records preserved, and stable-facility unlock absent.
The other 13 original entries have no isolated game edit/arrival test yet.
Four experimental destinations were tested in FTX-01–04. All four flags persist
in supplied before/after saves. Aurora's private room/garden and Salamis
Guesthouse did not appear in the Base Map list; their labels remain provisional.
**Yu Phas Temple** is the player-confirmed English name. It appeared, allowed
travel and walking out, but walking back in remained off limits. Its removed
file has no flag; disappearance from the game menu was not explicitly reported.
The original 16 remain the only map-identification anchors. These results do
not identify or bypass the remaining entry/visibility conditions.

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
The [Notable Deeds UI](notable-deeds.md) separates “complete but unclaimed” from “claimed” and preserves all claim states and Karma Shards. In this combined reference sequence,
390 + 820 deed rewards − 500 for EXP +10% = 710 Karma Shards. That arithmetic
supports the observation but is not an isolated reward-system test.

Some counters may be derived or recalculated. The visible played-hours counter
is not proof of a safe way to edit elapsed play time. Record the observed
counter, displayed threshold and claim state separately for every mapped deed.

DEED acceptance subsequently confirmed training 75 creates state 2 during the
load/menu check, and claiming changes 2 → 4 with Karma 710 → 720. Lowering
training to 40 caused the game to remove the 50-tier state 4, leaving an
incomplete 40/50 milestone. The editor now warns before an effective edit
leaves any claimed target unmet; it does not directly rewrite claims or currency.

## Boons of Salvation

The first attempt to write `因果報酬_経験値` (`7178d8f9`) did **not** unlock the
boon; the game discarded that record. It must not be used as a working preset.
After manually claiming deeds and purchasing/activating Increased EXP 10%, the
player's working save gained `3b6429de = 1` in the shared flag map (then map 6).
That is a **candidate**, since several actions occurred between the two saves.
Its symbolic name and ownership-versus-activation semantics remain unknown.

Data lists the EXP +10% reward at a cost of 500. Before implementing purchase writes,
obtain a disposable save immediately before purchase, one immediately after
purchase, and one after any separate activation action, with no other claims
or changes between them. Confirm the effect in a repeatable EXP comparison and
save/reload. Preserve the already working reference boon; do not repeat the
failed attempt on it. Other tiers need separate evidence.

The **Boons Research 1** tab and [reference documentation](boons.md) are now
implemented. [BOON-01–04](testing-boons.md) captures have now been returned;
the [comparison report](test-results-boons-2026-11-15.md#player-results-and-controlled-save-comparisons)
supersedes the earlier uncertainty about the EXP toggle:

* EXP off adds `6447f467 = 1`; on removes it. `3b6429de = 1` and Karma 710
  persist in both states. Ownership and activation cannot be represented by
  the older candidate alone; EXP purchase/higher-tier semantics remain untested.
* Purchasing **Weapons Discount 10%** adds `5bfcaa34 = 1`, spends exactly 300
  Karma (710 → 410) and activates immediately. The record and balance persist
  on reload. BEDIT-06 subsequently isolated a separate disable candidate,
  `ddb8d06b = 1` Off / absent On, with the purchase record and Karma unchanged.
* All six containers pass checksum checks. Known tutorials, travel, audiences,
  blessing values and Deeds records match the baseline. Reload also adds an
  unidentified `75060745 = 1` in another map; no dependency is inferred.

Only individual containers were supplied, so full-folder synchronization is
unverified. **Boons Test 1's existing EXP +10% toggle is now accepted** on the
reported setup. BEDIT-01–04/07 have reported passes and the returned saves
verify persistence. BEDIT-05 has matched starting states and Leda gains 16 EXP
Off versus 17 On after one reported kill and retreat; this does not establish
a general rounding formula. BEDIT-06's before file is unpurchased, followed by
purchased On/Off captures. After Armorer access was restored separately, the
follow-up On/Off/On screenshots show the same 10% listed-price reduction in
both On states. The final returned save has the purchase marker, no disable
marker and Karma 410; intermediate states were supplied as screenshots only.
Test 2's Weapons Discount control is now accepted: WEDIT-01–07 all passed by
player report. Four returned captures verify the exact editor-produced Off/On
payloads, game persistence and unchanged Karma 410. The player reports prices
matching the earlier comparison and backups from `.bak` through `.bak4`;
new screenshots and backup files were not supplied. The accepted baseline
remains the supplied B0-01 package's Auto. Exact symbolic identity, higher
tiers and fractional-price rounding remain unknown. See the
[Test 2 acceptance report](test-results-weapon-boon-2026-11-15.md).

The [locked Weapons Discount 20% experiment](testing-weapon-discount-20.md)
passed with screenshots and returned saves: level 2 persists, prices are
240/400 On and 300/500 Off, and Karma remains 410. Progression was unchanged.
The next 30% offer still shows Locked. General tier and activation editing is
now implemented at the user's request using the shared hash pattern. The
remaining groups are labelled Inferred; this does not claim every effect is
game-tested or that save-side purchase eligibility has been decoded. See the
[Test 3 results and limits](test-results-boon-levels-2026-11-15.md).

The Test 1 acceptance report records incidental baseline progression observations
that constrain the B05/B06 tests. The known feast unlock flag was already 1
in B0 and all four B05 captures. Personal save-restoration repair work is
tracked separately; these observations are not registered as editor defects.

## Deeds: inferred rollout enabled

All 47 counters are editable. [DEED-R01–15](deeds-follow-up.md) tracks Hours
acceptance and the remaining 14 inferred fields. Individual game outcomes are
still useful for refining those labels, but are no longer prerequisites to
exposing the controls. The claimed-reward warning and unknown-state guards
apply throughout. Editing a Deed does not edit its underlying story/support,
skill or blessing records.

## Story progress

A Chapter 2 base was reconstructed into Leda Chapter 9, and the player loaded
the scene, reached the Chapter 9 fight and continued. This confirms that
specific restoration, not a general chapter selector. Header chapter/route,
timeline, schedule, quests and facility availability can all need to agree.
Changing only a chapter number can produce the right label with the wrong
scene or roster.

The user requested a warning-gated Leda Part 1 selector and one test save per
chapter. [Story progression Test 1](story-progression.md) staged entries for
Chapters 1–12, refusing other routes/parts and inconsistent save fields. It
preserved all prior progression records, existing units and embedded snapshots.
UI01–06 passed, but all twelve progression cases failed. The writer was paused;
the [return report](test-results-story-test1-return.md) identifies
preserved resume state, schedule and an old Chapter 9 restart cache. Four
[Test 2 diagnostics](testing-story-entry-test2.md) isolating entry mode, restart
and date initialization at Chapters 4 and 9 did not establish working transitions.
[Test 2 returns](test-results-story-test2-return.md) narrow restart availability
but do not prove its exclusive data source. [Test 3](test-results-story-test3.md)
passed for Chapters 4 and 9 after adding the separate resume identifier. HubSeq
removal brought no benefit, so the editor retains it and uses the full D setup.
[Test 4](test-results-story-test4.md) passed all UI checks and the seven remaining
chapters. All 14 returned saves validate; Chapters 4–12 are now Game-tested for
opening and the next story beat. [Test 5](testing-story-test5.md) opens Chapters
1–3 as Inferred, with the natural Chapter 1 historical date and Chapter 2 date.
The optional chapter-file checkbox queues a same-state checkpoint for Save;
overwrite confirmation, numbered backups, cancellation/history and failures
have automated coverage. Obelisk loading remains pending in-game testing.

The user observed no new external Chapter_Led_ files except 1_1 in the earlier
Chapter 1 test. Creation at the previous chapter boundary is a hypothesis, not
confirmed behavior. Type 84 precedes Chapters 2–12 in the timeline, but its
function is unrecovered. Internal target restart snapshots do rebuild after
successful entry. The new explicit file-creation option does not depend on
identifying that natural boundary. The Obelisk warning now explains the option,
Save-only writes, existing-file confirmation and backups. No natural creation
trigger is claimed as confirmed.

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

## Facilities Test 1 accepted on the reported setup

FAC-UI01–05 and FAC-01–06 passed. Ten services and six gates are Game-tested;
Yu Phas's Conditional pass requires its ordinary Fast travel destination in
the tested setup. Ten untested services stay Inferred. The drinks-vendor
introduction after combined restoration is recorded as an observation, not an
isolated dependency. See [scope](facilities.md) and
[returned-save analysis](test-results-facilities-test1.md).

The user has now prioritized **Story progression** next: a warning-gated Leda
Part 1 chapter selector, with independent chapter-start saves for load and next
story-beat tests. It must not grant prior facilities, units, tutorials, travel,
quests or other progression. New-unit creation remains queued with the identity
validation requirements below. Main and the accepted baseline remain unchanged.

## Requested Facilities scope

Facility locking/unlocking follows the now-completed Deeds rollout.
Start with independently verified shop restrictions and distinguish service
availability, physical-entry conditions and fast-travel registration. The
previous shop and Gate of the Gods Kalla's Temple repairs motivate these
controls; those baseline repairs remain resolved, not new editor defects.
Preserve unrelated facilities, including the intentionally locked Stables.

## Feature backlog: create new unit entry

Requested on 2026-11-15 for prioritization. Unit creation remains queued after the now-prioritized Story progression
experiment; it is not part of the current Deeds release.

A new unit entry needs a unique `unit_number`. The earlier personal-save
restoration duplicated unit identities: selecting Catania selected Buccar,
and selecting Olympia selected Sirocco; cancelling a move could warp the
selected unit to the other unit's tile. The corrected baseline passed its
selection and save/load checks. This was a restoration issue, not evidence
that the editor already supports safe unit creation.

Implementation requirements:

- Check the full relevant unit table for occupied `unit_number` values,
  including entries not currently visible or recruited. Preserve existing
  identities and refuse ambiguous, invalid or exhausted allocation states.
- Allocate a new identity and audit dependent references when constructing
  the entry. Do not copy another unit's identity or rely on roster display
  order, character name or character hash as a substitute for `unit_number`.
- Validate the complete result before writing; preserve every existing unit
  and unrelated save record. Support Undo/Redo and normal backup behavior.

Required testing includes duplicate and boundary cases, repeated additions,
save/reopen and game save/load. In game, deploy original and newly added units
together and check selection, movement, cancellation and tile occupancy for
each, explicitly covering the earlier Catania/Buccar and Olympia/Sirocco
failure pattern. A parseable save or correct roster list alone is insufficient
acceptance. Use synthetic fixtures publicly and keep personal saves private.
