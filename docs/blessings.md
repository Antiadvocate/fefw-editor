# Blessings: EXP for all seven gods

Milestone 2 exposes each god's **stored EXP** in the selected save. It does not
write a level field. Six level previews use thresholds found in the game's
data; Fortuna has special handling. The [all-god acceptance run](testing-blessings.md)
passed on Leda Part I Chapter 9 / `fefw-recomp-0.1.5`: all six ordinary gods
displayed the tested level 2, including a reduction of Kalla from level 3.
The seven supplied case saves retained their requested EXP. This validates the
tested values and workflow, not every boundary or game version. See the
[results](test-results-blessings-2026-11-15.md).

**Naming correction:** Test 1 called the `MIR_フォトナ` record Photon. The
player's screenshots identify its effect as **Fortuna's Blessing**. The current
English display name is Fortuna; the Japanese key, full hash, save layout and
editing behavior are unchanged. Historical BLESS-09 references to Photon mean
this same record.

## Using the page

1. Close the game and open a disposable copy of a working save folder.
2. Leave **Also edit this route's other saves**, below the Slot selector,
   unchecked. Select the slot and open **Blessings**.
3. Select one god and enter a whole number into **New EXP**. The level buttons
   merely fill that input with a threshold; they do not apply or save it.
4. Click **Apply EXP**. Check the changed row. Ctrl+Z undoes; Ctrl+Y redoes.
5. Ctrl+S writes changed slots to disk. Reopen the save to verify the export.

The input accepts 0–65535, the unsigned 16-bit storage range. This is **not** a
recommendation to use extreme values in game. Initial gameplay tests use
values within the six gods' data thresholds, and Fortuna 1 only as a controlled
persistence experiment. Zero EXP remains editable even if the god has not yet
been met.

**Selected (stored)** displays the raw selection byte: 0 is shown as No, 1 as
Yes, other values as Unknown. This is separate from selecting a row in the
editor. It cannot be changed on this page. Divine Sand is also read-only.
Neither field is inferred from EXP. Audience flags, temple access, story
progress, Boons and notable-deed progress/claim state are not written by this
operation. The game may update derived progression or deeds when loading or
playing; record those effects during testing rather than assuming EXP alone
fully restores all associated state.

## Identity and threshold catalogue

Hashes are full FNV-1 64-bit values over the UTF-8 key, stored little-endian.
They are not the truncated 32-bit keys used by some flag maps.

| English name | Reads as | Full hash | Level 1 EXP | Level 2 EXP | Level 3 EXP |
|---|---|---|---:|---:|---:|
| Fortuna | `MIR_フォトナ` | `d2fdff3fa4a597ed` | Special | Special | Special |
| Mars | `MIR_マーズ` | `a1e2e07e81a0a45b` | 25 | 60 | 120 |
| Credna | `MIR_クレール` | `976774b9a9818925` | 15 | 40 | 80 |
| Kalla | `MIR_カーラ` | `f4fe5a5c9aab9f81` | 20 | 50 | 100 |
| Jurah | `MIR_ジュラ` | `b980ecffb61b6541` | 25 | 60 | 120 |
| Smyrnos | `MIR_スミルノス` | `bdafb8af054f07e0` | 25 | 60 | 120 |
| Aurora | `MIR_アウロラ` | `72fc44e0a9217c6a` | 20 | 50 | 100 |

For the six ordinary rows, preview level is the number of thresholds reached:
Mars 24 → 0, 25 → 1, 59 → 1, 60 → 2, 119 → 2, 120 → 3. This interpretation
fits the confirmed Mars 25 / level 1 and Kalla 100 / level 3 reference. The
editor shows stored total EXP; a game progress bar might instead show progress
within a level. Do not assume the displayed numbers must be identical.

Fortuna's three threshold fields are all zero. Treating them as ordinary
thresholds would misleadingly display level 3 at zero EXP. Its preview is
therefore **Special / unknown**, and its level buttons are disabled. Raw EXP
is editable as requested. In BLESS-09, EXP 1 persisted on editor reload and in
the supplied case save; the player saw no noticeable in-game change. In a
follow-up, the player also set the maximum stored EXP (65535) and reported
nothing easily noticeable on the Blessings screen. No follow-up save was
supplied to independently check that maximum value or its persistence.
These observations establish EXP 1 persistence and the reported screen
behavior, not the meaning of the field or an absence of all possible effects.
No Fortuna level or gameplay effect is promised.

## Technical layout and preservation

The observed live table is a non-struct direct child of the unique
`GameUserData` block, total size **88 bytes**, including its end pointer.

| Relative offset | Type / length | Meaning | Writable here |
|---|---|---|---|
| +0 | u32 | Object end pointer | No |
| +4 | u8 | Version, observed 2 | No |
| +5 | u32 | Divine Sand | No |
| +9 | u8 | Count, observed 7 | No |
| +10 | 7 × 11 bytes | God records | EXP only |
| +87 | 1 byte | Trailing byte, purpose unverified | No |

Each 11-byte record contains u64 identity at +0, u8 selection at +8 and u16
EXP at +9. All multibyte fields are little-endian. The parser accepts reordered
records and shifted object addresses. It does not assume child number 6,
a node index or an absolute save offset. An embedded older state in a different
struct can contain the same identities; an arbitrary payload search is unsafe.

`blessings.read` identifies candidate non-struct direct children by known full
hashes at record positions, then requires one candidate, version 2, count 7,
length 88, no child nodes, and exactly the seven distinct identities. A missing,
duplicate, unknown, malformed or ambiguous layout disables this page's edits.
No new god record is inserted and no unsupported layout is repaired.

`blessings.edited` validates the full request and returns a copy. Only the two
bytes at each requested EXP field can differ from the input payload. Object
sizes, pointers, order, selection bytes (including unknown values), Divine
Sand, trailing byte and every other payload byte are preserved. The normal
save writer recompresses the result and updates container metadata/checksums;
therefore a whole-file binary diff need not contain only two changed bytes.

The GUI edits one god at a time and uses the selected slot's existing undo
history. It refuses Apply while route mirroring is enabled. Invalid input and
same-value edits do not add a blessing undo entry. Reload, slot switches,
structural edits elsewhere, undo and redo refresh the table; cached offsets
are not reused to write a later payload.

## Evidence and reproducibility

Source evidence was the supplied working Leda Part I Chapter 9 save and a
local game-data dump. Neither belongs in the public repository. The exact game
data version was not independently reported; the player runs
`fefw-recomp-0.1.5`. These offsets identify the inspected dump, not a universal
format locator:

* The MIR rows are in a later section of `GameData/Skill.bin`, not its first
  table. Row stride is 176 bytes; the MIR key pointer is at row +8.
* `経験１`, `経験２`, `経験３` are unsigned two-byte fields at row offsets
  120, 144 and 168. Their field descriptors are at `0x28a2a8`, `0x28a2e8`
  and `0x28a328` in the inspected file.
* Fortuna through Aurora row starts are `0x28a3f8`, `0x28a4a8`, `0x28a558`,
  `0x28a608`, `0x28a6b8`, `0x28a768`, `0x28a818` respectively.
* `謁見条件` is a separate field at row +48. Ordinary gods refer to first-talk
  flags such as `共有_行動_初めてマーズと話した`; Fortuna has an empty value.
  The editor does not infer or write these flags from the EXP amount.

For a different dump version, find the MIR rows and named field descriptors
again, then compare their values. Do not reuse these file offsets blindly.
For the current validation record, see
[automated and GUI checks](test-results-blessings-2026-11-15.md).
