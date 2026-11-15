# Boons Research 1 — implementation checks

Date: 2026-11-15. This report covers the read-only inspection build, not
in-game acceptance of Boon editing. No purchase, activation or removal writes
are implemented.

## Automated checks

The public suite discovers 73 tests: 68 pass and five private-save tests skip
when their optional fixtures are absent. Five new Boon tests cover:

- The 31-group / 81-tier reference catalogue and the first EXP/discount costs.
- Absent, zero, positive and negative candidate values, without interpreting
  any value as purchased or active.
- Reordered maps, duplicate entries, sparse maps and ambiguous map layouts.
- Rejection of an unrecognised player resource header.
- English and original Japanese catalogue search.

Read-only observations preserve the payload bytes. The existing public
Tutorials, Blessings, audience, Fast travel and Notable Deeds tests also pass.
The release workflow includes the new JSON catalogue on both platforms; this
research delivery is a source ZIP, not a newly built executable release.

## Private-save inspection

The supplied B0 save reads Karma 710 and EXP-associated record `3b6429de = 1`.
The supplied post-claim save reads Karma 720 and the same candidate value.
Both pass the existing checksum verification, and inspection leaves their
payload bytes unchanged. These saves do not isolate a Boon purchase or
activation, so neither observation establishes the record's meaning.

No private saves, game binaries or screenshots are distributed with this
contribution. The catalogue contains derived reference metadata.

## Native interface checks

The new build was opened against a disposable copy of B0. Checks at 1240×800
and the 1000×640 minimum, in dark and light themes, confirmed:

- The Boons tab is reachable and shows 81 tiers, 31 groups, Karma 710 and the
  candidate's explicitly unconfirmed raw value.
- Ctrl+F filtering and single-row selection show the correct EXP and weapon
  discount reference details.
- The table, themed scrollbars and explanatory details remain visible.
- Browsing, selecting and changing theme leave the save unmodified.

The test desktop does not render the Japanese glyphs correctly; Japanese
search is covered by the automated test, while the player's normal font
environment still needs its usual visual check.

## Player results and controlled save comparisons

The player returned BOON-01 as **PASS**, supplied the BOON-02 off/on captures,
reported that the BOON-03 purchase **activates immediately**, and confirmed
BOON-04 persistence. This completes Research 1's inspection/capture round;
it is not acceptance of editor-written Boon changes or measured effects.
The previously reported environment is Leda Part I Chapter 9,
fefw-recomp-0.1.5 on Bazzite 45; no environment change was reported.

Six individual save containers and three screenshots were supplied. These
are not complete save-folder ZIPs, and the original loaded slot name was not
specified. Findings below apply to the supplied containers; cross-slot,
Global/Route storage and synchronization remain untested.

All six containers pass both header and payload checksum verification and
the structural shared-map locator. Both `before` files are byte-identical.
The records below are in the live shared map (enumerated map 6 in these
files); the implementation must continue using structural identification,
not this map index or a fixed offset. Every listed value 1 uses a compact
one-byte encoding. **Absent is record removal, not a stored zero.**

| Supplied checkpoint | Karma | EXP-associated `3b6429de` | EXP-off `6447f467` | Weapons Discount purchase-associated `5bfcaa34` |
|---|---:|---:|---:|---:|
| B02-EXP-before | 710 | 1 | Absent | Absent |
| B02-EXP-off | 710 | 1 | 1 | Absent |
| B02-EXP-on | 710 | 1 | Absent | Absent |
| B03-purchase-before | 710 | 1 | Absent | Absent |
| B03-purchase-after | 410 | 1 | Absent | 1 |
| B04-reloaded | 410 | 1 | Absent | 1 |

### BOON-02: existing Increased Exp 10%

The off/on screenshots show the 10% status and the `R OFF` / `R ON` control,
with Karma 710 in both. The left-hand row says **Increased Exp 20%** and is
locked: that is the next offered tier, not the currently owned 10% value.

The only named-flag change from `before` to `off` is addition of
`6447f467 = 1`; the only named-flag change from `off` to `on` is removal of
that record. `3b6429de = 1` remains unchanged throughout. This establishes a
separate **disable marker for the existing EXP Boon** on this setup. It rules
out interpreting `3b6429de` alone as the current activation state, but does
not independently establish the EXP purchase operation or higher-tier values.

### BOON-03: Weapons Discount 10% purchase

The only named-flag change across the purchase is addition of
`5bfcaa34 = 1`. Karma decreases by exactly 300, from 710 to 410, matching the
reference first-tier cost. The player reports immediate activation; the
screenshot shows **Weapons Discount**, status **10%**, `R ON`, and the next
20% tier locked. This confirms the official group wording and first-tier
purchase/activation observation. The new record is purchase-associated;
the combined action does not prove it is itself an activation flag.

No separate weapon-discount off-state was captured. Do not guess its disable
key from the EXP key or generalise this value to all Boons or tiers.

### BOON-04: reload

The purchase-associated record remains 1 and Karma remains 410 in
`B04-reloaded`, agreeing with the player's persistence report. The reload
also adds an unidentified `75060745 = 1` record in enumerated map 4, outside
the shared Boon map. Its meaning/cause is unknown; it is not classified as a
Boon dependency or copied into a future edit. All other named-map values
remain unchanged across this reload pair.

### Preservation checks and evidence limits

Across all six files, Gold 1523, Renown 6640, Divine Sand 100, all seven
blessing EXP/selection values, six first-audience records, tutorial records,
fast-travel records, and Deeds progress/claim records match the baseline.
This is a comparison of those parsed fields, not a claim that every payload
byte is unchanged. Normal game saves also differ in headers, schedule,
world state and embedded data; these captures do not identify the meaning of
every changed byte.

No repeated battle-action EXP measurement or same-item weapon-shop price
comparison was performed. A menu ON state and successful persistence do not
establish an effective numerical bonus. The current published research build
remains read-only and retains its conservative raw-value display.

## Next implementation scope

The next editable trial should start with **off/on for an already-owned
EXP +10% Boon**, using the observed disable record only, preserving its
ownership-associated record and currency. Require the observed state shape,
reject unknown values, preserve every unrelated record, and test undo/redo,
save/reload and an actual EXP effect in game. This is a planned control,
not a feature enabled by this report.

The first Weapons Discount purchase now has an isolated candidate record,
cost and persistence result. Its independent off/on mapping, editor-written
purchase/removal and actual shop-price effect still need separate trials.
No direct purchase, higher-tier or story-eligibility edits are accepted yet.

### Evidence fingerprints

Private save bytes and screenshots are not committed or distributed.

| Checkpoint | SHA-256 |
|---|---|
| B02-EXP-before / B03-purchase-before | `887b67b56d1abf3b94f7c194d063ba01d861208b3474bdcb957f5c419228734b` |
| B02-EXP-off | `c75344a3fc4008ea7d1cee25ed4964e0e74953c85392f6d808564321b1bc9727` |
| B02-EXP-on | `168f8a237a8565e94cfee05574e6fea7c4387f8f59c24b0fd9a0398710f6f4fa` |
| B03-purchase-after | `b014172b5e252855312d134898a6e83b9200f207a1a08448f7d6483c5969485f` |
| B04-reloaded | `177209065cbe2a0797200619873cca935167651d2bfad0bb2a2339bb4d7b0a51` |

The separate [15-counter Deeds follow-up](deeds-follow-up.md) is queued after
this milestone; its read-only fields have not been enabled by this build.
