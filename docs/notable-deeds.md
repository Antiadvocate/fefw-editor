# Notable Deeds: progress and claim states

**Notable Deeds** provides a searchable table of **350 milestones across
47 mapped counters**. **32 activity counters** can be edited, one at a time.
The other 15 are read-only. The player completed the first [DEED acceptance
run](test-results-deeds-2026-11-15.md#player-acceptance-and-supplied-saves). Training
completion and a +10-shard claim worked. Lowering training below a claimed tier
caused the game to remove that claim, so **Test 2 adds an OK/Cancel warning**.
The player subsequently reported **DEED-11–14 all passed** on 2026-11-15,
completing acceptance of this milestone on the reported Leda Chapter 9 setup.
This does not expand the tested counters, routes or versions.

## Use

1. Open a copied save and turn off **Also edit this route's other saves**.
2. Open **Notable Deeds**. Search by activity, category, Japanese key, counter
   hash, milestone hash or target. Ctrl+F focuses search.
3. Select a milestone. The form shows its **whole activity total**, exact
   counter key/hash, allowed range and any read-only reason.
4. Enter **New total**, or click **Use selected target** to fill the input.
   Filling the input does not edit the save. Click **Apply progress**. If the new
   total leaves any previously claimed tier below target, an **OK/Cancel**
   warning lists the affected targets. Cancel is the default and makes no
   deed edit or undo entry. OK applies the counter edit. Then
   **Save** / Ctrl+S. Ctrl+Z/Ctrl+Y undo/redo; Reload rereads the saved file.
5. Load the exact edited slot in game and check progress. Claim rewards in
   game. The tested training counter refreshed completion on the reported load/menu
   check; a natural threshold-crossing training action also worked. Other
   milestones may have additional refresh or visibility conditions.

One counter feeds every tier for that activity. Editing the 75-training row
changes the training total, including progress shown against the 10–100 tiers.
The table caps each progress fraction at its target; the form always shows
the uncapped stored total. **Reached** is only a mathematical comparison.
Changing an existing total to zero keeps the record; missing zero totals are
normal and a zero-to-zero action does not manufacture a record.

## What each column means

| Field | Meaning |
|---|---|
| Activity · milestone target | Concise English description and target; not a verbatim game-text catalogue |
| Progress | Counter compared with this tier's target; may differ from the game's currently refreshed display |
| Karma Shards | Reward amount from the mapped data; not currency granted by the editor |
| Claim state (stored) | The actual milestone flag, independent of the displayed progress |
| Counter editing | Editable or Read-only; select the row for the reason |
| Reads as · milestone key | Original Japanese milestone key, preserved exactly |
| Milestone hash | Stable low-32-bit hashed identity |

| Stored state | Display | Interpretation |
|---|---|---|
| No record | Not stored | No saved claim-state record; does not by itself mean locked or incomplete |
| 2 | Complete, unclaimed (2) | Observed complete milestone whose reward was not yet claimed |
| 4 | Claimed (4) | Observed after claiming the reward in game |
| Anything else, including 0 | Unknown (value); preserved | Semantics unknown; associated counter editing disabled |

**Every claim state is read-only here.** This tab neither creates completion
flags nor marks rewards claimed, grants Karma Shards, changes Boons, or resets
claims when progress is reduced **in the editor**. However, the game can remove
those claims on loading: the supplied 65 → 40 training test cleared the
50-training claim and displayed incomplete 40/50, while Karma stayed 710.
A stored Claimed (4) label before loading does not prevent this game behavior.
The confirmation text is “You are about to unclaim some previously claimed
rewards. Continue anyway?” and shows which claimed targets exceed the new total.
It is only shown for an effective, valid edit. Meeting a target exactly or
reducing progress without leaving any claimed target unmet does not prompt.
No-op, invalid and read-only attempts do not prompt. This check also covers an
existing inconsistent claim when an increase still leaves its target unmet.
Undo/Redo restore the approved editor state; they do not undo game actions.
Do not use the generic Flags tab
to substitute guessed completion/visibility edits for this workflow.

## Planned second pass

At the player's request, [DEED-R01–15](deeds-follow-up.md) queues controlled tests
for every read-only counter after the Boons milestone, starting with the three
enemy counters. These fields stay read-only until their individual results
support enabling them.

## Coverage and limits

Editable counters cover base activities, spending, ordinary/undead/beast
kills, avoided attacks, critical attacks, assists, Blaze Arts, gambits, Support
Salvation, skirmishes, clashes, links, searches, rare search materials, feasts,
local performances and ore. The complete catalogue below specifies each one.

Read-only: paralogues, three support conversation ranks, five skill growth
ranks, two blessing growth counters, play time, and three insufficiently
confirmed enemy categories. The first eleven may depend on underlying
progress. Play time may be recalculated from elapsed time. The giant-enemy label remains provisional; livestock and golden/silver mummy
names are confirmed by the DEED-08 screenshot, but their editing is untested. Raw EXP edits elsewhere do not
prove that a growth deed counter can independently reproduce those changes.

Edits are bounded to **0 through the last mapped target**, or through the
current stored total if that is higher. Existing higher totals can be retained
or reduced, not increased further. Negative stored totals are preserved and
read-only. This bounds input; it does not prove that every value is game-tested.

The catalogue may show later, hidden or otherwise condition-dependent tiers.
It is not an unlock-all list. Other counters present in the file remain
untouched. Other routes, earlier chapters and game-data versions need their
own tests. A sparse or ambiguous save is read-only rather than guessed.

## Evidence and binary layout

The source research mapped records in `Reward.bin`: 350 rows for these 47
counters, within the observed row region `0x120..0xaaf0`, stride 104. Group key
pointer is at +8, counter key pointer +48, signed target +60, u16 reward +64.
Blank group names continue the previous group with successive `_1`, `_2`, etc.
These are **dump offsets**, not portable save addresses. The distributed JSON
contains only selected identities, numeric facts and our concise labels; no
source dump or private save is shipped. Each tier's identity is explicit and
hash-validated, never inferred from its English name at edit time.

The original restoration set both counters and milestone state 2. The player
reported the progress correct but rewards unclaimed, then claimed them in
game. A supplied comparison showed **79 milestone states changing 2 → 4**.
The accepted B0 reference contains 39 of these counters and 79 claimed states;
eight zero counters are omitted. The combined reward/boon balance change is
not an isolated currency test. This feature changes counters only. [DEED-04–05](test-results-deeds-2026-11-15.md#player-acceptance-and-supplied-saves)
confirmed training 75 creates state 2 and an in-game claim changes 2 → 4 with
Karma 710 → 720. DEED-06 confirmed the game can clear state 4 below target.

Counter keys use `実績_…`; milestone keys use `実績状態_…`. Both hashes are the
low 32 bits of FNV-1 64 of the full UTF-8 key (`core.id_hash`). The same map
contains other records, which are preserved. The locator requires:

* Exactly one live `GameUserData` block and one candidate map containing any
  catalogue counter or milestone identity.
* At least three distinct known counter identities and no duplicate records.
* A leaf map inside a struct group directly below the live `GameUserData` node.

The map number moved in reference saves; no index or absolute address is used.
The object contains an end pointer, version byte 0, u16 count, then u32-hash
records. A value is one byte (0–254), or `ff` plus signed i32. Counter writes
preserve existing wide encoding, promote short records when needed, and append
new nonzero counters. Every other record retains its bytes and relative order.
No guessed `実績表示_…` flags are created. The shared-map boon candidate
`3b6429de` and all other systems remain outside this operation.

`core.replace_content()` relocates pointers; the normal container writer
updates checksums. No-ops are byte-identical and create no undo history.
Validation precedes the edit. The GUI refuses route mirroring and uses the
normal selected-slot cache, undo, dirty-state and save mechanisms. Unknown
claim states, read-only counters and invalid inputs fail without a partial edit.

## Complete counter catalogue

Targets and rewards below are paired in order. Exact milestone keys and hashes
are in `deed_names.json`; the selected form shows the counter identity and the
table shows each milestone identity. English labels also appear in **Flags**,
with original Japanese in **Reads as**. These descriptive labels do not change
any hashed key.

| Activity | Counter key | Hash | Editing | Targets | Rewards |
|---|---|---|---|---|---|
| Paralogues cleared | `実績_外伝クリア数` | `ac891429` | Read-only | 1, 2, 3, 4, 5, 6, 7, 8, 9 | 25, 25, 25, 25, 25, 25, 25, 25, 25 |
| C support conversations viewed | `実績_支援会話C再生数` | `6e05ea11` | Read-only | 5, 10, 15, 20, 25, 30, 35, 40, 45, 50 | 10, 10, 15, 20, 25, 30, 35, 40, 45, 50 |
| B support conversations viewed | `実績_支援会話B再生数` | `cc4a3b3a` | Read-only | 5, 10, 15, 20, 25, 30, 35, 40, 45, 50 | 10, 10, 15, 20, 25, 30, 35, 40, 45, 50 |
| A support conversations viewed | `実績_支援会話A再生数` | `01aca43b` | Read-only | 5, 10, 15, 20, 25, 30, 35, 40, 45, 50 | 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 |
| Hours played | `実績_プレイ時間` | `eb92a0f6` | Read-only | 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 150, 200, 250, 300 | 10, 20, 30, 40, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50 |
| Skill levels raised to C | `実績_技能レベルC成長数` | `c6f4cfe6` | Read-only | 3 | 10 |
| Skill levels raised to B | `実績_技能レベルB成長数` | `05413e55` | Read-only | 3 | 20 |
| Skill levels raised to A | `実績_技能レベルA成長数` | `69c3bd94` | Read-only | 3 | 30 |
| Skill levels raised to S | `実績_技能レベルS成長数` | `0c174336` | Read-only | 3 | 40 |
| Skill levels raised to maximum | `実績_技能レベル最大成長数` | `0cd50d11` | Read-only | 3 | 50 |
| Blessings raised to level 2 | `実績_加護レベル2達成数` | `da109aa3` | Read-only | 1, 3, 6 | 10, 30, 100 |
| Blessings raised to maximum | `実績_加護レベル最大達成数` | `b8892bfd` | Read-only | 1, 3, 6 | 30, 100, 200 |
| Training sessions | `実績_訓練回数` | `2adbdfbf` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Theatre visits | `実績_観劇回数` | `c01c6da3` | Editable | 10, 20, 30, 40, 50 | 10, 10, 10, 10, 10 |
| Temple services performed | `実績_奉仕回数` | `b693004d` | Editable | 10, 20, 30, 40, 50 | 10, 10, 10, 10, 10 |
| Rooms rented at inns | `実績_宿泊回数` | `e14e0e21` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Turns performing individual actions | `実績_個別行動周期数` | `dbc7c723` | Editable | 10, 20, 30, 40, 50 | 10, 10, 10, 10, 10 |
| Meals at inns | `実績_食事回数` | `4baccce0` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Gifts given | `実績_贈り物回数` | `23a7a96e` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Perfect interactions at the perch | `実績_パーフェクト回数` | `971d3e40` | Editable | 10, 20, 30, 40, 50 | 10, 20, 30, 40, 50 |
| Bonds deepened with the Pale Raven | `実績_白鴉絆回数` | `ef1833d1` | Editable | 10, 20, 30, 40, 50 | 10, 20, 30, 40, 50 |
| Certification exams passed | `実績_資格試験成功回数` | `2f6582a3` | Editable | 10, 20, 30, 40, 50 | 10, 10, 10, 10, 10 |
| Vandahl Trading Company exchanges | `実績_ヴァンダル商会交換数` | `37d2ac86` | Editable | 10, 20, 30, 40, 50 | 10, 10, 10, 10, 10 |
| Gold spent at shops in bases | `実績_買い物消費金額` | `71015890` | Editable | 10000, 30000, 50000, 100000, 200000, 300000 | 10, 10, 10, 20, 20, 20 |
| Foes defeated in battle | `実績_敵撃破数` | `50126cb8` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Undead foes defeated in battle | `実績_冥魔敵撃破数` | `1be28238` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300, 350, 400, 450, 500 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Giant foes defeated (translation) | `実績_巨大敵撃破数` | `84f61022` | Read-only | 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Beasts defeated in battle | `実績_野生敵撃破数` | `9bd7c8ca` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Livestock defeated in battle | `実績_家畜敵撃破数` | `550f13b3` | Read-only | 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Golden or silver mummies defeated | `実績_特別敵撃破数` | `e203feff` | Read-only | 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Attacks avoided | `実績_回避回数` | `6614ae03` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Critical attacks performed | `実績_必殺回数` | `e997585d` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Assists performed | `実績_補助回数` | `c12cf155` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Blaze Arts used | `実績_特技回数` | `d423a64f` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Gambits used | `実績_計略回数` | `444e1de9` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200, 250, 300 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Support Salvations performed | `実績_援護回数` | `8a922825` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 25, 25, 50, 50 |
| Skirmishes won | `実績_遭遇戦勝利数` | `c989a067` | Editable | 5, 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Clashes won | `実績_ショートバトル勝利数` | `c449c893` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Attack Links performed | `実績_攻撃連携回数` | `f222c6fe` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Recovery Links performed | `実績_回復連携回数` | `d4e84b3a` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Mixed Links performed | `実績_攻防連携回数` | `73f4db16` | Editable | 10, 20, 30, 40, 50, 75, 100 | 10, 10, 10, 10, 10, 10, 10 |
| Gold spent with travelling merchants | `実績_商人消費金額` | `160b2bb2` | Editable | 10000, 20000, 30000, 50000, 100000, 200000 | 10, 10, 10, 10, 20, 20 |
| Spots searched | `実績_探索回数` | `a0b99107` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Rare materials obtained through searches | `実績_レア素材入手数` | `16f518a2` | Editable | 10, 20, 30, 40, 50, 75, 100, 150, 200 | 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Feasts held | `実績_饗宴回数` | `730acddc` | Editable | 5, 10, 15, 20, 25, 30, 35, 40, 50 | 10, 10, 10, 10, 10, 10, 10, 10, 10 |
| Local performances given | `実績_興行回数` | `e7d753ab` | Editable | 5, 10, 15, 20 | 10, 10, 10, 10 |
| Pieces of ore obtained | `実績_鉱石入手数` | `c2f3210d` | Editable | 10, 50, 100, 200, 300, 400, 500 | 10, 10, 10, 10, 10, 10, 10 |
