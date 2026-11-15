# Facilities Test 1 — preparation and evidence

Prepared 2026-11-15 from accepted main `da1486a` on
`feature/facilities-access`. **Player testing is pending.** Main and the
accepted B0-01 baseline remain unchanged.

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

## Acceptance still required

[FAC-UI01–05 and FAC-01–06](testing-facilities.md) cover the new interface,
core lock/restore pairs, separate gate registrations, persistence and the
route-filtered travel comparison. Individual results and returned game-resaved
files will determine which evidence labels can be promoted. No arbitrary
route/story/door writes were introduced to force the hidden destinations.
