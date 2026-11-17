# Boons Test 4: skill-key correction and capture evidence

Date: 2026-11-15. **Test 4 bulk-max game acceptance passed.**
This supersedes Test 3's inferred full-name mappings for eight skill groups.
The original failed bulk test remains a failure, not retrospective acceptance.

## Player acceptance

The player reports “Everything is on and max!” and then confirms “Save/load
worked too”. This accepts the Test 4 bulk action on the tested setup: all
31 catalogue Boons display their maximum owned tier and On, and those states
persist through save/load, including the eight previously missing skill groups.

| Check | Result | Evidence |
|---|---|---|
| All Boons at maximum and On in game | Pass | Player report after Test 4 bulk max |
| States persist after save/load | Pass | Explicit player confirmation |

No new screenshots or game-resaved slot accompanied these confirmations, so
this is player-reported acceptance, not a new independent save comparison.
The earlier Brawling/Black-Magic captures remain the byte-level evidence.
This does not establish every gameplay effect, each intermediate tier, or
independent Off-toggle behavior for every group. The accepted baseline remains
Auto from B0-01-Unit-Selection-Test-1.zip; the all-max test is not promoted to it.

## Independent evidence

| Capture | Brawling level / Off | Black-Magic level / Off | Karma |
|---|---|---|---:|
| Before_Brawling | absent / absent | absent / absent | 410 |
| After_Brawling_On | 1 / absent | absent / absent | 110 |
| After_Brawling_Off | 1 / 1 | absent / absent | 110 |
| Before_Black_Magic | absent / absent | absent / absent | 410 |
| After_Black_Magic_On | absent / absent | 1 / absent | 110 |
| After_Black_Magic_Off | absent / absent | 1 / 1 | 110 |

Brawling records are level 45409cb9 and Off 79b46b58. Black-Magic records are
level 45227c65 and Off 79c9024c. These reproduce abbreviated names 技能経験格
and 技能経験黒 using the established level prefix and disable hash-state.
They are not the earlier proposed 39-/40-byte prefix truncations.

Both before files match the accepted B0-01 Auto byte-for-byte. All six containers
pass checksum/object-tree checks. Each purchase adds only its level record
across all parsed maps; each Off step adds only its disable marker. Gold 1523,
Renown 6640, parsed Deeds/tutorials/fast-travel/blessings and repaired unit
numbers match the baseline. Different container sizes do not establish further
intended edits. No raw saves or game binaries are published.

| Private file | Bytes | SHA-256 |
|---|---:|---|
| Before_Brawling; Before_Black_Magic | 39,549 each | 8675e054e082bd2b80cae318b9889326531d00f9fe3f8b366add5edf80de5663 |
| After_Brawling_On | 48,638 | 5913739433601e7d656d8c70d5d739b9f30333559a885d2aede52621b19ee37b |
| After_Brawling_Off | 45,781 | d88769c291b438300160f6f0be61b05fd0f3305d45736922810b69907fddda65 |
| After_Black_Magic_On | 48,637 | 9b60659f6ed1f98ec63f05434f9b2d72db407d1d181414a03048c7274fe36013 |
| After_Black_Magic_Off | 45,780 | eb696025aad254c8bf98bc99845f7c528308bdabcd2859a5abdd0bb6f75753e9 |

## Implementation and limits

Test 4 uses eight explicit skill aliases. Its shipped labels mark
Brawling/Black-Magic tier 1 Save-verified and other aliases/higher tiers Inferred.
The later player acceptance confirms the maximum-tier On result for all groups;
it does not add independent key captures for each group or validate every effect.
Other group names and the general identifier hash remain unchanged. The two
purchase captures do not establish a universal length cutoff. The all-group
menu/persistence report also covers groups outside the original failure images.

Incorrect Test 3 full-name records are ignored for ownership and preserved
byte-for-byte. They are not silently migrated, and removing a corrected record
does not revive stale ownership. Explicit tier changes or bulk max write the
corrected keys; recognized Off states are retained. Karma, progression,
numbered backups and the rightmost Flags tab are preserved.

## Validation

**All 116 tests passed locally**, including all private fixtures: 97 public and
19 opt-in private tests. Public CI skips private inputs. The actual Tk UI also
passed stale-Test-3 ownership display, Save-verified labels, Brawling tier/Off/On
writes checked against literal captured keys, Off persistence through save and
bulk max, filtered bulk max, Undo/Redo, save/reopen, numbered backups, mirroring
refusal and unchanged source/Karma. Flags remains last. English controls fit
inspected dark 1240×800 and light 1000×640 layouts; container font rendering
is not a Japanese-text acceptance check.

New public regressions use literal captured hashes and distinguish stale
Test 3 records from real ownership. Private tests load both three-save sets,
compare every parsed flag map and the listed preserved features, and check
editor-created level/On/Off changes against independent game maps. Editor
edits preserve normalized outside-map payload bytes and Karma, then serialize
and reopen with valid checksums. Input files remain byte-identical.

Set FEFW_SKILL_BOON_CAPTURE_DIR to the private directory containing the six
named captures, along with existing private-fixture environment variables
listed in the [Test 3 report](test-results-boon-levels-2026-11-15.md), and run
python -m unittest discover -s tests -v. Private tests skip without their inputs.

The [focused Test 4 game check](testing-boon-levels.md) is now complete on
the reported setup. Automated checks and player acceptance remain distinct
evidence; neither establishes every unmeasured gameplay effect.
