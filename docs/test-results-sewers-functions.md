# Cai Sewers acceptance and Functions integration — 2026-11-16

The user confirmed that the one-record Sewers test fixed the Chapter 4
objective after natural Chapter 3 completion. Chapter 3 was fully completed.
The prerequisite is now exposed as **Functions → Area access → Sewers access
(Cai)**, with **Unlock tested** evidence. Disabling has not been game-tested.

## Returned evidence

Both supplied saves validate their container and payload checksums. Both retain
Cai Part 1 Chapter 4, 1449-03-01 15:00 and exactly one copy of the tested
`7d18367a` dialogue-history record with value 1.

| Capture | SHA-256 | Header resume context |
|---|---|---|
| Auto-arrival | `fd6b7904195f0a626303f19653459b789503bf2c55de64e1daa4090c78d8309d` | `12 05` |
| Auto-after-progress | `ddefc27a2390b729336bdae1d861f1ddb199148674960664c955d49212691565` | `12 06` |

The header sequence remains `d63bb68c219adbe2`; the changed resume context,
together with the user's report, records successful progression. Do not claim
a sequence-ID advance. The post-progress object tree is unsupported by the
current story writer; its existing read-only guard remains in force.

## Production behavior

- Cai selector: Chapters 2, 3, 4 and 9. Chapter 3 uses 1449-02-04 08:00.
- Every supported Cai target >=3 enables the prerequisite. The numeric rule
  applies to later targets when they are independently supported.
- Chapter 2 and Leda selections preserve its existing state. Other Functions
  switches, party units and earlier unlocks are not automatically granted.
- Chapter and prerequisite changes share one Undo/Redo action. Save writes the
  prerequisite to the selected slot and any requested Cai chapter file.
- Manual disable survives ordinary Save; choosing Chapter 3+ again enables it.
- A manually disabled prerequisite makes a pending Chapter 3+ checkpoint
  request stale, so Save asks the player to apply the chapter start again.
- The history member is selected by structural key `b631f2c1` inside the
  anchored general-flag group, never by map ordinal or the dialogue hash alone.
  Wrong-map same-hash records are preserved and never treated as this switch.
- General/history batches validate completely before mutation. Unknown values,
  duplicate keys, malformed or missing history members refuse the operation.
- Flags displays the new English name and preserves the exact original
  `MID_LGV_1KAI_c02_LG11_003_m06` identifier in Reads As.

Historical Test 1 and Chapter 3 probe generators remain reproducible and do
not retroactively include the new automatic prerequisite.

## Verification

- Public suite: 220 discovered, 170 passed, 50 private-data tests skipped.
- Focused private suite: 33 discovered, 30 passed, 3 unavailable-capture tests
  skipped. Includes native Cai checkpoints, both successful returns, the
  original Sewers probe, Leda preservation and primary entrance conditions.
- Label refresh reviewed: exactly the Sewers entry changes; label check passes.
- Live Tk checks pass: 37 switches; three Area access rows; Flags rightmost;
  toggle, Undo/Redo, disable + Save + reload; Cai 2/3/4/9 selector; automatic
  Chapter 3 prerequisite; identical valid Auto and Chapter_Kai_1_3 exports;
  backups/source preservation; dark/light layouts at 1000×640.

Chapter 4 remains a **conditional pass**: Sewers fixed on natural Chapter 3
progression. A direct Chapter 4 jump with this integration is not yet accepted
in-game. Cai Obelisk tests and Arena isolation remain deferred. No further
Chapter 9 battle playthrough is required for this change.
