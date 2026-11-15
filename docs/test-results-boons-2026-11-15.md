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

## Next evidence

Run [BOON-01–04](testing-boons.md). Capture complete save folders around a
single purchase and, only if the game provides a separate control, activation.
An absent activation toggle is a valid observation. Actual names, eligibility,
purchase/activation storage and gameplay effects remain unconfirmed until
those comparisons and subsequent edit tests are complete.

The separate [15-counter Deeds follow-up](deeds-follow-up.md) is queued after
this milestone; its read-only fields have not been enabled by this build.
