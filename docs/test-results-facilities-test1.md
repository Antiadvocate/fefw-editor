# Facilities Test 1 — preparation and evidence

Prepared 2026-11-15 from accepted main `da1486a` on
`feature/facilities-access`. **Player testing returned 2026-11-16.** FAC-UI01–05 and FAC-01–06 passed,
with the Yu Phas condition below. Main and the accepted B0-01 baseline remain unchanged.

## Implementation checks

- All **140 local tests passed**, including 117 public tests and 23 opt-in
  private-fixture tests. The facility additions cover all 27 controls in both
  directions, mixed inverse/positive selections, no-ops, wide and zero values,
  unknown-state atomic refusal, shifted/reordered/ambiguous maps, raw-record
  and outside-map preservation, container serialization/reopen and Undo/Redo.
- The running Tk interface passed all 27 toggle/Undo/Redo checks, search by
  English/Japanese/hash, category filtering, mixed selection, mirroring refusal,
  save/reopen, original backup and access-diagnostics copying.
- Flags remains last and visible at 1000×640. Dark 1240×800 and light 1000×640
  layouts were reviewed. The application header retains the clean product and
  upstream v1.3.9 version; Test 1 identifies this package and documentation.
- The known English flag dictionary was refreshed and its freshness check
  passed. Original keys were preserved.
- Thirteen private Auto files were generated and checksum-verified. Only the
  named switch/map records change. All paired restored/removed cases match the
  accepted baseline's complete raw flag-record maps. Stables and route Leda
  P1 Ch9 remain unchanged in every supplied case. The original baseline's
  bytes remain unchanged.

The public branch contains code, synthetic tests and documentation. The kit's
personal test-save copies and their manifests are supplied privately, not in
Git. A public pass does not establish game behavior for an inferred switch.

## Static access evidence

The reproducible report identifies 17 rows across 12 target labels. Relevant
source fingerprints (SHA-256):

| Personal source | SHA-256 |
|---|---|
| `HubDispos/Hub_000.bin` | `873b73807b308fc948812f84e8840ac526da9546122b9ab81639c0ac7de881a1` |
| `Hub.bin` | `eb728dfe433aea8346445e527b5e3456c4c82248cbc23cb48b8bb73312226a6a` |
| `Variable.bin` | `22b9946fe0781f0283fe4f15c84e6a86bbe2b076c47725da2896fd1c4b937321` |

The room/garden travel rows at `0x2dee80` / `0x2def30` require `KAI`; Salamis
at `0x2de900` requires `SEO`. Yu Phas at `0x2dfc40` has no protagonist filter.
The main-entrance and restriction rows, plus Aurora A60 condition variants,
are described in [facilities.md](facilities.md). These are observations from
typed game data, consistent with the earlier Leda outcomes. They do not prove
that every condition on every route/version has been exhaustively recovered.

## Player acceptance — 2026-11-16

| Tests | Reported outcome | Returned-save evidence |
|---|---|---|
| UI01–05 | Pass | Selection, editing, search/filter, undo/redo and persistence accepted by player |
| FAC-01 | Pass | Armorer and Item shop restrictions present in disabled case; absent in restored case |
| FAC-02 | Pass | Exams, drinks, local and tavern performance switches absent then 1 |
| FAC-03 | Pass | Marketplace, Inn, Blacksmith and Training switches absent then 1 |
| FAC-04 | Pass | Kalla gate registration absent then 1 |
| FAC-05 | Pass with Yu Phas condition | Six new gate registrations persist then are removed; Yu Phas additionally needs its ordinary destination recorded in the tested setup |
| FAC-06 | Pass | All four ordinary travel flags persist then are removed; no claim of bypassing route/entrance conditions |

All 12 returned case files and the extra Yu Phas save pass container checksums
and structural parsing. Every requested flag state persists. Each stays Leda
Part 1 Chapter 9, with Gold 1523, Renown 6640, Karma 410, Stables locked and
unique unit numbers `[47,48,1,2,3,4,5,6,7]`. Compared with the prepared cases,
unit stats/items/masteries, Boons, Deeds, Blessings, audiences and tutorials
are unchanged. The return files do not replace the accepted baseline.

Ten tested services and six gates now say **Game-tested**, scoped to this Leda
P1 Ch9 setup. Yu Phas says **Conditional pass**. The ten services not included
in these game cases remain **Inferred**. Broad route/version coverage is not
implied by these results.

### Yu Phas follow-up

The original gate case records `7d2c41eb = 1` but lacks ordinary temple travel
`65411bed`. Yu Phas is absent from the supplied six-entry gate-list screenshot.
The player then enabled **Yu Phas Temple** in **Fast travel**: the gate appeared
and its portal returned to the world map. The extra returned file records both
values as 1. Its SHA-256 is
`73bb2ac6707db02a0e161990b4ef448b072de13bf792d02b1bffabddee6f6e7a`.

There are four saved-flag differences from returned case 09: ordinary travel
is added; location flags `3c6b4ee1` and `bcd41adb` are removed; unidentified
`4cceb98e = 1` is added. This supports the successful combination, not proof
that the ordinary travel flag is the only possible dependency in every state.
Walking back into the temple is a separate, previously blocked condition and
was not reclassified by the portal test.

The editor now explains both switches in Yu Phas's row and read-only access
diagnostics. Enabling either switch does not silently change the other.

### Drinks-vendor introduction

The player heard the drinks-vendor introduction after restoring drinks and
tavern performance together; drinks alone had not replayed it in the earlier
repair. Returned case 04 has no flag-map differences from prepared case 04.
Record this as a dialogue observation: the combined action does not isolate a
trigger or establish a mandatory performance dependency. No dialogue flags
are written automatically.

### Other incidental save changes

Case 06 adds eight flag records during the game session: general-map
`39077a4b = 128`; another map's `1da84238`, `1da84239`, `1da8423a`, `7480a80b`,
`761be3f3`, `88880ef4` and `b9a1fd72`, all 1. Only the last has the recovered
key `MID_LGV_1_Dagsion_Hotel01_m01`; the others remain unidentified. Case 08
removes the Dagsion A1 location flag `3c6b4ee1`. No additional facility
requirement is inferred from these incidental changes.

Opt-in return regression checks use `FEFW_FACILITY_CAPTURE_DIR` with the twelve
numbered folders and `FAC-05_Yu_Pha`. Personal saves/screenshots are not in Git.

### Follow-up implementation checks

All **143 local tests passed** (118 public, 25 opt-in private), including the
13 returned captures, all four combinations of Yu Phas's two switches, unknown
values and unavailable maps. Read-only diagnostics preserve bytes. The running
UI passed guidance, selection/search/filter, Undo, save/reopen, backup,
mirroring refusal and small-window Flags visibility checks. English labels
are current. The release workflow now bundles the facility catalogue too.
