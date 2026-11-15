# Polish Test 1: implementation validation

Candidate: **FEFW-Polish-Test-1**, branch `feature/polish-audiences`.
Exact commit and CI details are recorded in the delivered archive's `BUILD.txt`.
**In-game acceptance is pending** [POL, FTX and AUD cases](testing-polish.md).

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
