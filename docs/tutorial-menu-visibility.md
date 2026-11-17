# Tutorial categories and menu visibility — 17 November 2026

The player tried enabling only the 38 provisional tutorial records plus both
mouse tutorials in an old Leda Part 1 Chapter 9 save. The same behavior occurred
before and after the performance changes. This investigation corrects catalogue
and UI claims; it does not change the tutorial-map writer or force game menus.

## Reported results and inspected saves

Both attached containers pass checksums and parse as Leda Part 1 Chapter 9.

| Capture | Stored records | Observed menu |
| --- | --- | --- |
| First pass | 112: 38 scenario, 2 mouse, 72 other records; 111 at value 2 and Obelisk Chamber at 1 | All includes ordinary non-battle entries; Battle shows only the two mouse entries |
| Second pass | Exactly 40: all 38 scenario records and the 2 mouse entries, all at value 2 | All shows the mouse entries and Free Time |

The second capture differs in tutorial state only by removing the 72 extra
records: no additions or changed values among retained keys. Free Time is absent
from the attached second file. The player then confirmed that its tutorial
popped up on loading the save, naturally unlocking it. The second edit therefore
has the exact intended stored selection; gameplay can add tutorials again.

The first capture alone cannot establish whether its 72 other records were
retained during editing or reintroduced in game. Filtered selection/removal
intentionally preserves records outside the selection. No fault in the byte
writer or performance cache was reproduced.

## Category evidence

The first child record in each Tutorial/Tutorial_P0 group has a u32 at +32.
Cross-checking all 218 identities gives:

| Value | Editor category | Entries | Evidence |
| --- | --- | --- | --- |
| 1 | Battle | 45 | Matches screenshot category |
| 2 | Bases | 48 | Matches screenshot category |
| 3 | The World Map | 30 | Matches screenshot category |
| 4 | Dungeons | 10 | Matches screenshot category |
| 5 | Flame Lords | 47 | Matches screenshot category |
| 6 | Scenario-specific | 38 | Separate data value; absent from tested menus |

All 38 provisional names belong to value 6. Assigning them to Battle by their
position in the source table was incorrect. Scenario-specific is an editor
description, not an established in-game category title. Neither save-state 2
nor naming evidence proves menu visibility. Whether these entries are displayed
during their associated scenarios remains unverified; no additional flags or
guessed state values are written to try to force that behavior.

## Correction and checks

- Catalogue records now carry the verified numeric category. The report checks
  it against source data; categories 1–5 and all original identities stay intact.
- UI uses **Stored (2)** / **Add to save** and explains menu eligibility and
  natural unlocks. Counts distinguish saved records inside and outside filters.
- Filtered deletion tests preserve other categories, exercise Undo/Redo, and
  check the remaining count. A full selection test produces exactly 38 scenario
  and 2 mouse records while preserving unrelated flags and the input payload.
- Private checks use both captures for edit/restore, compression/checksum
  roundtrips and preservation. Personal saves, screenshots and game binaries
  are not included in Git or the source-only correction package.
- Full regression run: 259 tests, 204 passed and 55 skipped for unavailable
  historical fixtures. Supplied game tables and Cai kit sources were included.
  English label refresh/check and diff checks pass. UI controller tests run
  without a display; no live Tk visual check was performed in this environment.

This is a correction to editor labels and feedback, not a claimed in-game
visibility unlock. The user has already supplied the decisive 40-record case;
no repeat chapter or 38-entry visibility test is required for this correction.
