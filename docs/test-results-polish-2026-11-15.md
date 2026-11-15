# Polish builds: validation and player acceptance

Candidate: **FEFW-Polish-Test-1**, branch `feature/polish-audiences`.
Exact commit and CI details are recorded in the delivered archive's `BUILD.txt`.
The initial implementation checks below precede the
[player acceptance and supplied saves](#player-acceptance-and-supplied-saves).
Polish Test 2 contains the resulting name/theme fixes; its exact commit and CI
run are in that build's `BUILD.txt`.

## Scope

* Retains accepted Open, Tutorials, EXP and original 16 destination features.
* Includes eight player-confirmed English destination corrections.
* Adds four explicitly experimental Dagsion entries, with provisional labels.
* Adds six identified first-audience flags in Blessings. Fortuna's empty
  condition is displayed as Not required; no flag/control is invented for her.
* Shows a build label and adds horizontal scrolling to the wider Blessings table.

The four destination keys exist verbatim in the local Timeline_Com data and
their destinations/locators are represented in Hub data. All four are absent
from the private FT-04 save. The six audience keys are the MIR condition fields
in the local Skill table; B0 contains Mars/Kalla at 1 and the other four absent.
This establishes identity and observed storage, not early-access behavior.

## Automated checks

`python -m unittest discover -s tests -q`: **50 public tests pass**, with four
private-fixture cases skipped when no private save is configured.

`FEFW_TEST_SAVE=<private B0> python -m unittest discover -s tests -q`:
**54 tests pass**. The source file is read-only throughout. Temporary writes
are isolated and deleted by the test harness.

Coverage includes:

* Every one of the 20 destinations added/removed/restored from its initial
  state, serialized, reopened and checksum-verified on the private fixture.
* Every one of the six audience flags tested off/on and restored, preserving
  unrelated shared-map records byte-for-byte, including unknown records.
* Audience changes preserve all other payload content after normalization of
  relocatable pointers; EXP/selection/Sand, tutorials and travel are also
  checked explicitly after serialization. The other payload comparison covers
  story, facilities, deed claims, currency and world-map data.
* Unknown-state, duplicate, sparse, ambiguous and wrong-parent map rejection;
  invalid IDs/values and Fortuna writes rejected atomically; wide records and
  no-ops preserved; all six audiences can be removed without losing the map.
* The four experimental destinations cannot replace the original three
  required locator anchors. UI edit/undo/redo, cache refresh, mirroring refusal,
  no-op handling and rejected-checkbox reset are tested.

`git diff --check` passes. No private save, screenshot or game dump is included
in public fixtures or the source archive.

## Native interface check

On an isolated B0 copy, the desktop application launched with the new build
label, seven audience states and checkbox form. Mars's checked state changed
to Not recorded; Undo restored the row and checkbox, with EXP still 25.
Fortuna's checkbox was disabled with its explanation. Fast travel showed
16/20, four experimental entries, 14 other records preserved, and all four new
rows initially Absent. Scrollbars and the new columns were visible at 1240×800.

The test desktop's font configuration did not render Japanese/Unicode labels
correctly, including unchanged existing labels; Japanese legibility on the
player's setup and minimum-window sizing remain part of POL-01. No game was
run here, and no first-audience gameplay effect or new destination arrival is
claimed. Other routes, earlier save layouts and game versions remain unverified.

## Player acceptance and supplied saves

Reported 2026-11-15 on the existing Leda Part I Chapter 9 /
`fefw-recomp-0.1.5` setup. The player reported POL-01, POL-02, AUD-01–08 and
POL-03 passed. POL-01 also identified an unthemed horizontal scrollbar;
the supplied screenshot shows the bright strip beneath Fast travel.
Polish Test 2 applies the same palette styling as the vertical scrollbar to
both orientations, in both themes, and corrects Yu Phas Temple's English name.

### Travel results

| Case | Destination | Player observation | Supplied-save verification |
|---|---|---|---|
| FTX-01 | Aurora's garden | No Base Map entry appeared | Flag remains 1 before/after |
| FTX-02 | Aurora's private room | No Base Map entry appeared | Flag remains 1 before/after |
| FTX-03 | Salamis Guesthouse | No Base Map entry appeared | Flag remains 1 before/after |
| FTX-04 | Yu Phas Temple | Entry appeared; travel and walking out worked; walking back in remained off limits | Flag remains 1 before/after; absent in the supplied removed file |

All nine travel files have valid container checksums. For each before/after
pair, the entire travel map's raw records are identical, including other
destinations and unknown entries. Audience values, tutorial values, blessing
EXP/selection and Divine Sand also match across those pairs. This is not a
claim that the rest of each game-written save is byte-identical.

The first three English labels remain provisional and their additional
visibility conditions are unidentified. No usable travel access was established
for them. Yu Phas Temple's name is confirmed by the player's report; its
walk-in restriction still applies. The removed file establishes stored absence,
not independently confirmed disappearance from the game menu. All four remain
experimental and excluded from the map-identification anchors.

### Audience results

AUD-02–07 were all reported passed. Detailed evidence was supplied for
**AUD-02 (Mars)** only: Off/On screenshots and four before/after saves.

| Variant | Audience before → after | Mars EXP | Mars stored selection before → after | Divine Sand |
|---|---|---:|---|---:|
| Off | Absent → Absent | 25 throughout | 0 → 1 | 100 throughout |
| On | 1 → 1 | 25 throughout | 0 → 0 | 100 throughout |

All four files have valid checksums. Each before/after pair retains the entire
shared audience map's raw records, its travel list, tutorial values, all
blessing EXP values and Divine Sand. The screenshots show Mars's portrait
obscured Off and visible On, both at Bless Lv 1. They support an observed
portrait-visibility effect, not a claim that temple entry or every blessing
action is unlocked.

Mars's stored selection changes only in the Off-after game-written file.
The supplied screenshots both show Selected 2/4; the relation between that
count and the changed stored value is not established. We cannot attribute
the change to game recalculation versus an action during that session. The
editor's audience mutation does not write selection, and automated tests
separately verify that preservation before the game runs. Do not describe
this submission as proving selection stays unchanged after loading the game.
The two before saves are not otherwise byte-identical after normalization,
so they are not treated as a perfectly isolated binary A/B pair.

The other five ordinary gods have reported passes, without individual
files/screenshots here; their per-god visible effects remain unspecified.
Fortuna's disabled control passed AUD-08. No other route, chapter, version or
maximum-EXP effect was established by this run. All private files were read
without modifying them and remain excluded from the public repository/archive.

## Polish Test 2 follow-up

The only requested player retests are [POL-04 and POL-05](testing-polish.md):
scrollbar appearance/operation in both themes and the corrected label.
No save-format or flag-editing logic changed in this follow-up.

The public suite passes again (50 passed, four private-fixture cases skipped).
The native interface was checked at 1100×780: both tabs' horizontal bars follow
dark/light theme changes, and dragging the Fast travel thumb scrolls the table.
Player-side appearance remains POL-04 because platform rendering can differ.
All 13 newly supplied saves passed checksum verification during read-only
analysis. Previous private mutation round-trip results remain as recorded above;
they were not rerun for this theme/label-only update.
