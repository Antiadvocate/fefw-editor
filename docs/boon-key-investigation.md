# Boon save-key investigation

Date: 2026-11-15. **Test 4 bulk-max game acceptance passed:** the player
confirms all Boons are maximum and On, and save/load retains those states.
Brawling and Black-Magic keys also have independent purchase/toggle captures.

## Test 3 failure

Screenshots after Set all to max showed EXP 50%, Sword/Spear/Axe/Bow +3,
and Weapons/Items/Gifts discounts 30%. Brawling, Black-Magic, White-Magic,
Infantry, Rider, Heavy, Flier and Authority remained +0 with tier 1 offered
for 300. These are menu observations, not measurements of every effect.
The original synthetic tests read back their own inferred keys and therefore
could not establish that the game recognized those records.

All catalogue names match Reward.bin. Longer keys correlated with failure,
prompting a length-limit hypothesis. The first 39-/40-byte candidate hashes
did **not** match the later captures. No general hash or UTF-8 truncation rule
is established or implemented.

## Isolated game captures

Two independent three-save sets start from the accepted baseline. Both before
files match it byte-for-byte. Each purchase spends 300 Karma (410 → 110) and
adds one level record; Off adds one marker while retaining level 1.

| Group | Catalogue name | Name reproducing both captured keys | Level key | Off key |
|---|---|---|---|---|
| Brawling | 技能経験格闘 | 技能経験格 | 45409cb9 | 79b46b58 |
| Black-Magic | 技能経験黒魔法 | 技能経験黒 | 45227c65 | 79c9024c |

The level uses low 32 bits of FNV-1 64 over UTF-8 因果報酬_レベル_ followed
by the abbreviated name. Off continues low-32-bit FNV-1 state a21ab2b4 over
the same name; the original prefix text is unknown.

This supports explicit skill aliases without identifying every runtime naming
detail. Six further aliases were inferred: 白魔法→白, 歩兵→歩, 騎兵→騎,
重装→重, 飛行→飛 and 指揮→指. Each retains the 技能経験 prefix. The later
player report confirms their maximum-tier On result and persistence. It does
not independently isolate each key or toggle. Long blessing-cost names remain
unchanged and are included in the all-group menu/persistence report.

## Test 4 behavior

The editor reads and writes corrected keys. Old Test 3 full-name skill records
no longer appear as ownership and are preserved without automatic migration
or deletion. Set all to max explicitly writes corrected records and preserves
recognized game On/Off states. It does not charge Karma.

Brawling and Black-Magic tier 1 display **Save-verified**, separate from the
EXP/Weapons **Game-tested** effects. Six inferred aliases and untested higher
tiers retain **Inferred**. Tests compare literal captured identities and game
maps rather than only a shared read/write derivation.

See the [capture and acceptance report](test-results-boon-skill-keys-2026-11-15.md)
and [completed Test 4 procedure](testing-boon-levels.md). No further captures
are required to close this bulk-max test. Gameplay effects beyond prior accepted
EXP/Weapons tests remain unmeasured. The accepted baseline is unchanged.
