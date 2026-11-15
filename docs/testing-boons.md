# Boons Research 1: controlled save captures

This build adds a **read-only Boons tab**. It does not yet unlock, purchase,
activate or remove Boons. The purpose of this round is to identify those save
fields before enabling edits. Start with the known working EXP +10% Boon;
do not repeat the old guessed-flag edit.

## Setup

Use the reported Leda Part I Chapter 9 / fefw-recomp-0.1.5 environment. Note
any change of route, version or baseline. Extract the source ZIP to a fresh
folder and launch its `editor.py` in your working Python environment. The
header must say **Boons Research 1**; no new dependency is required.

Back up the **whole game save folder**, not just Auto. Boons might use shared
or global storage. Use a disposable copy/test profile and restore the whole
baseline between independent cases. Keep the accepted working save intact.
Leave route mirroring off. Do not edit counters, claim deeds, spend shards
elsewhere or advance the story during these captures.

For every named checkpoint, save in game, wait for saving to finish, quit and
copy the whole save folder to a ZIP with the checkpoint name. Include Auto,
the current Chapter slot, Global and Route files if present. Record which
slot you actually loaded. This lets us locate a change even if it is outside
Auto. Screenshots should show the Boon selection/state and Karma balance.

## Cases

| Case | Action | Expected result / evidence |
|---|---|---|
| **BOON-01 — Inspector** | Open accepted B0 in the new editor, then the Boons tab. Search `Experience` and `経験値`, select tier 1. Check normal/minimum window sizes and your current theme. | 81 reference tiers, 31 groups; B0 Karma 710; EXP-associated record `3b6429de` has raw value 1 with its meaning explicitly unconfirmed. First EXP tier lists value 10, cost 500, clear count 0. No purchase/activation buttons and no unsaved change from browsing. If using another baseline, record its actual balance instead of treating a different balance as failure. |
| **BOON-02 — Existing EXP activation** | From the disposable baseline, open Boons in game. Capture the existing EXP +10% state and checkpoint **B02-EXP-before**. If there is a separate disable/deactivate control, use only that, capture **B02-EXP-off**, then re-enable and capture **B02-EXP-on**. | Record the exact control wording, state markers and Karma at each checkpoint. No assumed state numbers. If there is no separate control, report **NO SEPARATE TOGGLE** with a screenshot and only the before checkpoint; do not try to remove it through Flags. This is a useful result, not a failed test. |
| **BOON-03 — One isolated purchase** | Restore the whole disposable baseline. Find the first **weapon discount** Boon (descriptive name; data says 10%, cost 300, clear count 0). Capture its actual English name, locked/unlocked state and price, then checkpoint **B03-purchase-before**. Buy only this one Boon. Capture **B03-purchase-after** before any separate activation action. If activation is separate, activate it and capture **B03-active-after**. | For a displayed price of 300, the balance should drop by exactly 300 (710 → 410 on B0). Record the actual price/balance if different. If it is already owned, unavailable, or costs more than the disposable balance, stop this case and send the screen; do not buy another tier or change unlock flags. If purchase activates immediately, report **PURCHASE ALSO ACTIVATES** rather than inventing an intermediate state. |
| **BOON-04 — Persistence** | Reload the post-purchase save, revisit the Boon, save/quit and capture **B04-reloaded**. Open that exact slot in the editor. | The purchased/active state and post-purchase Karma should persist in game. The editor may still show EXP candidate value 1: it does not map the weapon Boon yet. Include screenshots, the loaded slot and any automatic changes. Do not infer a working discount from the state marker alone. |

BOON-02 and BOON-03 are independent branches from the baseline, not one long
sequence. An unchanged save and the absence of an activation control are
both valuable evidence. Do not use the Player tab to top up shards for this
round; that would add another change to the comparison.

After these comparisons we will provide an editable build and an effect test
for the identified fields. A repeatable same-unit/same-action EXP comparison
or same-item/same-shop discount comparison belongs to that next round.

## Return template

```text
Build / commit:
Route / chapter / recomp version / OS (if changed):
Loaded slot:
BOON-01:
BOON-02: Toggle available / NO SEPARATE TOGGLE; control wording; balances
BOON-03: Actual Boon name, displayed price, purchase/activation behavior; balances
BOON-04:
Checkpoint ZIPs:
Screenshots / other actions / unexpected behavior:
```

The [read-only Deeds follow-up](deeds-follow-up.md) is queued separately;
none of those counter experiments are requested during the Boons captures.
