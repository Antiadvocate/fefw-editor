# Boons Test 1 — implementation validation

Date: 2026-11-15. This report describes the first editable Boon candidate.
Player acceptance of the edited saves and numerical effects is **pending**;
Research 1's captured game states are documented separately in the
[original report](test-results-boons-2026-11-15.md).

## Scope

Only the observed existing EXP +10% state can be switched Off/On. Off adds
shared record `6447f467 = 1`; On removes it. The ownership-associated record
`3b6429de` must already be 1. Its value, currency and every unrelated record
are preserved. Other tiers, unknown values, purchases and other Boon edits
remain unavailable. The two screenshot-confirmed group names are displayed,
with original descriptive and Japanese searches retained.

## Automated checks

**81 tests passed locally with the private fixtures supplied:** 75 public
checks and six optional private tests. Without private fixtures, the suite
discovers 81 tests, passes 75 and skips six. No private save or game binary is
included in the repository or source ZIP.

The new public tests cover:

- Repeated off/on changes, preserving currency, ownership, other records and
  their byte encodings, plus normalized bytes outside the resized map.
- Missing/zero/unknown ownership, unknown disable states, invalid requests,
  sparse/ambiguous/duplicate maps, wrong ancestry and unrecognized headers.
- Byte-identical no-ops, including an existing wide disable marker; stored
  zero remains distinct from absence and cannot be silently normalized.
- Real page-handler edits, undo/redo, current-payload validation after cache
  replacement, disabled higher-tier/other-Boon selections, mirroring refusal
  and no history/dirty entry for a rejected or unchanged action.
- Search by screenshot-confirmed, descriptive and Japanese group names.

The existing five private regression tests also passed for Tutorials,
Blessings, audiences, Fast travel and all 32 editable Deeds counters.

## Six-capture validation

The new optional private test reads B02-EXP-before/off/on,
B03-purchase-before/after and B04-reloaded. For each of the six files it
writes each requested EXP state to a temporary file, then reloads it.
All twelve outputs pass header/payload checksum verification.

Before serialization, only the disable record and object-tree relocation
change. After save/reload, the resulting shared-map values exactly match the
original map with just that marker added/removed. Every other shared record,
Karma, tutorials, travel, Deeds progress/claims, all seven blessing EXP and
selection values, and Divine Sand are preserved. Original input bytes remain
untouched. These are structural checks, not proof of a game bonus.

## Native interface validation

The running editor was checked using a disposable copy of B02-EXP-before:

- Dark theme at 1240×800 and light theme at the 1000×640 minimum: table,
  horizontal scrollbar, selected details and action buttons fit.
- Selecting the first EXP tier enables only the state-changing action;
  selecting tier 2 disables both actions.
- Off, Undo to On and Redo to Off refresh the displayed state and buttons.
- Save followed by Reload retains Off and Karma 710. The output independently
  reloads with valid checksums and the expected marker.
- Enabling route mirroring blocks the action with a warning and leaves the
  saved state unchanged. Mirroring was disabled after the check.
- Searching `Weapons Discount` returns the three reference tiers without
  edits; first-tier purchase observation and higher-tier mapping are separate.

This desktop's existing font setup does not render Japanese/some Unicode
glyphs correctly. Japanese search is covered by the automated checks; the
player should check appearance in their own environment as before.

## Player testing

Run [BEDIT-01–07](testing-boon-editing.md) on disposable saves. The essential
new evidence is editor-generated Off/On persistence and an actual EXP gain
comparison. A separate in-game Weapons Discount off/on capture supplies the
next mapping; its editor control has not been implemented. No repeat of the
accepted Deeds suite is requested. The 15 read-only counters remain queued.
