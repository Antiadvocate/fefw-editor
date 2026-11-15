# Boons Test 3: all catalogue tiers

**Known issue:** the general bulk unlock failed in game for eight skill-EXP
groups. Do not repeat Set all to max expecting those entries to unlock. The
editor's inferred state is not authoritative for those groups. The
[focused capture request](boon-key-investigation.md) replaces a broad retest
while the key derivation is investigated.

Extract FEFW-Boons-Test-3.zip into a fresh folder and launch its editor.py with
the working Python environment. No new dependencies are needed. The header
shows **v1.3.9 · Boons Test 3**, and **Flags is the far-right tab**.

Open a copy of your save, turn off **Also edit this route's other saves**, and
open **Boons**. The package contains no personal saves. The accepted B0-01
package Auto remains the reference baseline; WD20 captures are test evidence.

| Control | Behavior |
|---|---|
| Set selected tier | Sets the selected group's owned tier to that row; can raise or lower it, including before normal purchase requirements |
| Remove Boon | Removes that group's owned level; preserves its independent On/Off marker |
| Turn on / Turn off | Changes activation for the currently owned tier; select its row first |
| Set all to max | Sets all 31 groups to their catalogue maxima, including groups hidden by search; preserves existing On/Off switches |
| Undo / Redo | Restores one complete action, including a bulk edit |
| Save | Writes the selected save and uses the upstream numbered backups |

To unlock every tier, use **Set all to max**, review the states, then **Save**.
If a Boon was already Off, it stays Off: select its owned maximum-tier row and
choose Turn on if desired. Removal followed by re-adding also retains the old
switch state. No Karma is spent or refunded and no progression is changed.

The table shows **Not owned**, **Below tier N**, **On/Off**, or an unknown value
that must be preserved. Unknown levels or switch values block that group;
an unknown group blocks bulk max rather than partially applying it. Valid
unrelated groups remain individually editable.

**Game-tested** means EXP tier 1 or Weapons Discount tier 1/2. **Inferred**
means the shared level and activation-key patterns were extended to that row.
Automated checks cover all 81 tier choices, but the remaining gameplay effects
have not been individually verified. Required clears and Game cost are reference
purchase requirements; they are not a decoded save-side Locked/Unlocked state.

WD20 is complete; there is no repeat of its price/reload or earlier battle and
baseline-repair tests requested. For a quick check of this broader build, load
a disposable edited copy, inspect the Boons menu, save/reload and note any
missing or reset tier. A game-resaved copy would help diagnose any discrepancy.

See [the evidence and validation report](test-results-boon-levels-2026-11-15.md)
and [format documentation](boons.md).
